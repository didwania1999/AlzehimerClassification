# -*- coding: utf-8 -*-
"""
Author: MuskanDidwania
"""

from google.colab import files
uploaded = files.upload()
!ls -lha kaggle.json
!pip install -q kaggle
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle
!chmod 600 ~/.kaggle/kaggle.json
!pip install --upgrade --force-reinstall --no-deps kaggle

!kaggle datasets download -d tourist55/alzheimers-dataset-4-class-of-images

!unzip alzheimers-dataset-4-class-of-images.zip

from matplotlib import pyplot as plt
import numpy as np
import os
import time
from keras.applications.vgg16 import VGG16
from keras.preprocessing import image
from keras.preprocessing.image import img_to_array,load_img
from keras.applications.imagenet_utils import preprocess_input
from keras.applications.imagenet_utils import decode_predictions
from keras.layers import Dense, Activation, Flatten
from keras.layers import merge, Input
from keras.models import Model
from keras.utils import np_utils
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
import math

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import PIL

try:
    tpu = tf.distribute.cluster_resolver.TPUClusterResolver()
    print('Device:', tpu.master())
    tf.config.experimental_connect_to_cluster(tpu)
    tf.tpu.experimental.initialize_tpu_system(tpu)
    strategy = tf.distribute.experimental.TPUStrategy(tpu)
except:
    strategy = tf.distribute.get_strategy()
print('Number of replicas:', strategy.num_replicas_in_sync)
    
print(tf.__version__)

AUTOTUNE = tf.data.experimental.AUTOTUNE
BATCH_SIZE = 16 * strategy.num_replicas_in_sync
IMAGE_SIZE = [224, 224]
EPOCHS = 5
print(BATCH_SIZE)

train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    "Alzheimer_s Dataset/train",
    labels='inferred',
    validation_split=0.2,
    subset="training",
    seed=1337,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    "Alzheimer_s Dataset/train",
    labels='inferred',
    validation_split=0.2,
    subset="validation",
    seed=1337,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
)

NUM_CLASSES = len(class_names)
class_names = train_ds.class_names
print(class_names)
NUM_CLASSES = len(class_names)

plt.figure(figsize=(10, 10))
for images, labels in train_ds.take(1):
  for i in range(9):
    ax = plt.subplot(3, 3, i + 1)
    plt.imshow(images[i].numpy().astype("uint8"))
    plt.title(train_ds.class_names[labels[i]])
    plt.axis("off")
    print(images[i].numpy().shape)

def one_hot_label(image, label):
    label = tf.one_hot(label, NUM_CLASSES)
    return image, label

train_ds = train_ds.map(one_hot_label, num_parallel_calls=AUTOTUNE)
val_ds = val_ds.map(one_hot_label, num_parallel_calls=AUTOTUNE)

train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

NUM_IMAGES = []

for label in class_names:
    dir_name = "Alzheimer_s Dataset/train/" + label[:-2] + 'ed'
    NUM_IMAGES.append(len([name for name in os.listdir(dir_name)]))

NUM_IMAGES

fig = plt.figure(figsize=(8, 5))
plt.bar(class_names, NUM_IMAGES, width=0.7, align='center')
plt.title("Label Distribution")
plt.xlabel('Label')
plt.ylabel('Count')
plt.xticks(class_names)
plt.ylim(0, 3000)

# for a, b in zip(class_names, NUM_CLASSES):
#     plt.text(a, b, '%d' % b, ha='center', va='bottom', fontsize=10)
plt.show()

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.layers import Dense, Activation, Flatten
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model

num_classes = 4
#input shape
input_layer = Input(shape=(224, 224, 3))

#Use the VGG16 model 
model = VGG16(input_tensor=input_layer, include_top=True,weights='imagenet')

#Summary of the customize VGG16 model
model.summary()

last_layer = model.get_layer('fc2').output
out = Dense(num_classes, activation='softmax', name='output')(last_layer)
custom_vgg_model = Model(input_layer, out)
custom_vgg_model.summary()

for layer in custom_vgg_model.layers[:-1]:
    layer.trainable = False

hist=custom_vgg_model.compile(loss='categorical_crossentropy',optimizer='rmsprop',metrics=['accuracy'])

hist = custom_vgg_model.fit(train_ds, batch_size=32, epochs=20, verbose=1,validation_data=val_ds)

fig, ax = plt.subplots(1, 2, figsize=(20, 3))
ax = ax.ravel()

for i, met in enumerate(['accuracy', 'loss']):
    ax[i].plot(hist.history[met])
    ax[i].plot(hist.history['val_' + met])
    ax[i].set_title('Model {}'.format(met))
    ax[i].set_xlabel('epochs')
    ax[i].set_ylabel(met)
    ax[i].legend(['train', 'val'])

y_predicts = custom_vgg_model.predict(val_ds)
print(y_predicts)
y_predicts.shape

def decoder(val):
  class_names = ['MildDementia', 'ModerateDementia', 'NonDementia', 'VeryMildDementia']
  return class_names[val]

plt.figure(figsize=(10, 10))
for images, labels in val_ds.take(1):
  for i in range(9):
    ax = plt.subplot(3, 3, i + 1)
    plt.imshow(images[i].numpy().astype("uint8"))
    plt.title(decoder(np.argmax(y_predicts[i])))
    plt.axis("off")
    print(images[i].numpy().shape)

"""Testing Images from Unseen Dataset"""

images = image.load_img("Alzheimer_s Dataset/test/NonDemented/26 (100).jpg", target_size=( 224, 224))    
x = image.img_to_array(images)
x = x.reshape(1,x.shape[0],x.shape[1],x.shape[2])
prediction=custom_vgg_model.predict(x)
print(decoder(np.argmax(prediction)))
plt.figure(figsize=(10, 10))
plt.imshow(x[0].astype("uint8"))
plt.axis("off")

images = image.load_img("Alzheimer_s Dataset/test/ModerateDemented/28 (2).jpg", target_size=( 224, 224))    
x = image.img_to_array(images)
x = x.reshape(1,x.shape[0],x.shape[1],x.shape[2])
prediction=custom_vgg_model.predict(x)
print(prediction)
print(decoder(np.argmax(prediction)))
#Result=NonDementia
plt.figure(figsize=(10, 10))
plt.imshow(x[0].astype("uint8"))
# plt.title(decoder(np.argmax(y_predicts[i])))
plt.axis("off")
# print(images[i].numpy().shape)

(loss, accuracy) = custom_vgg_model.evaluate(val_ds, batch_size=100, verbose=10)

accuracy

from tensorflow.keras.utils import plot_model
plot_model(custom_vgg_model,to_file = 'plot.png')



