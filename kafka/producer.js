const { Kafka } = require('kafkajs');

const kafka = new Kafka({
    clientId: 'sensor-app',
    brokers: ['localhost:9092']
});

const producer = kafka.producer();

const sendMessage = async () => {
    await producer.connect();
    console.log("Producer connected");

    setInterval(async () => {
        const message = {
            sensor_id: `sensor_${Math.floor(Math.random() * 10)}`,
            temperature: parseFloat((Math.random() * 100).toFixed(2)),
            humidity: parseFloat((Math.random() * 100).toFixed(2)),
            timestamp: Date.now()
        };

        await producer.send({
            topic: 'sensor-data',
            messages: [
                {
                    value: JSON.stringify(message)
                }
            ]
        });

        console.log("Sent:", message);
    }, 1000);
};

sendMessage().catch(console.error);
