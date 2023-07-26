import boto3
from boto3.dynamodb.conditions import Key

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', 
                          aws_access_key_id='AKIAXFDHSRD2URBMV25P',
                          aws_secret_access_key='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')

# Get the DynamoDB table
table = dynamodb.Table('pricedata')

response = table.scan()

items = sorted(response['Items'], key=lambda x: int(x['id']), reverse=True)

if len(items) >= 2: # ensure we have two records (today's and the most recent one)
    last_record = items[1] # return the second last record (most recent excluding today's)
else:
    last_record = None # return None if there's not enough data
    
print(last_record)
