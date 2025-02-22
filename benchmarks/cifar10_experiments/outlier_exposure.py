#%%
import tensorflow as tf
import pickle
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets
tf.compat.v1.enable_eager_execution()
from kdg.utils import generate_gaussian_parity, generate_ood_samples, generate_spirals, generate_ellipse
from sklearn.metrics import roc_auc_score
from tensorflow import keras
from scipy.io import loadmat
import random
from tensorflow import keras
from tensorflow.keras.layers import Dense, Conv2D, BatchNormalization, Activation
from tensorflow.keras.layers import AveragePooling2D, Input, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, LearningRateScheduler
from tensorflow.keras.callbacks import ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.regularizers import l2
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.datasets import cifar100, cifar10
from tqdm import tqdm
from tensorflow.keras import layers

#%% load OOD data
ood_set = np.load('/Users/jayantadey/kdg/benchmarks/300K_random_images.npy')

#%%
def cross_ent(logits, y):
    logits = tf.nn.softmax(logits, axis=1)
    losses = tf.keras.losses.CategoricalCrossentropy(from_logits=True)
    
    return losses(logits, y)


def max_conf(logits):
    losses = -tf.reduce_mean(tf.reduce_mean(logits, 1) - tf.reduce_logsumexp(logits,axis=1))
    return losses


#%%
batchsize = 128 # orig paper trained all networks with batch_size=128
epochs = 30
data_augmentation = False
num_classes = 10
seed = 400
input_shape = (32,32,3)
#%% load pretrained model weights
print('loading weights')
with open('/Users/jayantadey/kdg/benchmarks/cifar10_experiments/pretrained_weight_contrast.pickle', 'rb') as f:
    weights = pickle.load(f)
#%%
np.random.seed(seed)

data_augmentation = keras.Sequential(
    [
        layers.Normalization()
    ]
)

model = keras.Sequential()
base_model = keras.applications.ResNet50V2(
        include_top=False, weights=None, input_shape=input_shape, pooling="avg"
    )

inputs = keras.Input(shape=input_shape)
model.add(inputs)
model.add(data_augmentation)
model.add(base_model)
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dense(200))
model.add(Activation('relu'))
model.add(
            Dense(
                    num_classes,
                    activation='softmax'
                )
        )

model.build()

#%%
model.layers[0].set_weights(weights[1][:3])
model.layers[0].trainable = False

model.layers[1].set_weights(weights[1][3:])
model.layers[1].trainable = False

model.layers[2].set_weights(weights[2])
model.layers[2].trainable = False
#%%
# Load the CIFAR10 data.
(x_train, y_train), (x_test, y_test) = cifar10.load_data()
y_train = y_train.ravel()
y_test = y_test.ravel()
# Input image dimensions.
input_shape = x_train.shape

# Normalize data.
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
ood_set = ood_set.astype('float32')

model.summary()

#%%
iteration = int(5e4//batchsize)
#optimizer = tf.optimizers.Adam(3e-3) 
lr = 3e-3
ood_batch_size = int(ood_set.shape[0]//iteration)
#y_train_one_hot = tf.one_hot(y_train, depth=num_classes)
#model.fit(x_train, y_train_one_hot,
#                    batch_size=40,
#                    epochs=epochs,
 #                   shuffle=True)
for i in range(1,epochs+1):
    if i > .8*epochs:
        lr *= 0.5e-3
    elif i > .6*epochs:
        lr *= 1e-3
    elif i > .4*epochs:
        lr *= 1e-2
    elif i > .2*epochs:
        lr *= 1e-1

    optimizer = tf.optimizers.Adam(lr) 
    perm = np.arange(batchsize*iteration).astype(int)
    perm_ood = np.arange(ood_batch_size*iteration).astype(int)
    
    np.random.shuffle(perm)
    np.random.shuffle(perm_ood)
    perm = perm.reshape(-1,batchsize)
    perm_ood = perm_ood.reshape(-1,ood_batch_size)

    for j in tqdm(range(iteration)):
        x_train_ = x_train[perm[j]]
        y_train_ = tf.one_hot(y_train[perm[j]], depth=num_classes)
        X_ood = ood_set[perm_ood[j]]
        
        with tf.GradientTape() as tape:
            logits = model(x_train_, training=True)
            logits_ood = model(X_ood)
            loss_main = cross_ent(logits, y_train_)
            loss_ood = max_conf(logits_ood)
            loss = loss_main + 0.5*loss_ood
            grads = tape.gradient(loss, model.trainable_weights)
            #print(loss)
            optimizer.apply_gradients(zip(grads, model.trainable_weights))

    train_err = np.mean(logits.numpy().argmax(1) != y_train_.numpy().argmax(1))
    test_logits = model(x_test)
    test_err = np.mean(test_logits.numpy().argmax(1) != y_test)

    print("Epoch {:03d}: loss_main={:.3f} loss_ood={:.3f} train err={:.2%} test err={:.2%}".format(i, loss_main, loss_ood, train_err, test_err))

model.save('resnet20_models/cifar10_OE_'+str(seed))
# %%
