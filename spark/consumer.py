import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, concat, lit
from pyspark.sql.types import StructType, StringType, FloatType, LongType, IntegerType
from pyspark.ml import PipelineModel
from influxdb_client import InfluxDBClient, Point, WriteOptions
from datetime import timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaSensorConsumer")

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_ORG = "nust"
INFLUXDB_TOKEN = 'TEF9yzQY76LI-IDI6o0N58LRBwOhK0x9aRMgNsS4HnaEvIPUPAwtq005sjLAJTJRnWq2RcYCmLPf8_imrmT62g=='
INFLUXDB_BUCKET = "ml-pipeline"

# Create Spark Session
spark = SparkSession.builder \
    .appName("KafkaSensorConsumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.elasticsearch:elasticsearch-spark-30_2.12:8.13.2") \
    .config("es.nodes", "elasticsearch") \
    .config("es.port", "9200") \
    .config("es.nodes.wan.only", "true") \
    .config("es.net.ssl", "false") \
    .config("es.nodes.discovery", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Define schema for the JSON payload from Kafka
schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("temperature", FloatType()) \
    .add("humidity", FloatType()) \
    .add("timestamp", LongType()) \
    .add("hour_of_day", IntegerType()) \
    .add("day_of_week", IntegerType()) \
    .add("temp_change_rate", FloatType()) \
    .add("humidity_change_rate", FloatType()) \
    .add("avg_temp_last_5min", FloatType()) \
    .add("status_flag", IntegerType()) \
    .add("location", StringType())

# Read from Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "sensor-data") \
    .load()

kafka_df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)").writeStream \
    .format("console") \
    .start() \
    .awaitTermination()

# Parse and transform data
raw_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Convert timestamp from milliseconds to timestamp type
parsed_df = raw_df.withColumn("timestamp", to_timestamp((col("timestamp") / 1000)))

# Fill missing values with default
parsed_df = parsed_df.fillna(0)

# Base features
base_df = parsed_df.select(
    "sensor_id", "temperature", "humidity", "status_flag", "hour_of_day", "day_of_week",
    "temp_change_rate", "humidity_change_rate", "avg_temp_last_5min", "timestamp", "location"
)

# Generate unique row_id
base_df = base_df.withColumn("row_id", 
    concat(col("sensor_id"), lit("_"), col("timestamp").cast("string"))
)

# Load ML models
model1 = PipelineModel.load("./saved_models/status_flag_model")
model2 = PipelineModel.load("./saved_models/temp_anomaly_model")
model3 = PipelineModel.load("./saved_models/humidity_regressor")

# Run inference
df1 = model1.transform(base_df).select("row_id", F.col("prediction").alias("status_prediction"))
df2 = model2.transform(base_df).select("row_id", F.col("prediction").alias("anomaly_prediction"))
df3 = model3.transform(base_df).select("row_id", F.col("prediction").alias("humidity_prediction"))

# Join predictions
joined_df = base_df.join(df1, on="row_id") \
    .join(df2, on="row_id") \
    .join(df3, on="row_id")

# Final output columns
output_df = joined_df.select(
    "sensor_id", "timestamp", "temperature", "humidity", "status_flag",
    "status_prediction", "anomaly_prediction", "humidity_prediction", "location"
)

def write_to_influx(row):
    try:
        # Ensure timestamp has UTC timezone info
        timestamp = row.timestamp.replace(tzinfo=timezone.utc)
        
        point = Point("sensor_prediction") \
            .tag("sensor_id", row.sensor_id) \
            .field("temperature", float(row.temperature)) \
            .field("humidity", float(row.humidity)) \
            .field("location", row.location) \
            .field("status_flag", int(row.status_flag)) \
            .field("status_prediction", float(row.status_prediction)) \
            .field("anomaly_prediction", float(row.anomaly_prediction)) \
            .field("humidity_prediction", float(row.humidity_prediction)) \
            .time(timestamp)

        return point
    except Exception as e:
        logger.error(f"Error creating point for row {row}: {str(e)}")
        return None

def write_batch_to_influx(df, epoch_id):
    try:
        # Initialize client for each batch to ensure fresh connection
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
            write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10_000))
            
            points = []
            for row in df.collect():
                point = write_to_influx(row)
                if point:
                    points.append(point)
            
            if points:
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
                logger.info(f"Successfully wrote {len(points)} points to InfluxDB for epoch {epoch_id}")
            else:
                logger.warning(f"No valid points to write for epoch {epoch_id}")
                
    except Exception as e:
        logger.error(f"Error writing batch to InfluxDB: {str(e)}")
    finally:
        # Ensure write_api is properly closed
        if 'write_api' in locals():
            write_api.close()

# Start the streaming query with foreachBatch to write to InfluxDB
# query = output_df.writeStream \
#     .foreachBatch(write_batch_to_influx) \
#     .start()
output_df.printSchema()
output_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start()
    
es_output_df = output_df.withColumn("timestamp", col("timestamp").cast("string"))

es_query = es_output_df.writeStream \
    .format("es") \
    .option("checkpointLocation", "/tmp/spark-checkpoints") \
    .option("es.resource", "sensor-index") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.nodes.wan.only", "true") \
    .option("es.net.ssl", "false") \
    .outputMode("append") \
    .start()
try:
    # query.awaitTermination()
    output_df.awaitTermination()
    es_query.awaitTermination()
except KeyboardInterrupt:
    logger.info("Stopping streaming queries...")
    # query.stop()
    es_query.stop()
    spark.stop()