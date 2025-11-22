import numpy as np
import cv2
from matplotlib import pyplot as plt
import torch
# In the below line,remove '.' while working on your local system. However Make sure that '.' is present before face_recognition_model while uploading to the server, Do not remove it.
from .face_recognition_model import *
from PIL import Image
import base64
import io
import os
import joblib
import pickle
# Add more imports if required



###########################################################################################################################################
#         Caution: Don't change any of the filenames, function names and definitions                                                      #
#        Always use the current_path + file_name for refering any files, without it we cannot access files on the server                  # 
###########################################################################################################################################

# Current_path stores absolute path of the file from where it runs. 
current_path = os.path.dirname(os.path.abspath(__file__))

#1) The below function is used to detect faces in the given image.
#2) It returns only one image which has maximum area out of all the detected faces in the photo.
#3) If no face is detected,then it returns zero(0).

def detected_face(image):
    eye_haar = current_path + '/haarcascade_eye.xml'
    face_haar = current_path + '/haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(face_haar)
    eye_cascade = cv2.CascadeClassifier(eye_haar)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    face_areas=[]
    images = []
    required_image=0
    for i, (x,y,w,h) in enumerate(faces):
        face_cropped = gray[y:y+h, x:x+w]
        face_areas.append(w*h)
        images.append(face_cropped)
        required_image = images[np.argmax(face_areas)]
        required_image = Image.fromarray(required_image)
    return required_image


#1) Define an object to your siamese network here in the function and load the weight from the trained network, set it in evaluation mode.
#2) Get the features for both the faces from the network and return the similarity measure, Euclidean,cosine etc can be it. But choose the Relevant measure.
#3) For loading your model use the current_path+'your model file name', anyhow detailed example is given in comments to the function 
#Caution: Don't change the definition or function name; for loading the model use the current_path for path example is given in comments to the function
def get_similarity(img1, img2):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    det_img1 = detected_face(img1)
    det_img2 = detected_face(img2)
    if(det_img1 == 0 or det_img2 == 0):
        det_img1 = Image.fromarray(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY))
        det_img2 = Image.fromarray(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY))
    face1 = trnscm(det_img1).unsqueeze(0)
    face2 = trnscm(det_img2).unsqueeze(0)
    ##########################################################################################
    ##Example for loading a model using weight state dictionary:                            ##
    ## feature_net = light_cnn() #Example Network                                           ##
    ## model = torch.load(current_path + '/siamese_model.t7', map_location=device)          ##
    ## feature_net.load_state_dict(model['net_dict'])                                       ##
    ##                                                                                      ##
    ##current_path + '/<network_definition>' is path of the saved model if present in       ##
    ##the same path as this file, we recommend to put in the same directory                 ##
    ##########################################################################################
    ##########################################################################################
    
    # YOUR CODE HERE, load the model
    feature_net = Siamese().to(device)
    model = torch.load(current_path + '/siamese_model.t7', map_location=device)
    feature_net.load_state_dict(model['net_dict'])
    feature_net.eval()

    # YOUR CODE HERE, return similarity measure using your model
    with torch.no_grad():
        face1 = face1.to(device)
        face2 = face2.to(device)
        output1 = feature_net(face1)
        output2 = feature_net(face2)
        # Example: Euclidean Distance
        euclidean_distance = F.pairwise_distance(output1, output2)
        return euclidean_distance.item()
    
    return 0
    
#1) Define an object to your network here in the function and load the weight from the trained network, set it in evaluation mode
#2) Perform necessary transformations to the input(detected face using the above function).
#3) Along with the siamese, you need the classifier as well, which is to be finetuned with the faces that you are training
##Caution: Don't change the definition or function name; for loading the model use the current_path for path example is given in comments to the function
def get_face_class(img1):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    det_img1 = detected_face(img1)
    if(det_img1 == 0):
        det_img1 = Image.fromarray(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY))
    ##YOUR CODE HERE, return face class here

    svcClassifier = joblib.load(os.path.join(current_path, "decision_tree_model.sav"))

    feature_net = Siamese().to(device)
    model = torch.load(current_path + '/siamese_model.t7', map_location=device)
    feature_net.load_state_dict(model['net_dict'])
    feature_net.eval()
    face1 = trnscm(det_img1).unsqueeze(0)
    with torch.no_grad():
        face1 = face1.to(device)
        output1 = feature_net(face1)
        output1 = output1.cpu().numpy()
        predicted_class_index = svcClassifier.predict(output1)
        predicted_class = classes[predicted_class_index[0]]
        return predicted_class_index[0]

    ##Hint: you need a classifier finetuned for your classes, it takes o/p of siamese as i/p to it
    ##Better Hint: Siamese experiment is covered in one of the labs
    return "YET TO BE CODED"