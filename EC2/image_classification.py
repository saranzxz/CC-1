import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from urllib.request import urlopen
from PIL import Image
import numpy as np
import json
import sys
import time


model = models.resnet18(pretrained=True)
model.eval()


def predict(path):
    img = Image.open(path)
    img_tensor = transforms.ToTensor()(img).unsqueeze_(0)
    outputs = model(img_tensor)
    _, predicted = torch.max(outputs.data, 1)

    with open('EC2/imagenet-labels.json') as f:
        labels = json.load(f)
    result = labels[np.array(predicted)[0]]
    img_name = path.split("/")[-1]
    #save_name = f"({img_name}, {result})"
    save_name = f"{img_name},{result}"
    
    return save_name.split(',')[1]