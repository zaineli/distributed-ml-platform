const { Client } = require('@elastic/elasticsearch');

// Set compatibility mode for older Node.js versions
const client = new Client({ 
  node: 'http://localhost:9200',
  tls: { 
    rejectUnauthorized: false
  },
  maxRetries: 3,
  requestTimeout: 60000
});

// Function to generate a random number within a range
function randomInRange(min, max) {
  return Math.random() * (max - min) + min;
}

// Function to generate a random location string (latitude, longitude)
function randomLocation() {
  const lat = (randomInRange(-90, 90)).toFixed(4);
  const lon = (randomInRange(-180, 180)).toFixed(4);
  return `${lat}, ${lon}`;
}

// Constants for generating realistic data
const SENSOR_IDS = ['sensor_0', 'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4'];
const NUM_SENSORS = SENSOR_IDS.length;

// Initialize Elasticsearch index if it doesn't exist
async function initializeElastic() {
  try {
    // Check if index exists - using the exists API compatible with older client versions
    const indexExists = await client.indices.exists({ 
      index: 'sensor-predictions' 
    }).catch(() => false);
    
    if (!indexExists.body) {
      console.log('Creating sensor-predictions index...');
      await client.indices.create({
        index: 'sensor-predictions',
        body: {
          mappings: {
            properties: {
              sensor_id: { type: 'keyword' },
              timestamp: { type: 'date' },
              temperature: { type: 'float' },
              humidity: { type: 'float' },
              location: { type: 'text' },
              status_flag: { type: 'integer' },
              status_prediction: { type: 'float' },
              anomaly_prediction: { type: 'float' },
              humidity_prediction: { type: 'float' }
            }
          }
        }
      });
      console.log('Index created successfully');
    } else {
      console.log('Index already exists');
    }
  } catch (error) {
    console.error('Error initializing Elasticsearch:', error);
  }
}

// Generate a single sensor reading with predictions
function generateSensorData() {
  // Basic sensor metrics
  const timestamp = new Date();
  const sensorIndex = Math.floor(Math.random() * NUM_SENSORS);
  const sensorId = SENSOR_IDS[sensorIndex];
  
  // Generate realistic temperature based on time of day (sinusoidal pattern)
  const hour = timestamp.getHours();
  const baseTemp = 70 + Math.sin(hour * Math.PI/12) * 15;
  const temperature = parseFloat((baseTemp + randomInRange(-5, 5)).toFixed(2));
  
  // Humidity often has inverse relationship with temperature
  const humidity = parseFloat((Math.min(100, Math.max(20, 110 - temperature + randomInRange(-10, 10)))).toFixed(2));
  
  // Location - random coordinates
  const location = randomLocation();
  
  // Status flag - binary (0 or 1)
  const status_flag = temperature > 80 ? 1 : 0;
  
  // Simulated ML model predictions
  // Model 1: Status prediction (probability between 0-1)
  const status_prediction = parseFloat((temperature > 75 ? randomInRange(0.6, 0.95) : randomInRange(0.05, 0.4)).toFixed(3));
  
  // Model 2: Anomaly prediction (probability between 0-1)
  const isAnomalous = Math.random() < 0.1; // 10% chance of anomaly
  const anomaly_prediction = parseFloat((isAnomalous ? randomInRange(0.7, 0.99) : randomInRange(0.01, 0.3)).toFixed(3));
  
  // Model 3: Humidity prediction (regression)
  // Small random deviation from actual humidity
  const humidity_prediction = parseFloat((humidity + randomInRange(-8, 8)).toFixed(2));
  
  return {
    sensor_id: sensorId,
    timestamp: timestamp.toISOString(),
    temperature,
    humidity,
    location,
    status_flag,
    status_prediction,
    anomaly_prediction,
    humidity_prediction
  };
}

// Send data to Elasticsearch
async function sendToElastic(data) {
  try {
    const result = await client.index({
      index: 'sensor-predictions',
      body: data,
      refresh: true // Makes data immediately available for search
    });
    return true;
  } catch (error) {
    console.error('Error sending to Elasticsearch:', error.message);
    return false;
  }
}

// Main function to continuously send data
async function startProducing() {
  try {
    // Initialize Elasticsearch index
    await initializeElastic();
    
    console.log('Starting to send simulated sensor data to Elasticsearch...');
    console.log('Press Ctrl+C to stop');
    
    // Counter for total records sent
    let recordCount = 0;
    
    // Set interval to send data every second
    const intervalId = setInterval(async () => {
      try {
        // Generate between 1-3 data points per iteration
        const numPoints = Math.floor(Math.random() * 3) + 1;
        
        for (let i = 0; i < numPoints; i++) {
          const data = generateSensorData();
          const success = await sendToElastic(data);
          
          if (success) {
            recordCount++;
            if (recordCount % 10 === 0) {
              console.log(`${recordCount} records sent to Elasticsearch`);
            }
            console.log(`Sent: sensor_id=${data.sensor_id}, temp=${data.temperature}, status_pred=${data.status_prediction}`);
          }
        }
      } catch (err) {
        console.error('Error in interval:', err.message);
      }
    }, 1000);
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      clearInterval(intervalId);
      console.log(`\nStopped after sending ${recordCount} records`);
      process.exit(0);
    });
  } catch (err) {
    console.error('Failed to start producer:', err.message);
  }
}

// Run the producer with error handling
startProducing().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});