import boto3
import os

os.environ['AWS_PROFILE'] = "local Windows"
os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

# Create SQS client
sqs = boto3.client('sqs')

queue_url = 'https://sqs.us-east-1.amazonaws.com/800653936604/InputQueue'

# # Send message to SQS queue
# response = sqs.send_message(
#     QueueUrl=queue_url,
#     DelaySeconds=10,
#     MessageAttributes={    },
#     MessageBody=(
#         'image_id = 1'
#     )
# )

queue_attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
message_count = queue_attributes['Attributes']['ApproximateNumberOfMessages']



print(message_count);