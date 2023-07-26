import boto3

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', 
                          aws_access_key_id='AKIAXFDHSRD2URBMV25P',
                          aws_secret_access_key='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')

table = dynamodb.Table('pricedata')

response = table.scan()
sorted_items = sorted(response['Items'], key=lambda x: int(x['id']))

for item in sorted_items:
    print(item)