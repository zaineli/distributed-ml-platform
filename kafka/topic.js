const { Kafka } = require('kafkajs');

async function run() {
    const kafka = new Kafka({
        clientId: 'my-app',
        brokers: ['localhost:9092']
    });

    const admin = kafka.admin(); // ✅ moved out of try block

    try {
        await admin.connect();
        console.log('Connected to Kafka broker');

        // Create a new topic
        await admin.createTopics({
            topics: [
                {
                    topic: 'Products',
                    numPartitions: 2,
                    replicationFactor: 1
                }
            ]
        });

        console.log('Topic created successfully');
    } catch (error) {
        console.error('Error creating Kafka topic:', error);
    } finally {
        console.log('Kafka instance created successfully');
        await admin.disconnect();
    }
}

run().catch(console.error);
