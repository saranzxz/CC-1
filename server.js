const express = require('express');
const multer = require('multer');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { SQS, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } = require('@aws-sdk/client-sqs');


const server = express();
const hostname = '127.0.0.1';
const port = 3000;

const s3 = new S3Client({ region: 'us-east-1' });
const sqsInput = new SQS({ region: 'us-east-1' });
const sqsOutput = new SQS({ region: 'us-east-1' });
// const upload = multer({ dest: 'uploads/' });
const upload = multer({storage: multer.memoryStorage()});
const inputQueueUrl = 'https://sqs.us-east-1.amazonaws.com/800653936604/InputQueue';
const outputQueueUrl = 'https://sqs.us-east-1.amazonaws.com/800653936604/OutputQueue';

const pendingResponses = new Map();
const requestTimeout = 30000; // 30 seconds

const generateUniqueCorrelationId = () => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

server.use(express.json());

server.post('/upload', upload.single('myfile'), async (req, res) => {
  try {
    console.log('Request received');

    if (!req.file) {
      return res.status(400).send('No file in request.');
    }

    const correlationId = generateUniqueCorrelationId();

    const s3Params = {
      Bucket: 'input-bucket-zxz',
      Key: req.file.originalname,
      Body: req.file.buffer,
    };

    const inputSqsParams = {
      QueueUrl: inputQueueUrl,
      MessageBody: JSON.stringify({ imageName: s3Params.Key, correlationId }),
    };
    
    await s3.send(new PutObjectCommand(s3Params));
    console.log('Uploaded image to input S3 bucket');
    await sqsInput.send(new SendMessageCommand(inputSqsParams));
    console.log('Sent message to intput queue');

    pendingResponses.set(correlationId, (imageResult) => {
      clearTimeout(requestTimeoutId);
      res.status(200).json({ imageResult });
    });

    // Set a timeout for the request
    const requestTimeoutId = setTimeout(() => {
      // Handle request timeout
      pendingResponses.delete(correlationId); // Remove the response function
      res.status(504).send('Request timed out.'); // Send a timeout response
    }, requestTimeout);
  } catch (err) {
    console.error(err);
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
    console.log("polling");
    const { Messages } = await sqsOutput.send(new ReceiveMessageCommand(receiveParams))

    if (Messages) {
      const message = JSON.parse(Messages[0].Body);
      const correlationId = message.correlationId;

      const sendResponse = pendingResponses.get(correlationId);

      if (sendResponse) {
        sendResponse(message.imageResult);

        // Remove from pending responses
        pendingResponses.delete(correlationId);

        const deleteParams = {
          QueueUrl: outputQueueUrl,
          ReceiptHandle: Messages[0].ReceiptHandle,
        };
        // TODO: Decide on order of delete. Deleter before responding to user or after. Accordingly visibilitytimeout (default 30s)
        await sqsOutput.send(new DeleteMessageCommand(deleteParams))
      }
    }
  } catch(err) {
    console.error(err);
  }
  // Continue polling
  pollOutputQueue();
};

// Start polling the output queue
pollOutputQueue();

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});