import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const fetchSensorStats = async (hours: number = 24) => {
  const response = await axios.get(`${API_BASE_URL}/sensors`, {
    params: { hours }
  });
  return response.data;
};

export const fetchSensorTrends = async (sensorId: string, hours: number = 24, resolution: string = '15m') => {
  const response = await axios.get(`${API_BASE_URL}/sensors/${sensorId}/trends`, {
    params: { hours, resolution }
  });
  return response.data;
};

export const fetchAnomalies = async (hours: number = 24, threshold: number = 0.8) => {
  const response = await axios.get(`${API_BASE_URL}/anomalies`, {
    params: { hours, threshold }
  });
  return response.data;
};

export const fetchLocations = async () => {
  const response = await axios.get(`${API_BASE_URL}/locations`);
  return response.data;
};

export const fetchHistoricalComparison = async (sensorIds: string[], days: number = 7, field: string = 'temperature') => {
  const response = await axios.get(`${API_BASE_URL}/sensors/historical`, {
    params: { sensor_ids: sensorIds.join(','), days, field }
  });
  return response.data;
};

export const fetchCorrelation = async (sensorId: string, days: number = 7) => {
  const response = await axios.get(`${API_BASE_URL}/sensors/correlation`, {
    params: { sensor_id: sensorId, days }
  });
  return response.data;
};