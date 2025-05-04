# consumer.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, FloatType, LongType

# Step 1: Create Spark Session
spark = SparkSession.builder \
    .appName("KafkaSensorConsumer") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Step 2: Define schema of sensor data
schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("temperature", FloatType()) \
    .add("humidity", FloatType()) \
    .add("timestamp", LongType())

# Step 3: Read stream from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "sensor-data") \
    .load()

# Step 4: Parse JSON messages
json_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Step 5: Write stream to console
query = json_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start()

query.awaitTermination()
