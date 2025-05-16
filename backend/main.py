from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pytz
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Sensor Analytics Dashboard API",
    description="API for real-time sensor data visualization and analytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_ORG = "nust"
INFLUXDB_TOKEN = 'TEF9yzQY76LI-IDI6o0N58LRBwOhK0x9aRMgNsS4HnaEvIPUPAwtq005sjLAJTJRnWq2RcYCmLPf8_imrmT62g=='
INFLUX_BUCKET = "ml-pipeline"

client = influxdb_client.InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

query_api = client.query_api()

# Pydantic Models
class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    status_flag: str
    status_prediction: float
    anomaly_prediction: float
    humidity_prediction: float
    location: str

class SensorStats(BaseModel):
    sensor_id: str
    reading_count: int
    avg_temperature: float
    avg_humidity: float
    avg_anomaly_score: float
    last_reading: datetime
    location: str

class TimeSeriesData(BaseModel):
    timestamps: List[datetime]
    values: List[float]

class SensorTrends(BaseModel):
    sensor_id: str
    temperature: TimeSeriesData
    humidity: TimeSeriesData
    anomaly_score: TimeSeriesData

class AnomalyReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    anomaly_prediction: float
    location: str
    status_flag: str

class LocationData(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    last_reading: datetime
    status_flag: str
    current_temperature: float
    current_humidity: float

# Helper Functions
def query_influx(query: str) -> pd.DataFrame:
    """Execute Flux query and return results as DataFrame"""
    try:
        result = query_api.query_data_frame(query)
        if isinstance(result, list):
            df = pd.concat(result, ignore_index=True)
        else:
            df = result
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"InfluxDB query error: {str(e)}")

def build_base_query(measurement: str, start: datetime, end: datetime, filters: dict = None) -> str:
    """Build base Flux query with time range and optional filters"""
    query = f"""
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: {start.isoformat()}, stop: {end.isoformat()})
        |> filter(fn: (r) => r._measurement == "{measurement}")
    """
    
    if filters:
        for field, value in filters.items():
            if value is not None:
                query += f"""|> filter(fn: (r) => r.{field} == "{value}")\n"""
    
    return query

# API Endpoints
@app.get("/api/sensors", response_model=List[SensorStats], tags=["Sensors"])
def get_sensor_stats(hours: int = Query(24, description="Time window in hours")):
    """
    Get statistics for all sensors in the specified time window
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(hours=hours)
    
    # Query for sensor metadata and last readings
    query = f"""
    {build_base_query("sensor_data", start_time, end_time)}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> group(columns: ["sensor_id"])
        |> last()
    """
    last_readings = query_influx(query)
    
    # Query for statistics
    query = f"""
    {build_base_query("sensor_data", start_time, end_time)}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> group(columns: ["sensor_id"])
        |> aggregateWindow(every: 1h, fn: mean)
        |> mean()
    """
    stats = query_influx(query)
    
    # Combine results
    if last_readings.empty or stats.empty:
        return []
    
    result = []
    for _, row in stats.iterrows():
        sensor_id = row['sensor_id']
        last_reading = last_readings[last_readings['sensor_id'] == sensor_id].iloc[0]
        
        result.append({
            "sensor_id": sensor_id,
            "reading_count": int(row['count']),
            "avg_temperature": float(row['temperature']),
            "avg_humidity": float(row['humidity']),
            "avg_anomaly_score": float(row['anomaly_prediction']),
            "last_reading": last_reading['_time'].to_pydatetime(),
            "location": last_reading['location']
        })
    
    return result

@app.get("/api/sensors/{sensor_id}/trends", response_model=SensorTrends, tags=["Sensors"])
def get_sensor_trends(
    sensor_id: str,
    hours: int = Query(24, description="Time window in hours"),
    resolution: str = Query("15m", description="Resolution: 1m, 5m, 15m, 1h, etc.")
):
    """
    Get time series trends for a specific sensor
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(hours=hours)
    
    query = f"""
    {build_base_query("sensor_data", start_time, end_time, {"sensor_id": sensor_id})}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> aggregateWindow(every: {resolution}, fn: mean)
        |> fill(usePrevious: true)
    """
    df = query_influx(query)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for this sensor")
    
    return {
        "sensor_id": sensor_id,
        "temperature": {
            "timestamps": df['_time'].dt.to_pydatetime().tolist(),
            "values": df['temperature'].tolist()
        },
        "humidity": {
            "timestamps": df['_time'].dt.to_pydatetime().tolist(),
            "values": df['humidity'].tolist()
        },
        "anomaly_score": {
            "timestamps": df['_time'].dt.to_pydatetime().tolist(),
            "values": df['anomaly_prediction'].tolist()
        }
    }

