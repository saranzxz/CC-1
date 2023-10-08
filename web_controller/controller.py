import boto3
import os
import schedule
import time

#Stuff to move to envs
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
queue_url = "https://sqs.us-east-1.amazonaws.com/800653936604/InputQueue"
scale_launch_template = {"LaunchTemplateName" : "scale-template-zxz"}
instance_number = 2

def createInstanceFromTemplate(ec2_resource, instance_number):
     ec2_resource.create_instances(
            LaunchTemplate = scale_launch_template, 
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'app_instance'+ str(instance_number)
                        },
                    ]
                }
            ]
        )

def autoScaler():
    # Create SQS client
    sqs = boto3.client("sqs")

    queue_attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"])
    message_count_in_queue = int(queue_attributes["Attributes"]["ApproximateNumberOfMessages"])


    # Create EC2 client
    ec2_client = boto3.client("ec2")     
    instances = ec2_client.describe_instances(Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running','stopped','pending','stopping']
                },
        ],)

    instance_data = []
    for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_data.append(
                            {
                                'instance_id': instance['InstanceId'],
                                'instance_state': instance['State']['Name'],
                                'launch_date': instance['LaunchTime'].strftime('%Y-%m-%dT%H:%M:%S.%f')
                            }
                        )

    running_instances = []
    stopped_instances = []
    for instance in instance_data:
            if(instance['instance_state'] in ['running','pending']):
                running_instances.append(instance['instance_id'])
            else:
                stopped_instances.append(instance['instance_id'])

    if(message_count_in_queue == 0):
        try:
            response = ec2_client.terminate_instances(
                InstanceIds = stopped_instances 
            )            
        except:
            print("Termination failed, will terminate in next iteration")
        return

    # max number of machines is limited to 12
    machines_needed = min(message_count_in_queue // 4, 12)
    machines_needed -= len(running_instances)
    machines_to_start = []
    if(machines_needed <= len(stopped_instances)):
        machines_to_start = stopped_instances[:machines_needed]
        machines_needed = 0
    else:
        machines_to_start = stopped_instances
        machines_needed -=len(stopped_instances)

    try:
        response = ec2_client.start_instances(
            InstanceIds = machines_to_start,
        )
    except:
        pass

    if(machines_needed > 0 ):
        ec2_resource = boto3.resource('ec2')
        for i in range(machines_needed):
            createInstanceFromTemplate(ec2_resource= ec2_resource, instance_number= instance_number + i)
        instance_number += machines_needed
     
schedule.every(3).seconds.do(autoScaler)
  
while True:
    schedule.run_pending()
    # time.sleep(5)
