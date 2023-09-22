import boto3


# Get SQS resource
sqs = boto3.resource('sqs', region_name = 'us-east-1')

# Get input queue
queue_in = sqs.get_queue_by_name(QueueName = 'InputQueue')

# Get output queue
queue_out = sqs.get_queue_by_name(QueueName = 'OutputQueue')

# Keep checking for new messages
while True:
    message = queue_in.receive_messages()
    print(message.body)
    # Fetch from input queue
        print(message.body)

        # Fetch image from input S3 bucket using ID from input queue

        # Trigger image classifier with fetched image

        # Store result in output S3 bucket

        # Delete the message from the input queue
        message.delete()

# Stop the instance
