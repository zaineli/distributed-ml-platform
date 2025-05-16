FROM bitnami/spark:3.5

USER root

# Install only essential packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages with pip cache disabled
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    pyarrow \
    py4j \
    influxdb-client \
    kafka-python

WORKDIR /app
COPY consumer.py .

USER 1001