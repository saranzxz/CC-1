# CC-1

Cloud Computing Project 1

These are the instructions to run the project.

1. After logging in to AWS, launch an instance using the `web-tier-template-zxz` 
> EC2 -> Instances -> Instances -> Launch instance from template 

This spawns the web-tier EC2 instance. It already has the required code, python libraries and node modules installed. The server starts automatically on instance launch.

2. Run the `multithreaded_workload_generator.py` script with the URL `http://<instance_public_ip>:3000/upload`

3. You should see the image results as responses.