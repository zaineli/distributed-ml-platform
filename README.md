# Distributed ML Platform

A scalable, real-time platform for ingesting, processing, analyzing, and visualizing IoT sensor data using Apache Kafka, Apache Spark, machine learning models, Elasticsearch, and Kibana. The system is fully containerized with Docker Compose for easy deployment and reproducibility.

---

## 🚀 Overview

This project demonstrates a modern data pipeline for real-time analytics:

- **Data Generation:** Simulated sensor data (temperature, humidity, location, etc.)
- **Ingestion:** Apache Kafka for high-throughput, fault-tolerant message streaming
- **Processing:** Apache Spark Structured Streaming for distributed, parallel ML inference
- **Machine Learning:** Three models for status prediction, anomaly detection, and humidity regression
- **Storage:** Elasticsearch for fast, scalable indexing and search
- **Visualization:** Kibana dashboards for real-time monitoring and insights

---

## 🏗️ Architecture

- **producer.js:** Generates and streams realistic sensor data to Kafka.
- **Kafka:** Buffers and distributes data for parallel processing.
- **Spark:** Reads from Kafka, applies ML models, and writes results to Elasticsearch.
- **Elasticsearch:** Stores processed data for fast querying.
- **Kibana:** Visualizes data with interactive dashboards.

---

## 📦 Project Structure

```
.
├── docker-compose.yml
├── README.md
├── data
│   ├── README.md
│   └── sample_data.csv
├── notebooks
│   ├── README.md
│   └── Sensor_Data_Analysis.ipynb
├── producer
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   └── producer.js
├── spark
│   ├── Dockerfile
│   └── spark-job.py
└── webapp
    ├── Dockerfile
    ├── package.json
    ├── package-lock.json
    └── server.js
```

- **data/** - Sample data used for testing and development.
- **notebooks/** - Jupyter notebooks for data analysis and visualization.
- **producer/** - Node.js application for generating and sending data to Kafka.
- **spark/** - Spark job for processing data and applying machine learning models.
- **webapp/** - Node.js and Express application for serving the Kibana dashboard.

---

## 🛠️ Technologies

- **Apache Kafka** - Distributed event streaming platform.
- **Apache Spark** - Unified analytics engine for big data processing.
- **Elasticsearch** - Search and analytics engine.
- **Kibana** - Data visualization and exploration tool.
- **Docker** - Containerization platform for deploying applications.
- **Node.js** - JavaScript runtime for building scalable network applications.
- **Express** - Web application framework for Node.js.

---

## 🚀 Getting Started

To run the entire platform locally, use Docker Compose:

```bash
docker-compose up --build
```

This command builds and starts all containers: Kafka, Zookeeper, Spark, Elasticsearch, Kibana, and the producer application.

Access the applications:

- **Kibana:** [http://localhost:5601](http://localhost:5601)
- **Kafka:** [localhost:9092](localhost:9092)
- **Elasticsearch:** [http://localhost:9200](http://localhost:9200)

---

## 📚 Documentation

- **Kafka:** [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- **Spark:** [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- **Elasticsearch:** [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- **Kibana:** [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- **Docker:** [Docker Documentation](https://docs.docker.com/)

---

## 🤝 Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👀 Acknowledgments

- Inspired by the need for scalable and real-time data processing solutions.
- Leveraging open-source technologies for rapid development and deployment.
