# Use the Apache Airflow official image
FROM apache/airflow:2.10.2

# Copy requirements.txt to image
COPY ./requirements.txt ./opt/requirements.txt

# Install python package 
RUN pip install --no-cache-dir -r ./opt/requirements.txt

# Copy service-account.json to image
COPY ./scripts/service-account.json ./opt/airflow/service-account.json

# Set up env variable for Airflow to pass the GCS service authentication
ENV GOOGLE_APPLICATION_CREDENTIALS=./opt/airflow/service-account.json
