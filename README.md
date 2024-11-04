# AirflowWithBigQuery

## Project Description
This project is about using Apache Airflow to manage the end-to-end data flow. This data flow will extract the public dataset (austin_bikeshare) in BigQuery, transform and store the data in Google Cloud Storage (GCS) in a partitioned format, and then create an external table in BigQuery to facilitate querying and analysis. 
The pipeline executes on every day 1am. The data from the BigQuery will be partitioned by date and hour, and save in parquet file format to ensure scalability and efficiency. Since the amount of data is not a huge amount, this project decides to use python as the data processing engine. If the data amount is going up sharply 
in the future and cannot be handled by python, we suggest to use the spark to deal with that situation. Last, in order to ensure consistency and portability across different environments, this project use docker to launch the service and execute the data pipeline.

## Technologies

- Docker: 27.2.0
- Docker-compose: v2.29.2-desktop.2
- Apache Airflow: 2.10.2
- Python: 3.12.6
- Google BigQuery

## Project structure

```
zeals/
├── dags/
│   └── bikeshare_etl.py
├── scripts/
│   └── service_account.json
│   └── dataAnalysis.sql
├── utils/
│   └── __init__.py
│   └── sqlQuery_utils.py
│   └── tableSchema_utils.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

- **DAGS FOLDER**: This folder contains the data pipeline dag file which will be executed in airflow. By adding one dag file here, one new dag appears in Airflow UI and can be executed. The bikeshare_etl.py is only dag file in this folder, this dag represent a data pipeline which will extract the public dataset (austin_bikeshare) in BigQuery, transform and store the data in Google Cloud Storage (GCS)
- **SCRIPTS FOLDER**: It has service_account.json. This json file is the credential for connecting to the Google cloud service. Due to the security concern, now this json file is empty. After you pull this repo, please replace this empty json file with your Google cloud credential json file. The dataAnalysis.sql is the SQL answer for the SQL question in the assignment.
- **UTILS FOLDER**: This folder contains two files, sqlQuery_utils.py and tableSchema_utils.py. sqlQuery_utils.py has the SQL command template which will be imported by bikeshare_etl.py. And, tableSchema_utils has the bikeShareTripsTableSchema table schema also will be imported by bikeshare_etl.py.
- **DOCKERFILE**: A script that contains a series of instructions to build a Docker image. User needs this file for building the docker image which is needed in this project.
- **DOCKER-COMPOSE.YML**: A configuration file used by Docker Compose to define and manage multi-container Docker applications. User uses this file to launch the airflow service in the local environment.
- **REQUIREMENTS.TXT**: A standard file used in Python projects to specify the dependencies required for the project to run. Can check this file to see which python package is needed in the project.
- **README.MD**: A file presents details about this project

## Project prerequisites
- Docker Desktop: This project needs the Docker Desktop. Before you run this project, please make sure you install Docker Desktop in your local environment. The detail about installing the Docker Desktop can refer to "Environment setup->Local environment->step4"

## Environment setup
### Google cloud environment
- **STEP1**: Register a Google cloud account

- **STEP2**: Add BigQuery external connection - Access to your google cloud account. In your Google Cloud console, find "BigQuery" product and click it. After you enter the product page, the left panel will show your project information. Please keep the project ID information. On the top of the left panel, Click the ADD button and a new page will pop out. In this new page, click the "connection to external data sources" option. In the setting up page, choose "Vertex AI remote models, remote functions and BigLake" for connection type section. Then, fill a connection ID in the connection ID section. Other sections can use the default settings. After you finish it, go back to the left panel and find the "External connection". Click this "External connection" and find the created connection. Then, click this connection to find "Connection ID" information and "Service account id" information. This two parameter is necessary for this project. In sum, in this step, you need to keep three parameters which are projectID, Connection ID, and Service account id.

- **STEP3**: Retrieve the service-account.json from Google cloud - Go to the Google Cloud Console. Navigate to the IAM & Admin section. Click the "Create Service Account" button at the top of the page and enter a name and description for the service account, then click "Create". Assign the necessary roles for the service account based on what access it needs. In our demo case, we choose BigQuery Admin role/ Storage Admin role/ Storage Object Admin role. (Note: in the prod env, you need to follow the least privilege principle). After creating the service account, you will see an option to create a key. Click on "Add Key" and select "JSON". A file named service-account-key.json will be generated and automatically downloaded to your computer.

### Local environment
- **STEP1**: Clone this repository:
   ```
   git clone https://github.com/username/repo.git
   ```
- **STEP2**: Change the service-account.json - Use the service-account.json you get from "Google cloud environment step3" to replace the service-account.json in scripts folder

- **STEP3**: Change some settings in the bikeshare_etl.py file - In "Google cloud environment step2", you keep projectID, Connection ID, and Service account id. Now we need to use these three parameter to replace the default setting. In bikeshare_etl.py job settings section, you can find destinationProjectId setting, bigQueryExternalConnectionID setting, bigQueryExternalConnectionServiceAccountID setting. Assign projectID to destinationProjectId. Assign Connection ID to bigQueryExternalConnectionID. Assign Service account id to bigQueryExternalConnectionServiceAccountID. Like below
   ```
   projectID --> destinationProjectId
   Connection ID --> bigQueryExternalConnectionID
   Service account id --> bigQueryExternalConnectionServiceAccountID

- **STEP4**: Install Docker Desktop on your Mac, please reference to below Docker Desktop official website
   ```
   Docker Desktop official website: https://docs.docker.com/desktop/install/mac-install/
   
- **STEP5**: Build a docker image in your local side
   ```
   docker build -t airflow-withGCPKey-image .

## Run project
- **STEP1**: Launch up the airflow service by using docker-compose
   ```
   docker-compose up -d 
   ```
- **STEP2**: Connect to the Airflow web UI - Open your web browser, type "localhost:8081" and connect to the Airflow UI. The Airflow UI will ask you to fill up userId and password. The userId is admin and password is airflow.

- **STEP3**: Execute the bikeshare_etl data pipeline - After connecting to Airflow Web ui, the bikeshare_etl data pipeline is on the page. You can check the information of this data pipeline by click the data pipeline. To execute this data pipeline, please click "Pause/Unpause DAG button". After clickign it, the data pipeline will execute automatically. (NOTE: In bikeshare_etl, this data pipeline has the "catchup=True setting" and the "start_date=2024,6,1 setting". This setting means that while you trigger the data pipeline, it will check the difference between current time and the start time. If the system finds there is no execution history in this time period, system will back-fill the data for these missing days. For example, the start_date in bikeshare_etl is 2024/06/01 and the current time is 2024/11/04. While we turn on this dag, system will check whether there are any execution history in this time period. If system cannot find the execution history, it will execute this data pipeline from 2024/06/01 to 2024/11/04 to "back-fill" these missing execution history. If you check this job in Airflow webUI, you can find the running history from from 2024/06/01 to 2024/11/04.)

- **STEP4**: Check the result in Google GCS and Google BigQuery - After the job is executed and finished, can go to the Google Cloud Console. By clicking the GCS, can check whether the data which is fetched by our data pipeline is kept in the GCS or not. By clicking the BigQuery, can have a query to check whether we can query the data from the data pipeline destination table or not.

- **STEP5**: Stop the Airflow service
   ```
   docker-compose down