#%%
from kdg import kdf
from kdg.utils import get_ece, get_ace
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os 
import numpy as np
import openml
from sklearn.metrics import cohen_kappa_score
from kdg.utils import get_ece
from sklearn.model_selection import train_test_split
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier as rf 
from sklearn.calibration import CalibratedClassifierCV as calcv

# %%
root_dir = "openml_kdf_res"

try:
    os.mkdir(root_dir)
except:
    print("directory already exists!!!")
# %%
def experiment(dataset_id, n_estimators=500, reps=10, random_state=42):
    filename = 'Dataset_' + str(dataset_id) + '.csv'
    if os.path.exists(os.path.join(root_dir, filename)):
        return
    
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
    
    min_val = np.min(X,axis=0)
    max_val = np.max(X, axis=0)
    
    X = (X-min_val)/(max_val-min_val+1e-12)
    _, y = np.unique(y, return_inverse=True)
    '''for ii in range(X.shape[1]):
        unique_val = np.unique(X[:,ii])
        if len(unique_val) < 10:
            return'''
        
    total_sample = 10000 if X.shape[0]>10000 else X.shape[0]
    test_sample = total_sample//3 if total_sample//3 < 1000 else 1000
    train_samples = np.logspace(
            np.log10(100),
            np.log10(total_sample-test_sample),
            num=3,
            endpoint=True,
            dtype=int
        )
    err = []
    err_geod = []
    err_rf = []
    ece = []
    ece_geod = []
    ece_rf = []
    err_isotonic = []
    ece_isotonic = []
    err_sigmoid = []
    ece_sigmoid = []
    mc_rep = []
    samples = []

    for train_sample in train_samples:
        for rep in range(reps):
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_sample, train_size=train_sample, random_state=random_state+rep, stratify=y)

            if train_sample >= 200:
                X_train, X_cal, y_train, y_cal = train_test_split(
                    X_train, y_train, train_size=0.9, random_state=random_state+rep, stratify=y_train)
            else:
                X_train, X_cal, y_train, y_cal = train_test_split(
                    X_train, y_train, train_size=0.5, random_state=random_state+rep, stratify=y_train)
            
            ################
            uncalibrated_model = rf(n_estimators=n_estimators)
            uncalibrated_model.fit(X_train, y_train)
            model_kdf = kdf(rf_model=uncalibrated_model)
            model_kdf.fit(X_train, y_train, X_cal, y_cal)
            proba_kdf = model_kdf.predict_proba(X_test)
            proba_kdf_geod = model_kdf.predict_proba(X_test, distance='Geodesic')
            proba_rf = model_kdf.rf_model.predict_proba(X_test)
            predicted_label_kdf = np.argmax(proba_kdf, axis = 1)
            predicted_label_kdf_geod = np.argmax(proba_kdf_geod, axis = 1)
            predicted_label_rf = np.argmax(proba_rf, axis = 1)

            err.append(
                1 - np.mean(
                        predicted_label_kdf==y_test
                    )
            )
            err_geod.append(
                1 - np.mean(
                        predicted_label_kdf_geod==y_test
                    )
            )
            err_rf.append(
                1 - np.mean(
                    predicted_label_rf==y_test
                )
            )
            ece.append(
                get_ece(proba_kdf, y_test)
            )
            ece_geod.append(
                get_ece(proba_kdf_geod, y_test)
            )
            ece_rf.append(
                get_ece(proba_rf, y_test)
            )
            samples.append(
                train_sample
            )
            mc_rep.append(rep)

            ### train baseline ###
            
            calibrated_rf_isotonic = calcv(
                uncalibrated_model, method='isotonic', ensemble=False, cv='prefit')
            calibrated_rf_isotonic.fit(X_cal, y_cal)

            calibrated_rf_sigmoid = calcv(
                uncalibrated_model, method='sigmoid', ensemble=False, cv='prefit')
            calibrated_rf_sigmoid.fit(X_cal, y_cal)

            y_proba_isotonic = calibrated_rf_isotonic.predict_proba(X_test)
            y_hat_isotonic = np.argmax(y_proba_isotonic, axis=1)

            y_proba_sigmoid = calibrated_rf_sigmoid.predict_proba(X_test)
            y_hat_sigmoid = np.argmax(y_proba_sigmoid, axis=1)

            err_isotonic.append(
                1 - np.mean(
                    y_hat_isotonic == y_test
                )
            )
            ece_isotonic.append(
                get_ece(y_proba_isotonic, y_test)
            )
            err_sigmoid.append(
                1 - np.mean(
                    y_hat_sigmoid == y_test
                )
            )
            ece_sigmoid.append(
                get_ece(y_proba_sigmoid, y_test)
            )

    df = pd.DataFrame() 
    df['err_kdf'] = err
    df['err_kdf_geod'] = err_geod
    df['err_rf'] = err_rf
    df['ece_kdf'] = ece
    df['ece_kdf_geod'] = ece_geod
    df['ece_rf'] = ece_rf
    df['err_isotonic'] = err_isotonic
    df['ece_isotonic'] = ece_isotonic
    df['err_sigmoid'] = err_sigmoid
    df['ece_sigmoid'] = ece_sigmoid
    df['rep'] = mc_rep
    df['samples'] = samples

    filename = 'Dataset_' + str(dataset_id) + '.csv'
    df.to_csv(os.path.join(root_dir, filename))

# %%
benchmark_suite = openml.study.get_suite('OpenML-CC18')
#data_id_not_done = [28, 554, 1485, 40996, 41027, 23517, 40923, 40927]

Parallel(n_jobs=-1,verbose=1)(
        delayed(experiment)(
                dataset_id,
                ) for dataset_id in benchmark_suite.data
            )

