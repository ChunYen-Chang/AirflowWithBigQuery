# import packages
import time
import pandas as pd
import pendulum
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud import storage
from google.oauth2 import service_account
from io import BytesIO

from utils.sqlQuery_utils import fetchQueryTemplateWithWhereCondition
from utils.sqlQuery_utils import createTableQueryTemplate
from utils.tableSchema_utils import bikeShareTripsTableSchema


# job settings section
gcsBucketName = "zeals-assignment"
gcsBucketFolderName = "bikeshare/"

sourceProjectName = "bigquery-public-data"
sourceDatasetName = "austin_bikeshare"
sourceTableName = "bikeshare_trips"
fetchWhereCondition = "start_time BETWEEN '{startDate} 00:00:00' AND '{endDate} 23:59:59'"
fetchQuery = fetchQueryTemplateWithWhereCondition.format(projectName=sourceProjectName, datasetName=sourceDatasetName, tableName=sourceTableName, condition = fetchWhereCondition)

destinationProjectId = "bigqueryproject-440214"
destinationDatasetName = "zeals_assignment"
destinationTableName = "bikeshare_trip"
bigQueryExternalConnectionID = "projects/bigqueryproject-440214/locations/us/connections/testConnection"
bigQueryExternalConnectionServiceAccountID = "serviceAccount:bqcx-623082554964-umir@gcp-sa-bigquery-condel.iam.gserviceaccount.com"
fileFormat = "PARQUET"
gcsURI = "gs://{gcsBucketName}/{gcsBucketFolderName}*".format(gcsBucketName=gcsBucketName, gcsBucketFolderName=gcsBucketFolderName)
partitionPrefix = "gs://{gcsBucketName}/{gcsBucketFolderName}".format(gcsBucketName=gcsBucketName, gcsBucketFolderName=gcsBucketFolderName)
metadataCacheMode = "AUTOMATIC"
maximumStaleness = "3 hours"
createTableQuery = createTableQueryTemplate.format(projectId=destinationProjectId, datasetName=destinationDatasetName, tableName=destinationTableName, schema=bikeShareTripsTableSchema, bigQueryExternalConnectionID=bigQueryExternalConnectionID, fileFormat=fileFormat, gcsURI=gcsURI, partitionPrefix=partitionPrefix,metadataCacheMode=metadataCacheMode, maximumStaleness=maximumStaleness)


# define python unctions
def fetchBigQueryDateAndUploadToGCS(fetchQuery, bucketName, folderName, bigQueryExternalConnectionServiceAccountID, **context):
    # Below part for fetching data from BigQuery
    # Retrieve fetchQueryWithRetrieveDate
    dagExecutionTime = context['execution_date']
    dagExecutionTimeInLocalTimezone = pendulum.instance(dagExecutionTime).in_tz('Asia/Taipei')
    dagExecutionDate = dagExecutionTimeInLocalTimezone.date()
    retrieveDate = dagExecutionDate - timedelta(days=1)
    fetchQueryWithRetrieveDate = fetchQuery.format(startDate=str(retrieveDate), endDate=str(retrieveDate))
    print("Fetch query : " + fetchQueryWithRetrieveDate)

    # create bigquery client
    print("Start fetch data from bigQuery.")
    bigQueryClient = bigquery.Client()

    # fetch bigQuery data
    queryJob = bigQueryClient.query(fetchQueryWithRetrieveDate)
    bigQueryResultDf = queryJob.to_dataframe(create_bqstorage_client=True)
    print("Finish fetching data from bigQuery.")

    # bigQueryResultDf row number check
    bigQueryResultDfRowNumber = len(bigQueryResultDf)
    if bigQueryResultDfRowNumber == 0:
        print("Fetch 0 rows of data, upstream table does not have data today, will skip fetchBigQueryDateAndUploadToGCS stage")
        return

    # Below part for uploading data to GCS
    # create Google cloud Storage client
    print("Start upload parquet file to to Google cloud storage.")
    storageClient = storage.Client()

    # check bucket exist
    buckets = list(storageClient.list_buckets())
    if bucketName not in [bucket.name for bucket in buckets]:
        print("Cannot find " + bucketName + " bucket, try to create this bucket.")
        bucket = storageClient.create_bucket(bucketName)
        print("Successfully create " + bucketName + "bucket.")

        bucketPolicy = bucket.get_iam_policy()
        objectViewerRole = "roles/storage.objectViewer"
        bucketPolicy[objectViewerRole] = set()
        bucketPolicy[objectViewerRole].add(bigQueryExternalConnectionServiceAccountID)
        objectCreatorRole = "roles/storage.objectCreator"
        bucketPolicy[objectCreatorRole] = set()
        bucketPolicy[objectCreatorRole].add(bigQueryExternalConnectionServiceAccountID)
        bucket.set_iam_policy(bucketPolicy)
        print("Successfully add objectViewer and objectCreator permission for " + bigQueryExternalConnectionServiceAccountID + " .")

    # partition bigQueryResultDf by hour
    groupedDf = bigQueryResultDf.groupby(bigQueryResultDf['start_time'].dt.floor('h'))

    # upload file to GCS
    bucket = storageClient.bucket(bucketName)
    for startTime, eachDf in groupedDf:
        # parse data and hour inf from startTime
        date = startTime.strftime('%Y-%m-%d')
        hour = startTime.strftime('%H')
        gcsFilePath = folderName + "date=" + date + "/hour=" + hour + "/data.parquet"

        # convert dataframe into an arrow table
        table = pa.Table.from_pandas(eachDf, preserve_index = False)

        # write an Arrow table directly into a in-memory buffer
        buffer = BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)  

        # upload parquet file to GCS
        blob = bucket.blob(gcsFilePath)
        blob.upload_from_file(buffer, content_type='application/parquet')
        print("successfully upload parquet file to " + gcsFilePath + "...")

    print("Finish uploading parquet file to Google cloud storage")

