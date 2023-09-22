import boto3
from logger import log

# Get SQS resource
sqs = boto3.resource('sqs', region_name = 'us-east-1')

# Get input queue
queue_in = sqs.get_queue_by_name(QueueName = 'InputQueue')

# Get output queue
queue_out = sqs.get_queue_by_name(QueueName = 'OutputQueue')

# Keep checking for new messages
while True:
    # Fetch from input queue
    try:
        message = queue_in.receive_messages()

        if not message:
            break

        message = message[0]
        log('DEBUG', 'Message received from input queue: ' + message.body)

        # Fetch image from input S3 bucket using ID from input queue

        # Trigger image classifier with fetched image

        # Store result in output S3 bucket

        # Delete the message from the input queue
        message.delete()
    except Exception as e:
        # Delete message if any issue encountered
        log('ERROR', e)
        message.delete()

# Stop the instance
