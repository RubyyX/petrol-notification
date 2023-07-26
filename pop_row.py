import boto3

def delete_most_recent_row():
    # Initialize a DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', 
                              aws_access_key_id='AKIAXFDHSRD2URBMV25P',
                              aws_secret_access_key='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')

    # Get the DynamoDB table
    table = dynamodb.Table('pricedata')

    # Scan the table and sort the items by 'id' in descending order
    response = table.scan()
    items = sorted(response['Items'], key=lambda x: int(x['id']), reverse=True)

    # Get the 'id' of the most recent row
    most_recent_id = items[0]['id']

    # Delete the most recent row
    table.delete_item(
        Key={
            'id': most_recent_id
        }
    )
    print(f"Row with id {most_recent_id} deleted successfully!")

delete_most_recent_row()