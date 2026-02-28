import boto3, time
bedrock = boto3.client('bedrock-agent', region_name='ap-south-1')
for i in range(20):
    r = bedrock.get_ingestion_job(knowledgeBaseId='9X1YUTXNOQ', dataSourceId='XAES6NZN0V', ingestionJobId='T8FPFCLDQK')
    status = r['ingestionJob']['status']
    stats = r['ingestionJob'].get('statistics', {})
    scanned = stats.get('numberOfDocumentsScanned', 0)
    indexed = stats.get('numberOfNewDocumentsIndexed', 0)
    modified = stats.get('numberOfModifiedDocumentsIndexed', 0)
    failed = stats.get('numberOfDocumentsFailed', 0)
    print(f"Attempt {i+1}: {status} | scanned={scanned} indexed={indexed} modified={modified} failed={failed}")
    if status in ('COMPLETE', 'FAILED'):
        break
    time.sleep(5)
