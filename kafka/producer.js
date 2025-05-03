const { Kafka } = require('kafkajs');

const kafka = new Kafka({
    clientId: 'fake-producer',
    brokers: ['localhost:9092']
});

const producer = kafka.producer();

const run = async () => {
    await producer.connect();
    console.log("🚀 Producer connected");

    let id = 1;

    setInterval(async () => {
        const message = {
            id,
            name: `User${id}`,
            timestamp: new Date().toISOString()
        };

        await producer.send({
            topic: 'User',
            messages: [
                {
                    key: String(id),
                    value: JSON.stringify(message),
                    partition: id % 2 // send evenly to 2 partitions
                }
            ]
        });

        console.log(`✅ Sent message ${id}`);
        id++;

    }, 5000); // sends a message every second
};

run().catch(console.error);
