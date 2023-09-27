import boto3
import os
import schedule
import time

os.environ["AWS_PROFILE"] = "local Windows"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

def autoScaler():
    # Create SQS client
    sqs = boto3.client("sqs")
    queue_url = "https://sqs.us-east-1.amazonaws.com/800653936604/InputQueue"

    queue_attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"])
    message_count_in_queue = queue_attributes["Attributes"]["ApproximateNumberOfMessages"]


    # Create EC2 client
    ec2 = boto3.client("ec2")     
    instances = ec2.describe_instances(Filters=[
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
            response = ec2.terminate_instances(
                InstanceIds = stopped_instances 
            )            
        except:
            print("Termination failed, will terminate in next iteration")
        return

    # max number of machines is limited to 12
    machines_needed = min(message_count_in_queue // 4, 12)
    machines_needed -= len(running_instances)
    try:
        response = ec2.start_instances(
            InstanceIds = stopped_instances,
        )
        machines_needed -= len(stopped_instances)
    except:
        pass

    if(machines_needed > 0 ):
        #create new instances
        pass
     

schedule.every(1).minutes.do(autoScaler)
  
while True:
    schedule.run_pending()
    time.sleep(5)
