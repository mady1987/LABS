import torch
import torchvision
import torch.nn as nn
from torchvision import transforms
## Add more imports if required

####################################################################################################################
# Define your model and transform and all necessary helper functions here                                          #
# They will be imported to the exp_recognition.py file                                                             #
####################################################################################################################

# Definition of classes as dictionary
classes = {0: 'ANGER', 1: 'DISGUST', 2: 'FEAR', 3: 'HAPPINESS', 4: 'NEUTRAL', 5: 'SADNESS', 6: 'SURPRISE'}

# Example Network
class ExpressionCNN(nn.Module):
    def __init__(self, num_classes=7):
        super(ExpressionCNN, self).__init__()

        self._initialize_weights()

        # Convolutional Block 1
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout = nn.Dropout(0.25) # Dropout prevents overfitting

        # Input: 3x64x64 (1 channel, 64x64 pixels)
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        # Output: 32x32x32

        # Convolutional Block 2
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        # Output: 64x16x16

        # Convolutional Block 3
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        # Output: 128x8x8

        # Flatten the output for the fully connected layers
        self.flatten = nn.Flatten()

        # Fully Connected (Linear) Layers
        self.fc1 = nn.Linear(in_features=128 * 8 * 8, out_features=1024)
        self.fc2 = nn.Linear(in_features=1024, out_features=512)
        self.fc3 = nn.Linear(in_features=512, out_features=256)
        self.fc4 = nn.Linear(in_features=256, out_features=128)

        # Output Layer
        self.fc5 = nn.Linear(in_features=128, out_features=num_classes)

    def forward(self, x):
        # Pass data through the layers
        x = self.pool(self.relu(self.bn1(self.conv1(x))))
        x = self.pool(self.relu(self.bn2(self.conv2(x))))
        x = self.pool(self.relu(self.bn3(self.conv3(x))))

        # Flatten
        x = self.flatten(x)

        # Pass through linear layers
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.dropout(self.relu(self.fc3(x)))
        x = self.dropout(self.relu(self.fc4(x)))
        x = self.fc5(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

class BanuExpressionCNN(nn.Module):
    def __init__(self, num_classes=7):
        super(BanuExpressionCNN, self).__init__()

        def conv_block(in_channels, out_channels):
            # Helper to create a Conv-BN-ReLU -> Conv-BN-ReLU -> Pool block
            return nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2)
            )

        # Input: 1x64x64
        self.block1 = conv_block(1, 64)
        # Output: 64x32x32
        self.block2 = conv_block(64, 128)
        # Output: 128x16x16
        self.block3 = conv_block(128, 256)
        # Output: 256x8x8
        self.block4 = conv_block(256, 512)
        # Output: 512x4x4

        self.flatten = nn.Flatten()

        # Classifier Head
        self.fc = nn.Sequential(
            nn.Linear(512 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(1024, num_classes)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x

# Sample Helper function
def rgb2gray(image):
    return image.convert('L')
    
# Sample Transformation function
#YOUR CODE HERE for changing the Transformation values.
trnscm = transforms.Compose([transforms.Grayscale(num_output_channels=1), transforms.Resize((64,64)), transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5]) ])
 