def createBiglakeExternalTable(createTableQuery, projectId, datasetName, bucketName, folderName, gcsURI):
    # Bucket empty check
    storageClient = storage.Client()
    bucket = storageClient.bucket(bucketName)
    blobs = bucket.list_blobs(prefix=folderName)
    parquetFiles = [blob.name for blob in blobs if blob.name.endswith('.parquet')]
    if len(parquetFiles) == 0:
        print("Bucket " + bucketName + " with folder "+ folderName + " is empty. Skip to create external biglake table")
        return

    # create bigquery client
    bigQueryClient = bigquery.Client()

    # dataset exist check
    datasets = bigQueryClient.list_datasets(projectId)
    if datasetName not in [dataset.dataset_id for dataset in datasets]:
        print("Cannot find " + datasetName + " dataset, try to create this dataset.")
        dataset = bigQueryClient.create_dataset(datasetName)
        print("Successfully create " + datasetName + "dataset.")

    # Create external biglake table
    print("Start create external biglake table from GCS URI " + gcsURI)
    print("Create table query : " + createTableQuery)
    queryJob = bigQueryClient.query(createTableQuery)

    # Wait for the job to complete
    while not queryJob.done():
        print("still creating external biglake table from GCS URI " + gcsURI)
        time.sleep(1)

    print("successfully create external biglake table from GCS URI " + gcsURI)


# define airflow DAG
dagTimeZone = pendulum.timezone("Asia/Taipei")

default_args = {
    'owner': 'airflow',
    'start_date': dagTimeZone.datetime(2024, 6, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='bikeshare_etl',
    default_args=default_args,
    schedule_interval='0 1 * * *',
    catchup=True,  # 之後要改為true
    max_active_runs=1
) as dag:    

    start_task = DummyOperator(
        task_id='start'
    )

    fetch_and_upload_task = PythonOperator(
        task_id='fetchBigQuery_and_uploadGCS_task',
        python_callable=fetchBigQueryDateAndUploadToGCS,
        provide_context=True,
        op_kwargs={'fetchQuery': fetchQuery, 'bucketName': gcsBucketName, 'folderName': gcsBucketFolderName, 'bigQueryExternalConnectionServiceAccountID': bigQueryExternalConnectionServiceAccountID},
    )

    create_external_biglake_table_task = PythonOperator(
        task_id='create_external_biglake_table_task',
        python_callable=createBiglakeExternalTable,
        op_kwargs={'createTableQuery': createTableQuery, 'projectId': destinationProjectId, 'datasetName': destinationDatasetName, 'bucketName': gcsBucketName, 'folderName': gcsBucketFolderName, 'gcsURI': gcsURI},
    )

    end_task = DummyOperator(
        task_id='end'
    )

    start_task >> fetch_and_upload_task >> create_external_biglake_table_task >> end_task

