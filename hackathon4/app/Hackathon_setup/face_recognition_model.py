import math
import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
# Add more imports if required

# Sample Transformation function
# YOUR CODE HERE for changing the Transformation values.
trnscm = transforms.Compose([transforms.Resize((100,100)), transforms.ToTensor()])

##Example Network
class Siamese(torch.nn.Module):
    def __init__(self):
        super(Siamese, self).__init__()
        self.cnn1 = nn.Sequential(
            nn.ReflectionPad2d(1),       #Pads the input tensor using the reflection of the input boundary, it similar to the padding.
            nn.Conv2d(1, 4, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(4),

            nn.ReflectionPad2d(1),
            nn.Conv2d(4, 8, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(8),


            nn.ReflectionPad2d(1),
            nn.Conv2d(8, 8, kernel_size=3),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(8),
        )

        self.fc1 = nn.Sequential(
            nn.Linear(8*100*100, 500),
            nn.ReLU(inplace=True),

            nn.Linear(500, 500),
            nn.ReLU(inplace=True),

            nn.Linear(500, 5))
        
    def forward(self, x):
        x = self.cnn1(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        return x

##########################################################################################################
## Sample classification network (Specify if you are using a pytorch classifier during the training)    ##
## classifier = nn.Sequential(nn.Linear(64, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Linear...)           ##
##########################################################################################################

# YOUR CODE HERE for pytorch classifier


# Definition of classes as dictionary
classes = ['person1','person2','person3','person4','person5','person6','person7']


classifier = nn.Sequential(
    nn.Linear(5, 64),
    nn.BatchNorm1d(64),
    nn.ReLU(),
    nn.Linear(64, 32),
    nn.BatchNorm1d(32),
    nn.ReLU(),
    nn.Linear(32, len(classes))  # len(classes) gives number of classes
)