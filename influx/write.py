from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.write_api import WriteOptions
from datetime import datetime

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "nyFqY-9lp5L9NsjGHpP8SeV7ZKqvs6t_IfQqaXMaGbV0GptgsDVoNkGKGkcR2WTLBdNoFqVKSv1dQY7jAzhQNw=="
INFLUXDB_ORG = "nust"
INFLUXDB_BUCKET = "ml-pipeline"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

write_api = client.write_api(write_options=WriteOptions(write_type="blocking"))


point = Point("sensor_prediction") \
    .tag("sensor_id", "test_sensor") \
    .field("temperature", 25.0) \
    .field("humidity", 50.0) \
    .time(datetime.utcnow())

write_api.write(bucket="ml-pipeline", record=point)
print("Write successful")

client.close()
