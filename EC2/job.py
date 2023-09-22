import boto3
from logger import log
import re
import subprocess
from image_classification import predict
import os

def parseImageID(id):
    if re.match('^\w+.(jpg|jpeg|JPG|JPEG)$', id):
        return id
    else:
        return -1


# Get resources
sqs = boto3.resource('sqs', region_name = 'us-east-1')
s3 = boto3.client('s3')


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
        id = parseImageID(message.body)

        if id == -1:
            log('ERROR', 'Invalid ID obtained from input queue')
        
        obj = s3.get_object(Bucket = 'output-bucket-zxz', Key = id)
        img = obj['Body'].read()
        outfh = open(id, 'wb')
        outfh.write(img)
        outfh.close()


        # Trigger image classifier with fetched image
        # res = subprocess.run(['python3 ../image_classification.py {}'.format(id)], shell = True,\
        # capture_output = True, text = True)
        # print(res.stdout)
        res = predict(id)
        print(res)
        log('INFO', 'message: {} predicted as: {}'.format(id, res))

        # Store result in output S3 bucket

        # Delete the message from the input queue
        message.delete()
        log('INFO', 'message: {} deleted'.format(id))

        # Delete locally stored image to save space
        os.remove(id)
        log('INFO', 'Locally saved file {} removed'.format(id))
    except Exception as e:
        # Delete message if any issue encountered
        log('ERROR', str(e))
        message.delete()
        log('INFO', 'message: {} deleted'.format(id))

# Stop the instance
