fetchQueryTemplate = """
    SELECT *
    FROM `{projectName}.{datasetName}.{tableName}`
    ;
"""

fetchQueryTemplateWithWhereCondition = """
    SELECT *
    FROM `{projectName}.{datasetName}.{tableName}`
    WHERE {condition}
    ;
"""

createTableQueryTemplate = """
    CREATE OR REPLACE EXTERNAL TABLE `{projectId}.{datasetName}.{tableName}`
    (
        {schema}
    )
    WITH PARTITION COLUMNS
    (
        date STRING,
        hour STRING
    )
    WITH CONNECTION `{bigQueryExternalConnectionID}`
    OPTIONS (
        format = '{fileFormat}',
        uris = ['{gcsURI}'],
        hive_partition_uri_prefix = '{partitionPrefix}'
    )
"""