@app.get("/api/anomalies", response_model=List[AnomalyReading], tags=["Anomalies"])
def get_anomalies(
    hours: int = Query(24, description="Time window in hours"),
    threshold: float = Query(0.8, description="Anomaly score threshold"),
    limit: int = Query(100, description="Maximum number of results")
):
    """
    Get anomalous readings across all sensors
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(hours=hours)
    
    query = f"""
    {build_base_query("sensor_data", start_time, end_time)}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => r.anomaly_prediction >= {threshold})
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: {limit})
    """
    df = query_influx(query)
    
    if df.empty:
        return []
    
    return [{
        "sensor_id": row['sensor_id'],
        "timestamp": row['_time'].to_pydatetime(),
        "temperature": float(row['temperature']),
        "humidity": float(row['humidity']),
        "anomaly_prediction": float(row['anomaly_prediction']),
        "location": row['location'],
        "status_flag": row['status_flag']
    } for _, row in df.iterrows()]

@app.get("/api/locations", response_model=List[LocationData], tags=["Locations"])
def get_sensor_locations():
    """
    Get location data for all sensors with their latest readings
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(days=7)  # Look back 7 days for sensors
    
    query = f"""
    {build_base_query("sensor_data", start_time, end_time)}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> group(columns: ["sensor_id"])
        |> last()
        |> filter(fn: (r) => exists r.latitude and exists r.longitude)
    """
    df = query_influx(query)
    
    if df.empty:
        return []
    
    return [{
        "sensor_id": row['sensor_id'],
        "latitude": float(row['latitude']),
        "longitude": float(row['longitude']),
        "last_reading": row['_time'].to_pydatetime(),
        "status_flag": row['status_flag'],
        "current_temperature": float(row['temperature']),
        "current_humidity": float(row['humidity'])
    } for _, row in df.iterrows()]

@app.get("/api/sensors/historical", tags=["Analytics"])
def get_historical_comparison(
    sensor_ids: List[str] = Query(..., description="List of sensor IDs to compare"),
    days: int = Query(7, description="Number of days to look back"),
    field: str = Query("temperature", description="Field to compare: temperature, humidity, anomaly_prediction")
):
    """
    Get historical comparison data for multiple sensors
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(days=days)
    
    results = {}
    for sensor_id in sensor_ids:
        query = f"""
        {build_base_query("sensor_data", start_time, end_time, {"sensor_id": sensor_id})}
            |> filter(fn: (r) => r._field == "{field}")
            |> aggregateWindow(every: 1h, fn: mean)
        """
        df = query_influx(query)
        
        if not df.empty:
            results[sensor_id] = {
                "timestamps": df['_time'].dt.to_pydatetime().tolist(),
                "values": df['_value'].tolist()
            }
    
    return results

@app.get("/api/sensors/correlation", tags=["Analytics"])
def get_correlation_analysis(
    sensor_id: str,
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Get correlation analysis between different metrics for a sensor
    """
    end_time = datetime.now(pytz.utc)
    start_time = end_time - timedelta(days=days)
    
    query = f"""
    {build_base_query("sensor_data", start_time, end_time, {"sensor_id": sensor_id})}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> aggregateWindow(every: 1h, fn: mean)
    """
    df = query_influx(query)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for this sensor")
    
    # Calculate correlations
    corr_matrix = df[['temperature', 'humidity', 'anomaly_prediction', 'humidity_prediction']].corr()
    
    return {
        "temperature_humidity": float(corr_matrix.loc['temperature', 'humidity']),
        "temperature_anomaly": float(corr_matrix.loc['temperature', 'anomaly_prediction']),
        "humidity_anomaly": float(corr_matrix.loc['humidity', 'anomaly_prediction']),
        "humidity_prediction_accuracy": float(corr_matrix.loc['humidity', 'humidity_prediction'])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)