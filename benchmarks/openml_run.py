#%%
from kdg import kdf
from kdg.utils import get_ece
import openml
from joblib import Parallel, delayed
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier as rf
from sklearn.metrics import cohen_kappa_score
from kdg.utils import get_ece
import os
from os import listdir, getcwd 
# %%
def experiment(dataset_id, folder, n_estimators=500, test_sample=1000, reps=40):
    #print(dataset_id)
    dataset = openml.datasets.get_dataset(dataset_id)
    X, y, is_categorical, _ = dataset.get_data(
                dataset_format="array", target=dataset.default_target_attribute
            )

    if np.mean(is_categorical) >0:
        return

    if np.isnan(np.sum(y)):
        return

    if np.isnan(np.sum(X)):
        return

    for ii in range(X.shape[1]):
        unique_val = np.unique(X[:,ii])

        if len(unique_val) < 10:
            return

            
    total_sample = X.shape[0]
    indx = list(
        range(
            total_sample
            )
    )
    train_samples = np.logspace(
            np.log10(2),
            np.log10(total_sample-test_sample),
            num=10,
            endpoint=True,
            dtype=int
        )
    
    err = []
    err_rf = []
    ece = []
    ece_rf = []
    kappa = []
    kappa_rf = []
    mc_rep = []
    samples = []

    for train_sample in train_samples:
        for rep in range(reps):
            np.random.shuffle(indx)
            indx_to_take_train = indx[:train_sample]
            indx_to_take_test = indx[-test_sample:]
            model_kdf = kdf(k=1e300, kwargs={'n_estimators':n_estimators})
            model_kdf.fit(X[indx_to_take_train], y[indx_to_take_train])
            proba_kdf = model_kdf.predict_proba(X[indx_to_take_test])
            proba_rf = model_kdf.rf_model.predict_proba(X[indx_to_take_test])
            predicted_label_kdf = np.argmax(proba_kdf, axis = 1)
            predicted_label_rf = np.argmax(proba_rf, axis = 1)

            err.append(
                1 - np.mean(
                        predicted_label_kdf==y[indx_to_take_test]
                    )
            )
            err_rf.append(
                1 - np.mean(
                    predicted_label_rf==y[indx_to_take_test]
                )
            )
            kappa.append(
                cohen_kappa_score(predicted_label_kdf, y[indx_to_take_test])
            )
            kappa_rf.append(
                cohen_kappa_score(predicted_label_rf, y[indx_to_take_test])
            )
            ece.append(
                get_ece(proba_kdf, predicted_label_kdf, y[indx_to_take_test])
            )
            ece_rf.append(
                get_ece(proba_rf, predicted_label_rf, y[indx_to_take_test])
            )
            samples.append(
                train_sample
            )
            mc_rep.append(rep)

    df = pd.DataFrame() 
    df['err_kdf'] = err
    df['err_rf'] = err_rf
    df['kappa_kdf'] = kappa
    df['kappa_rf'] = kappa_rf
    df['ece_kdf'] = ece
    df['ece_rf'] = ece_rf
    df['rep'] = mc_rep
    df['samples'] = samples

    df.to_csv(folder+'/'+'openML_cc18_'+str(dataset_id)+'.csv')



def experiment_rf(dataset_id, folder, n_estimators=100, reps=30):
    dataset = openml.datasets.get_dataset(dataset_id)
    X, y, is_categorical, _ = dataset.get_data(
                dataset_format="array", target=dataset.default_target_attribute
            )

    if np.mean(is_categorical) >0:
        return

    if np.isnan(np.sum(y)):
        return

    if np.isnan(np.sum(X)):
        return

    total_sample = X.shape[0]
    unique_classes, counts = np.unique(y, return_counts=True)

    test_sample = min(counts)//3

    indx = []
    for label in unique_classes:
        indx.append(
            np.where(
                y==label
            )[0]
        )

    max_sample = min(counts) - test_sample
    train_samples = np.logspace(
        np.log10(2),
        np.log10(max_sample),
        num=10,
        endpoint=True,
        dtype=int
        )
    
    err = []
    err_rf = []
    ece = []
    ece_rf = []
    kappa = []
    kappa_rf = []
    mc_rep = []
    samples = []

    for train_sample in train_samples:
        
        for rep in range(reps):
            indx_to_take_train = []
            indx_to_take_test = []

            for ii, _ in enumerate(unique_classes):
                np.random.shuffle(indx[ii])
                indx_to_take_train.extend(
                    list(
                            indx[ii][:train_sample]
                    )
                )
                indx_to_take_test.extend(
                    list(
                            indx[ii][-test_sample:counts[ii]]
                    )
                )
            model_rf = rf(n_estimators=n_estimators)
            model_rf.fit(X[indx_to_take_train], y[indx_to_take_train])
            proba_rf = model_rf.predict_proba(X[indx_to_take_test])
            predicted_label_rf = np.argmax(proba_rf, axis = 1)

            err_rf.append(
                1 - np.mean(
                    predicted_label_rf==y[indx_to_take_test]
                )
            )
            ece_rf.append(
                get_ece(proba_rf, predicted_label_rf, y[indx_to_take_test])
            )
            samples.append(
                train_sample*len(unique_classes)
            )
            mc_rep.append(rep)

    df = pd.DataFrame() 
    df['err_rf'] = err_rf
    df['ece_rf'] = ece_rf
    df['rep'] = mc_rep
    df['samples'] = samples

    df.to_csv(folder+'/'+'openML_cc18_rf_'+str(dataset_id)+'.csv')

#%%
folder = 'openml_res'
folder_rf = 'openml_res_rf'
os.mkdir(folder)
#os.mkdir(folder_rf)
benchmark_suite = openml.study.get_suite('OpenML-CC18')
#current_dir = getcwd()
#files = listdir(current_dir+'/'+folder)
Parallel(n_jobs=-1,verbose=1)(
        delayed(experiment)(
                dataset_id,
                folder
                ) for dataset_id in openml.study.get_suite("OpenML-CC18").data
            )

'''Parallel(n_jobs=-1,verbose=1)(
        delayed(experiment_rf)(
                dataset_id,
                folder_rf
                ) for dataset_id in openml.study.get_suite("OpenML-CC18").data
            )'''
'''for task_id in benchmark_suite.tasks:
    filename = 'openML_cc18_' + str(task_id) + '.csv'

    if filename not in files:
        print(filename)
        try:
            experiment(task_id,folder)
        except:
            print("couldn't run!")
        else:
            print("Ran successfully!")'''
# %%
