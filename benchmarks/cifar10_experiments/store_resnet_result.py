# %%
import pickle
import numpy as np
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Flatten, Conv2D, MaxPooling2D, BatchNormalization
from keras.models import Model
from kdg import kdf, kdn
from tensorflow.keras.datasets import cifar10, cifar100
import timeit
from scipy.io import loadmat
import random
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
from vit_keras import vit, utils
#%%
image_size = 256 #size after resizing image
input_shape = (32, 32, 3) #Cifar10 image size
num_classes = 10

#%%
def fpr_at_95_tpr(conf_in, conf_out):
    TPR = 95
    PERC = np.percentile(conf_in, 100-TPR)
    #FP = np.sum(conf_out >=  PERC)
    FPR = np.sum(conf_out >=  PERC)/len(conf_out)
    return FPR, PERC
#%%
# Load the CIFAR10 and CIFAR100 data.
(x_train, y_train), (x_test, y_test) = cifar10.load_data()
(_, _), (x_cifar100, y_cifar100) = cifar100.load_data()
x_noise = np.random.random_integers(0,high=255,size=(1000,32,32,3)).astype('float')/255.0
#x_svhn = loadmat('/Users/jayantadey/DF-CNN/data_five/SVHN/test_32x32.mat')['X']
#y_svhn = loadmat('/Users/jayantadey/DF-CNN/data_five/SVHN/test_32x32.mat')['y']
x_svhn = loadmat('/cis/home/jdey4/test_32x32.mat')['X']
#y_svhn = loadmat('/cis/home/jdey4/train_32x32.mat')['y']
#test_ids =  random.sample(range(0, x_svhn.shape[3]), 2000)
x_svhn = x_svhn.astype('float32')
x_tmp = np.zeros((x_svhn.shape[3],32,32,3), dtype=float)

for ii in range(x_svhn.shape[3]):
    x_tmp[ii,:,:,:] = x_svhn[:,:,:,ii]

x_svhn = x_tmp
del x_tmp

# Input image dimensions.
input_shape = x_train.shape[1:]

# Normalize data.
x_train = x_train.astype('float32')/255.0 
x_test = x_test.astype('float32')/255.0 
x_cifar100 = x_cifar100.astype('float32') /255.0
x_svhn = x_svhn.astype('float32')/255.0 

#%% Load model file
seeds = [0, 1, 2, 3]

for seed in seeds: 
    print('doing seed ',seed)
    acet = keras.models.load_model('ACET_vit_'+str(seed))
    #filename =  '/Users/jayantadey/kdg/benchmarks/cifar10_experiments/results/vit_kdn/kdn_cifar10_vit_'+str(seed)+'.joblib'
    #model_kdn = joblib.load(filename)
    #acet = keras.models.load_model('resnet20_models/cifar100_ACET_'+str(seed))

    '''model_kdn.global_bias = -4e8

    proba_in = model_kdn.predict_proba(x_test, distance='Geodesic', n_jobs=50)

    model_kdn.global_bias = -1e7
    proba_cifar100 = model_kdn.predict_proba(x_cifar100, distance='Geodesic')
    proba_svhn = model_kdn.predict_proba(x_svhn, distance='Geodesic', n_jobs=20)
    proba_noise = model_kdn.predict_proba(x_noise, distance='Geodesic', n_jobs=20)

    proba_in_dn = model_kdn.network.predict(x_test)
    proba_cifar100_dn = model_kdn.network.predict(x_cifar100)
    proba_svhn_dn = model_kdn.network.predict(x_svhn)
    proba_noise_dn = model_kdn.network.predict(x_noise)'''


    proba_in_acet = acet.predict(x_test)
    proba_cifar100_acet = acet.predict(x_cifar100)
    proba_svhn_acet = acet.predict(x_svhn)
    proba_noise_acet = acet.predict(x_noise)

    #summary = (proba_in, proba_in_dn, proba_in_acet)
    summary = (proba_in_acet, proba_cifar100_acet, proba_svhn_acet, proba_noise_acet)
    #summary = (proba_in, proba_cifar100, proba_svhn, proba_noise, proba_in_dn, proba_cifar100_dn, proba_svhn_dn, proba_noise_dn)#, proba_in_acet, proba_cifar100_acet, proba_svhn_acet, proba_noise_acet)
    #file_to_save = '/Users/jayantadey/kdg/benchmarks/cifar10_experiments/vit_kdn_'+str(seed)+'.pickle'
    file_to_save = 'vit_acet_'+str(seed)+'.pickle'

    with open(file_to_save, 'wb') as f:
        pickle.dump(summary, f)
