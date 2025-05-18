// topic.js
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'topic-creator',
  brokers: ['localhost:29092']
});

const admin = kafka.admin();

const run = async () => {
  await admin.connect();
  console.log('Connected to Kafka broker');

  await admin.createTopics({
    topics: [{ topic: 'sensor-data', numPartitions: 1, replicationFactor: 1 }],
  });

  console.log('Topic "sensor-data" created');
  await admin.disconnect();
};

run().catch(console.error);
