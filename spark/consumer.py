import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, concat_ws, monotonically_increasing_id
from pyspark.sql.types import StructType, StringType, FloatType, LongType, IntegerType
from pyspark.ml import PipelineModel
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaSensorConsumer")

# Wait for other services to be ready
logger.info("Waiting for services to start...")
time.sleep(30)

# Create Spark session
spark = SparkSession.builder \
    .appName("KafkaSensorConsumer") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.elasticsearch:elasticsearch-spark-30_2.12:8.18.0") \
    .config("es.nodes", "elasticsearch") \
    .config("es.port", "9200") \
    .config("es.nodes.wan.only", "true") \
    .config("es.nodes.discovery", "false") \
    .config("es.net.ssl", "false") \
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
    .option("startingOffsets", "earliest") \
    .load()

# Parse and transform data
raw_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Convert timestamp from milliseconds to timestamp type
parsed_df = raw_df.withColumn("timestamp", to_timestamp((col("timestamp") / 1000)))

# Fill missing values with default
parsed_df = parsed_df.fillna(0)

# Add a serial index to create a unique row_id
parsed_df = parsed_df.withColumn("serial_index", monotonically_increasing_id())
base_df = parsed_df.withColumn("row_id", concat_ws("_", col("sensor_id"), col("serial_index")))

# Load ML models
try:
    logger.info("Loading ML models...")
    model1 = PipelineModel.load("./saved_models/status_flag_model")
    model2 = PipelineModel.load("./saved_models/temp_anomaly_model")
    model3 = PipelineModel.load("./saved_models/humidity_regressor")
    logger.info("ML models loaded successfully")
    
    # Run inference with real models
    df1 = model1.transform(base_df).select("row_id", F.col("prediction").alias("status_prediction"))
    df2 = model2.transform(base_df).select("row_id", F.col("prediction").alias("anomaly_prediction"))
    df3 = model3.transform(base_df).select("row_id", F.col("prediction").alias("humidity_prediction"))
    
    # Join predictions with the original dataframe
    joined_df = base_df.join(df1, on="row_id") \
        .join(df2, on="row_id") \
        .join(df3, on="row_id")
except Exception as e:
    logger.warning(f"Failed to load models: {str(e)}. Using dummy predictions.")
    # Add dummy predictions if model loading fails
    joined_df = base_df \
        .withColumn("status_prediction", F.rand()) \
        .withColumn("anomaly_prediction", F.rand()) \
        .withColumn("humidity_prediction", base_df.humidity + F.rand() * 5 - 2.5)

# Prepare final output dataframe for Elasticsearch
es_output_df = joined_df.select(
    "row_id", "sensor_id", "timestamp", "temperature", "humidity", "status_flag",
    "status_prediction", "anomaly_prediction", "humidity_prediction", "location"
).withColumn("timestamp", col("timestamp").cast("string"))

# Write to Console for debugging
console_query = es_output_df.writeStream \
    .format("console") \
    .option("truncate", False) \
    .outputMode("append") \
    .start()

# Write to Elasticsearch
es_query = es_output_df.writeStream \
    .format("es") \
    .option("checkpointLocation", "/tmp/spark-checkpoints") \
    .option("es.resource", "sensor-index") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.nodes.wan.only", "true") \
    .option("es.mapping.id", "row_id") \
    .outputMode("append") \
    .start()

try:
    es_query.awaitTermination()
except KeyboardInterrupt:
    logger.info("Stopping streaming queries...")
    es_query.stop()
    console_query.stop()
    spark.stop()