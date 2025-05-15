from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.regression import GBTRegressor
from pyspark.ml import Pipeline
import pyspark.sql.functions as F
import os

spark = SparkSession.builder.appName("ModelTraining").getOrCreate()

# Load training data
df = spark.read.csv("../models/training_data.csv", header=True, inferSchema=True)

# -----------------------------
# Model 1: StatusFlagPredictor (Random Forest)
# -----------------------------
feature_cols_model1 = [
    "temperature", "humidity", "hour_of_day", "day_of_week",
    "temp_change_rate", "humidity_change_rate", "avg_temp_last_5min"
]
assembler1 = VectorAssembler(inputCols=feature_cols_model1, outputCol="features")
rf = RandomForestClassifier(labelCol="status_flag", featuresCol="features", numTrees=10)
pipeline1 = Pipeline(stages=[assembler1, rf])

model1 = pipeline1.fit(df)

# Save Model 1
os.makedirs("saved_models", exist_ok=True)
model1.write().overwrite().save("saved_models/status_flag_model")
print("✅ Model 1: StatusFlagPredictor saved.")

# -----------------------------
# Model 2: TemperatureAnomalyDetector (Logistic Regression)
# -----------------------------
# Compute statistics for temperature to calculate z-score
stats = df.agg(F.mean("temperature").alias("mean"), F.stddev("temperature").alias("std")).collect()[0]
mean_temp = stats["mean"]
std_temp = stats["std"]
threshold = 80.0  # adjust threshold as needed

# Create anomaly label: 1 if temperature > threshold or |zscore| > 2, else 0
df = df.withColumn("zscore", (F.col("temperature") - F.lit(mean_temp)) / F.lit(std_temp))
df = df.withColumn("is_temp_anomaly", F.when((F.col("temperature") > threshold) | (F.abs(F.col("zscore")) > 2), 1).otherwise(0))

feature_cols_model2 = [
    "humidity", "hour_of_day", "day_of_week", "temp_change_rate", "avg_temp_last_5min"
]
assembler2 = VectorAssembler(inputCols=feature_cols_model2, outputCol="features")
lr = LogisticRegression(labelCol="is_temp_anomaly", featuresCol="features")
pipeline2 = Pipeline(stages=[assembler2, lr])

model2 = pipeline2.fit(df)

# Save Model 2
model2.write().overwrite().save("saved_models/temp_anomaly_model")
print("✅ Model 2: TemperatureAnomalyDetector saved.")

# -----------------------------
# Model 3: HumidityRegressor (Gradient-Boosted Regressor)
# -----------------------------
feature_cols_model3 = [
    "temperature", "hour_of_day", "day_of_week", "humidity_change_rate", "avg_temp_last_5min"
]
assembler3 = VectorAssembler(inputCols=feature_cols_model3, outputCol="features")
from pyspark.ml.regression import GBTRegressor
gbt = GBTRegressor(labelCol="humidity", featuresCol="features")
pipeline3 = Pipeline(stages=[assembler3, gbt])

model3 = pipeline3.fit(df)

# Save Model 3
model3.write().overwrite().save("saved_models/humidity_regressor")
print("✅ Model 3: HumidityRegressor saved.")
