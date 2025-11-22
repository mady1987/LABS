### History

#### OCTR

Retinal optical coherence tomography (OCT) is an imaging technique that uses coherent light to capture high-resolution of biological tissues. OCT is heavily used by ophthalmologists to obtain high resolution images of the eye retina. Retina of the eye functions much more like a film in a camera. OCT images can be used to diagnose many retina related eyes diseases.

OCT testing has become a standard of care for the assessment and treatment of most retinal conditions. OCT uses rays of light to measure retinal thickness. Approximately 30 million OCT scans are performed each year, and the analysis and interpretation of these images takes up a significant amount of time.





#### Description

The dataset contains subfolders for each image category (NORMAL, CNV, DME, DRUSEN). There are 8054 training X-Ray images (JPEG) and 1000 X-Ray images for testing with 4 categories (NORMAL, CNV, DME, DRUSEN).

Images are labeled as (disease)-(randomized patient ID)-(image number by this patient) and split into 4 directories: CNV, DME, DRUSEN, and NORMAL

![alt text](https://cdn.iiith.talentsprint.com/aiml/Experiment_related_data/Images/OCTR.jpg)


There are four classes in retinal oct images.They are:

1) Choroidal Neovascularization (CNV) : CNV is the creation of new blood vessels in the choroid layer of the eye.

2) Diabetic Macular Edema (DME) : DME is an accumulation of fluid in the macula — part of the retina that controls our most detailed vision abilities — due to leaking blood vessels.

3) Drusen (DRUSEN) : Drusen are yellow deposits under the retina. Drusen are made up of lipids, a fatty protein. Drusen likely do not cause age-related macular degeneration (AMD).

4) Normal Eye Retina (NORMAL) : Normal retina with preserved foveal contour and absence of any retinal fluid/edema.



### VGG16

The VGG16- convolutional network, is trained on ImageNet dataset (1000 classes) which is capable of extracting features from an image and train its fully connected network in order to classify different types of retinal damage instead of objects.