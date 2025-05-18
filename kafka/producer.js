const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:29092'] // Not 'kafka:9092', that's for internal Docker
});

const producer = kafka.producer();

// Variables to track previous values and rolling window for avg temperature
let lastTemp = null;
let lastHumidity = null;
const tempReadings = []; // Array of { timestamp, temperature }

const sendMessage = async () => {
    await producer.connect();
    console.log("Producer connected");

    setInterval(async () => {
        const timestamp = Date.now();
        const date = new Date(timestamp);
        const hour_of_day = date.getHours();
        const day_of_week = date.getDay();
        
        const temperature = parseFloat((Math.random() * 100).toFixed(2));
        const humidity = parseFloat((Math.random() * 100).toFixed(2));
        
        // Calculate change rates from the previous reading
        const temp_change_rate = lastTemp !== null ? parseFloat((temperature - lastTemp).toFixed(2)) : 0;
        const humidity_change_rate = lastHumidity !== null ? parseFloat((humidity - lastHumidity).toFixed(2)) : 0;
        
        lastTemp = temperature;
        lastHumidity = humidity;
        
        // Update rolling window for temperature readings over the last 5 minutes (300000 ms)
        tempReadings.push({ timestamp, temperature });
        const fiveMinutesAgo = timestamp - 300000;
        // Filter out readings older than 5 minutes
        const recentReadings = tempReadings.filter(r => r.timestamp >= fiveMinutesAgo);
        
        // Replace tempReadings with the filtered version to avoid unbounded growth
        while (tempReadings.length && tempReadings[0].timestamp < fiveMinutesAgo) {
            tempReadings.shift();
        }
        
        // Calculate rolling average temperature
        const avg_temp_last_5min = recentReadings.length 
            ? parseFloat((recentReadings.reduce((sum, r) => sum + r.temperature, 0) / recentReadings.length).toFixed(2))
            : temperature;
        
        // Set status_flag based on a simple condition (example: alert if temperature > 70)
        const status_flag = temperature > 70 ? 1 : 0;
        
        // Create location value (example: a random coordinate string)
        const location = `${(Math.random() * 180 - 90).toFixed(4)}, ${(Math.random() * 360 - 180).toFixed(4)}`;
        
        const message = {
            sensor_id: `sensor_${Math.floor(Math.random() * 10)}`,
            temperature,
            humidity,
            timestamp,
            hour_of_day,
            day_of_week,
            temp_change_rate,
            humidity_change_rate,
            avg_temp_last_5min,
            status_flag,
            location
        };

        await producer.send({
            topic: 'sensor-data',
            messages: [{
                value: JSON.stringify(message)
            }]
        });

        console.log("Sent:", message);
    }, 1000);
};

sendMessage().catch(console.error);
