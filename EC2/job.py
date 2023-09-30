import boto3
from logger import log
import re
import subprocess
from image_classification import predict
import os
from ec2_metadata import ec2_metadata
import json
import time

def parseImageID(id):
    if re.match('^\w+.(jpg|jpeg|JPG|JPEG)$', id):
        return id
    else:
        return -1

root_dir = '/home/ubuntu/app-tier/CC-1/'

# Get resources
sqs = boto3.resource('sqs', region_name = 'us-east-1')
s3 = boto3.client('s3')
ec2 = boto3.client('ec2', region_name = 'us-east-1')


# Get input queue
queue_in = sqs.get_queue_by_name(QueueName = 'InputQueue')

# Get output queue
queue_out = sqs.get_queue_by_name(QueueName = 'OutputQueue')

# Keep checking for new messages
while True:
    # Fetch from input queue
    try:
        message_sqs = queue_in.receive_messages()

        if not message_sqs:
            time.sleep(2)
            continue

        message = json.loads(message_sqs[0].body)

        log('DEBUG', 'Message received from input queue: ' + str(message))

        # Fetch image from input S3 bucket using ID from input queue
        id, corId = (parseImageID(message['imageName']), message['correlationId'])

        if id == -1:
            log('ERROR', 'Invalid ID obtained from input queue')

        obj = s3.get_object(Bucket = 'input-bucket-zxz', Key = id)
        img = obj['Body'].read()
        outfh = open(root_dir + id, 'wb')
        outfh.write(img)
        outfh.close()


        # Trigger image classifier with fetched image
        # res = subprocess.run(['python3 ../image_classification.py {}'.format(id)], shell = True,\
        # capture_output = True, text = True)
        # print(res.stdout)
        res = predict(root_dir + id)
        log('INFO', 'message: {} predicted as: {}'.format(id, res))

        # Store result in output S3 bucket
        s3.put_object(Bucket = 'output-bucket-zxz', Key = id.split('.')[0],\
        Body = '({}, {})'.format(id.split('.')[0], res))
        log('INFO', 'Saved result: ({}, {}) to output-bucket-zxz'.format(id.split('.')[0], res))

       # Send output to output queue
        queue_out.send_message(MessageBody = json.dumps({ "imageResult": res, "correlationId": corId }))
        log('INFO', 'Response sent for image: {}'.format(id))

        # Delete the message from the input queue
        message_sqs[0].delete()
        log('INFO', 'message: {} deleted'.format(id))

        # Delete locally stored image to save space
        os.remove(root_dir + id)
        log('INFO', 'Locally saved file {} removed'.format(id))
    except Exception as e:
        # Log error
        log('ERROR', str(e))

# Stop the instance
# ec2.stop_instances(InstanceIds = [ec2_metadata.instance_id], DryRun = False)
