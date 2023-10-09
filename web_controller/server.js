const express = require('express');
const multer = require('multer');
const { EC2Client, RunInstancesCommand } = require("@aws-sdk/client-ec2");
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { SQS, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } = require('@aws-sdk/client-sqs');
const { spawn } = require('child_process');
const winston = require('winston');

const ec2 = new EC2Client({ region: 'us-east-1' });
const s3 = new S3Client({ region: 'us-east-1' });
const sqsInput = new SQS({ region: 'us-east-1' });
const sqsOutput = new SQS({ region: 'us-east-1' });
const inputS3Bucket = 'input-bucket-zxz'
const inputQueueUrl = 'https://sqs.us-east-1.amazonaws.com/800653936604/InputQueue';
const outputQueueUrl = 'https://sqs.us-east-1.amazonaws.com/800653936604/OutputQueue';

const logger = winston.createLogger({
  level: 'info', //(info, debug, error)
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message }) => {
      return `${timestamp} [${level.toUpperCase()}]: ${message}`;
    })
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: '/home/ec2-user/CC-1/web_controller/server.log', level: 'debug' }),
  ],
});

const launchEC2Instance = async () => {
  const params = {
      LaunchTemplate: {
        'LaunchTemplateName': 'initial-template-zxz'
    },
    MinCount: 1,
    MaxCount: 1,
    TagSpecifications: [
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'app_instance1'
                },
            ]
        }
    ]
  };

  try {
    const response = await ec2.send(new RunInstancesCommand (params));
    const instanceId = response.Instances[0].InstanceId;

    logger.info(`Launched EC2 instance with ID: ${instanceId}`);
    return instanceId;
  } catch (err) {
    logger.error('Error launching EC2 instance:', err);
    throw err;
  }
};

(async () => {
  try {
    const instanceId = await launchEC2Instance();

    await new Promise((resolve) => setTimeout(resolve, 10000));

    // Continue only if app-instance1 instance launch was successful
    if (instanceId) {
      const upload = multer({storage: multer.memoryStorage()});

      const pendingResponses = new Map();
      const requestTimeout = 60000; // 60 seconds

      const generateUniqueCorrelationId = () => {
        return Date.now().toString(36) + Math.random().toString(36).slice(2);
      }

      const controllerScript = '/home/ec2-user/CC-1/web_controller/controller.py';
      const controllerProcess = spawn('python3', [controllerScript]);

      controllerProcess.stdout.on('data', (data) => {
        logger.info(`Controller stdout: ${data}`);
      });

      controllerProcess.stderr.on('data', (data) => {
        logger.error(`Controller stderr: ${data}`);
      });

      controllerProcess.on('close', (code) => {
        logger.info(`Controller process exited with code ${code}`);
      });

      const server = express();
      const port = 3000;
      server.use(express.json());

      // Request handler
      server.post('/upload', upload.single('myfile'), async (req, res) => {
        try {
          logger.info('Request received.');

          if (!req.file) {
            logger.error('No file in request.');
            return res.status(400).send('No file in request.');
          }

          const correlationId = generateUniqueCorrelationId();

          const s3Params = {
            Bucket: inputS3Bucket,
            Key: req.file.originalname,
            Body: req.file.buffer,
          };

          const inputSqsParams = {
            QueueUrl: inputQueueUrl,
            MessageBody: JSON.stringify({ imageName: s3Params.Key, correlationId }),
          };

          await s3.send(new PutObjectCommand(s3Params));
          logger.info('Uploaded image to input S3 bucket.');
          await sqsInput.send(new SendMessageCommand(inputSqsParams));
          logger.info('Sent message to intput queue');

          pendingResponses.set(correlationId, (imageResult) => {
            clearTimeout(requestTimeoutId);
            res.status(200).json({ imageResult });
            logger.info('Sent response.');
          });

          // Set a timeout for the request
          const requestTimeoutId = setTimeout(() => {
            // Handle request timeout
            logger.error('Request timed out.');
            pendingResponses.delete(correlationId); // Remove the response function
            res.status(504).send('Request timed out.'); // Send a timeout response
          }, requestTimeout);
        } catch (err) {
          logger.error(err);
          res.status(500).send('Some error occured.');
        }
      });

      const pollOutputQueue = async () => {
        const receiveParams = {
          QueueUrl: outputQueueUrl,
          // AttributeNames: ['All'],
          MaxNumberOfMessages: 1,
          // MessageAttributeNames: ['All'],
          // VisibilityTimeout: 5,
          WaitTimeSeconds: 10
        };
        try {
          logger.debug('Polling');
          const { Messages } = await sqsOutput.send(new ReceiveMessageCommand(receiveParams))

          if (Messages) {
            const message = JSON.parse(Messages[0].Body);
            const correlationId = message.correlationId;

            const sendResponse = pendingResponses.get(correlationId);

            if (sendResponse) {
              logger.debug('Sending response.');
              sendResponse(message.imageResult);

              // Remove from pending responses
              pendingResponses.delete(correlationId);
              logger.debug('Deleted from pendingResponses map.');
            }
            else {
              logger.error('No matching request found.');
            }
            const deleteParams = {
              QueueUrl: outputQueueUrl,
              ReceiptHandle: Messages[0].ReceiptHandle,
            };
            // TODO: Decide on order of delete. Deleter before responding to user or after. Accordingly visibilitytimeout (default 30s)
            await sqsOutput.send(new DeleteMessageCommand(deleteParams))
            logger.info('Deleted message from output queue');
          }
        } catch(err) {
          logger.error(err);
        }
        // Continue polling
        pollOutputQueue();
      };

      // Start polling the output queue
      pollOutputQueue();

      server.listen(port, () => {
        logger.info(`Server running`);
      });

    }
  } catch (err) {
    logger.log('EC2 instance launch failed:', err);
  }
})();