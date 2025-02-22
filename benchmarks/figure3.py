#%%
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os 
import numpy as np
import openml
from scipy.interpolate import interp1d

# %%
res_folder_kdn = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdn_res'
res_folder_kdn_baseline_ood = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdn_res_baseline_ood'
res_folder_kdf = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdf_res'
res_folder_kdf_baseline_ood = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdf_res_baseline_ood'
res_folder_kdn_ood = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdn_res_ood'
res_folder_kdf_ood = '/Users/jayantadey/kdg/benchmarks/openml_res/openml_kdf_res_ood'
files = os.listdir(res_folder_kdf)
#files.remove('.DS_Store')

#%%
def smooth_curve(data, w=5):
    smoothed_data = []
    buffer = []
    for point in data:
        if len(buffer) > w:
            buffer.pop(0)
        buffer.append(point)
        smoothed_data.append(np.mean(buffer))

    return smoothed_data

#%%
def plot_summary_ood(files, folder, baseline_folder, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=None, ax=None):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 8), sharey=True, sharex=True, constrained_layout=True)

    r = np.arange(0,5,.5)
    r[1:] += .5

    if parent == 'dn':
        parent_ = 'nn'
    else:
        parent_ = parent

    err_diff_ = []
    err_diff_isotonic = []
    err_diff_sigmoid = []  
    for file in files:
        if os.path.exists(folder+'/'+file):
            df = pd.read_csv(folder+'/'+file)
            df_baseline = pd.read_csv(baseline_folder+'/'+file)
            #print(file)
            data_id = file[:-4]
            data_id = int(data_id[8:])

            dataset = openml.datasets.get_dataset(data_id)
            X, y, is_categorical, _ = dataset.get_data(
                dataset_format="array", target=dataset.default_target_attribute
            )
            _, counts = np.unique(y, return_counts=True)
            mean_max_ood = np.max(counts)/np.sum(counts)
            #print(mean_max_ood)
            err_kdx_med = []
            err_isotonic_med =[]
            err_sigmoid_med = []
            err_x_med = []

            for dist in r:
                kdx = np.abs(df['conf_'+model][df['distance']==dist] - mean_max_ood)
                x = np.abs(df['conf_'+parent][df['distance']==dist] - mean_max_ood)
                isotonic = np.abs(df_baseline['conf_'+parent_+'_isotonic'][df_baseline['distance']==dist] - mean_max_ood)
                #print('error here')
                sigmoid = np.abs(df_baseline['conf_'+parent_+'_sigmoid'][df_baseline['distance']==dist] - mean_max_ood)

                err_kdx_med.append(
                    np.mean(kdx)
                )

                err_x_med.append(
                    np.mean(x)
                )
                err_isotonic_med.append(
                    np.mean(isotonic)
                )
                err_sigmoid_med.append(
                    np.mean(sigmoid)
                )
            
            err_diff_.append(
                np.array(err_x_med) - np.array(err_kdx_med)
            )
            err_diff_isotonic.append(
                np.array(err_x_med) - np.array(err_isotonic_med)
            )
            err_diff_sigmoid.append(
                np.array(err_x_med) - np.array(err_sigmoid_med)
            )

    final_err = []
    final_err_isotonic = []
    final_err_sigmoid = []
    for ii in range(len(err_diff_)):
        final_err.append(err_diff_[ii][-1])
        final_err_isotonic.append(err_diff_isotonic[ii][-1])
        final_err_sigmoid.append(err_diff_sigmoid[ii][-1])

    qunatiles = np.nanquantile(np.array(err_diff_),[.25,.75],axis=0)
    qunatiles_isotone = np.nanquantile(np.array(err_diff_isotonic),[.25,.75],axis=0)
    qunatiles_sigmoid = np.nanquantile(np.array(err_diff_sigmoid),[.25,.75],axis=0)
    ax.plot(r[1:], np.nanmedian(np.array(err_diff_), axis=0)[1:], linewidth=4, c=color[0], linestyle=linestyle[0])
    ax.fill_between(r[1:], qunatiles[0][1:], qunatiles[1][1:], facecolor=color[0], alpha=.1)

    ax.plot(r[1:], np.nanmedian(np.array(err_diff_isotonic), axis=0)[1:], linewidth=3, c=color[1], linestyle=linestyle[1])
    ax.fill_between(r[1:], qunatiles_isotone[0][1:], qunatiles_isotone[1][1:], facecolor=color[1], alpha=.1)

    ax.plot(r[1:], np.nanmedian(np.array(err_diff_sigmoid), axis=0)[1:], linewidth=3, c=color[2], linestyle=linestyle[2])
    ax.fill_between(r[1:], qunatiles_sigmoid[0][1:], qunatiles_sigmoid[1][1:], facecolor=color[2], alpha=.1)

    return final_err, final_err_isotonic, final_err_sigmoid

def plot_summary_error(files, folder, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=None, ax=None):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 8), sharey=True, sharex=True, constrained_layout=True)

    sample_combined = []
    for file in files:
        #print(file)
        df = pd.read_csv(folder+'/'+file)
        sample_combined.extend(np.unique(df['samples']))
        #print(np.unique(df['samples']))
    sample_combined = np.unique(
            sample_combined
        )
    
    err_diff_ = []
    err_diff_isotonic_ = []
    err_diff_sigmoid_ = []

    for file in files:
        df = pd.read_csv(folder+'/'+file)
        #df_baseline = pd.read_csv(baseline_folder+'/'+file)
        samples = np.unique(df['samples'])
        err_kdx_med = []
        err_x_med = []
        err_isotonic_med = []
        err_sigmoid_med = []
        
        for sample in samples:
            kdx = df['err_'+model][df['samples']==sample]
            x = df['err_'+parent][df['samples']==sample]
            isotonic = df['err_isotonic'][df['samples']==sample]
            sigmoid = df['err_sigmoid'][df['samples']==sample]

            err_kdx_med.append(
                np.mean(kdx)
            )

            err_x_med.append(
                np.mean(x)
            )
            
            err_isotonic_med.append(
                np.mean(isotonic)
            )

            err_sigmoid_med.append(
                np.mean(sigmoid)
            )

        err_diff = (np.array(err_x_med) - np.array(err_kdx_med))/(np.array(err_x_med))
        err_diff_isotonic = (np.array(err_x_med) - np.array(err_isotonic_med))/(np.array(err_x_med))
        err_diff_sigmoid = (np.array(err_x_med) - np.array(err_sigmoid_med))/(np.array(err_x_med))

        idx = np.where(sample_combined<=samples[-1])[0]
        f = interp1d(samples, err_diff, kind='linear')
        f_isotonic = interp1d(samples, err_diff_isotonic, kind='linear')
        f_sigmoid = interp1d(samples, err_diff_sigmoid, kind='linear')

        tmp_diff = list(f(sample_combined[idx]))
        tmp_diff.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_.append(
            tmp_diff
        )
        
        tmp_diff_isotonic = list(f_isotonic(sample_combined[idx]))
        tmp_diff_isotonic.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_isotonic_.append(
            tmp_diff_isotonic
        )

        tmp_diff_sigmoid = list(f_sigmoid(sample_combined[idx]))
        tmp_diff_sigmoid.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_sigmoid_.append(
            tmp_diff_sigmoid
        )
        #print(err_diff_isotonic_,'\n', parent)
       # ax.plot(samples, err_diff, linewidth=4, c='r', alpha=.1)
    final_err = []
    final_err_isotonic = []
    final_err_sigmoid = []
    for ii in range(len(err_diff_)):
        final_err.append(err_diff_[ii][-1])
        final_err_isotonic.append(err_diff_isotonic_[ii][-1])
        final_err_sigmoid.append(err_diff_sigmoid_[ii][-1])

    qunatiles = np.nanquantile(np.array(err_diff_),[.25,.75],axis=0)
    qunatiles_isotonic = np.nanquantile(np.array(err_diff_isotonic_),[.25,.75],axis=0)
    qunatiles_sigmoid = np.nanquantile(np.array(err_diff_sigmoid_),[.25,.75],axis=0)

    print(smooth_curve(np.nanmedian(np.array(err_diff_isotonic_), axis=0)))
    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_isotonic_), axis=0)), linewidth=3, c=color[1], linestyle=linestyle[1], label='Isotonic')    
    ax.fill_between(sample_combined, smooth_curve(qunatiles_isotonic[0]), smooth_curve(qunatiles_isotonic[1]), facecolor=color[1], alpha=.1)
    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_sigmoid_), axis=0)), linewidth=3, c=color[2], linestyle=linestyle[2], label='Sigmoid')    
    ax.fill_between(sample_combined, smooth_curve(qunatiles_sigmoid[0]), smooth_curve(qunatiles_sigmoid[1]), facecolor=color[2], alpha=.1)
    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_), axis=0)), linewidth=4, c=color[0], linestyle=linestyle[0], label=model[:3].upper())    

    ax.fill_between(sample_combined, smooth_curve(qunatiles[0]), smooth_curve(qunatiles[1]), facecolor=color[0], alpha=.2)

    return final_err, final_err_isotonic, final_err_sigmoid


def plot_summary_ece(files, folder, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=None, ax=None):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 8), sharey=True, sharex=True, constrained_layout=True)

    sample_combined = []
    for file in files:
        df = pd.read_csv(folder+'/'+file)
        sample_combined.extend(np.unique(df['samples']))

    sample_combined = np.unique(
            sample_combined
        )
    
    err_diff_ = []
    err_diff_isotonic_ = []
    err_diff_sigmoid_ = []
    for file in files:
        #print(file)
        df = pd.read_csv(folder+'/'+file)
        #df_baseline = pd.read_csv(baseline_folder+'/'+file)
        samples = np.unique(df['samples'])
        err_kdx_med = []
        err_x_med = []
        err_isotonic_med = []
        err_sigmoid_med = []
        
        
        for sample in samples:
            kdx = df['ece_'+model][df['samples']==sample]
            x = df['ece_'+parent][df['samples']==sample]
            isotonic = df['ece_isotonic'][df['samples']==sample]
            sigmoid = df['ece_sigmoid'][df['samples']==sample]

            err_kdx_med.append(
                np.mean(kdx)
            )

            err_x_med.append(
                np.mean(x)
            )

            err_isotonic_med.append(
                np.mean(isotonic)
            )

            err_sigmoid_med.append(
                np.mean(sigmoid)
            )

        err_diff = (np.array(err_x_med) - np.array(err_kdx_med))/(np.array(err_x_med))
        err_diff_isotonic = (np.array(err_x_med) - np.array(err_isotonic_med))/(np.array(err_x_med))
        err_diff_sigmoid = (np.array(err_x_med) - np.array(err_sigmoid_med))/(np.array(err_x_med))

        idx = np.where(sample_combined<=samples[-1])[0]
        f = interp1d(samples, err_diff, kind='linear')
        f_isotonic = interp1d(samples, err_diff_isotonic, kind='linear')
        f_sigmoid = interp1d(samples, err_diff_sigmoid, kind='linear')

        tmp_diff = list(f(sample_combined[idx]))
        tmp_diff.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_.append(
            tmp_diff
        )
        
        tmp_diff_isotonic = list(f_isotonic(sample_combined[idx]))
        tmp_diff_isotonic.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_isotonic_.append(
            tmp_diff_isotonic
        )

        tmp_diff_sigmoid = list(f_sigmoid(sample_combined[idx]))
        tmp_diff_sigmoid.extend((len(sample_combined)-len(idx))*[np.nan])
        err_diff_sigmoid_.append(
            tmp_diff_sigmoid
        )
        #ax.plot(samples, err_diff, linewidth=4, c='r', alpha=.1)
    final_err = []
    final_err_isotonic = []
    final_err_sigmoid = []
    for ii in range(len(err_diff_)):
        final_err.append(err_diff_[ii][-1])
        final_err_isotonic.append(err_diff_isotonic_[ii][-1])
        final_err_sigmoid.append(err_diff_sigmoid_[ii][-1])

    qunatiles = np.nanquantile(np.array(err_diff_),[.25,.75],axis=0)
    qunatiles_isotonic = np.nanquantile(np.array(err_diff_isotonic_),[.25,.75],axis=0)
    qunatiles_sigmoid = np.nanquantile(np.array(err_diff_sigmoid_),[.25,.75],axis=0)

    
    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_isotonic_), axis=0)), linewidth=3, linestyle=linestyle[1], c=color[1])    
    ax.fill_between(sample_combined, smooth_curve(qunatiles_isotonic[0]), smooth_curve(qunatiles_isotonic[1]), facecolor=color[1], alpha=.1)
    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_sigmoid_), axis=0)), linewidth=3, linestyle=linestyle[2], c=color[2])    
    ax.fill_between(sample_combined, smooth_curve(qunatiles_sigmoid[0]), smooth_curve(qunatiles_sigmoid[1]), facecolor=color[2], alpha=.1)

    ax.plot(sample_combined, smooth_curve(np.nanmedian(np.array(err_diff_), axis=0)), linewidth=4, linestyle=linestyle[0], c=color[0])    

    ax.fill_between(sample_combined, smooth_curve(qunatiles[0]), smooth_curve(qunatiles[1]), facecolor=color[0], alpha=.1)

    return final_err, final_err_isotonic, final_err_sigmoid

#%%
linestyles = ['-', '--', '-.']

sns.set(
    color_codes=True, palette="bright", style="white", context="talk", font_scale=1.5
)

fig, ax = plt.subplots(2, 3, figsize=(21,15))

err_kdf, err_iso_rf, err_sig_rf = plot_summary_error(files, res_folder_kdf, color=['r','chocolate','purple'], model='kdf_geod', linestyle=linestyles, ax=ax[0][0])
#plot_summary_error(files, res_folder_kdf, res_folder_kdf_baseline, linestyle='dashed', ax=ax[0][0])
ece_kdf, ece_iso_rf, ece_sig_rf = plot_summary_ece(files, res_folder_kdf, color=['r','chocolate','purple'], model='kdf_geod', linestyle=linestyles, ax=ax[0][1])
#plot_summary_ece(files, res_folder_kdf, res_folder_kdf_baseline, linestyle='dashed', ax=ax[0][1])
err_kdn, err_iso_nn, err_sig_nn = plot_summary_error(files, res_folder_kdn, color=['b','seagreen','magenta'], model='kdn_geod', parent='dn', linestyle=linestyles, ax=ax[1][0])
#plot_summary_error(files, res_folder_kdn, res_folder_kdf_baseline, color=['b','#8E388E','k'], model='kdn', parent='dn', linestyle='dashed', ax=ax[1][0])
ece_kdn, ece_iso_nn, ece_sig_nn =  plot_summary_ece(files, res_folder_kdn, color=['b','seagreen','magenta'], model='kdn_geod', parent='dn', linestyle=linestyles, ax=ax[1][1])
#plot_summary_ece(files, res_folder_kdn, res_folder_kdn_baseline, color=['b','#8E388E','k'], model='kdn', parent='dn', linestyle='dashed', ax=ax[1][1])
oce_kdf, oce_iso_rf, oce_sig_rf = plot_summary_ood(files, res_folder_kdf_ood, res_folder_kdf_baseline_ood, color=['r','chocolate','purple'], linestyle=linestyles, ax=ax[0][2])
oce_kdn, oce_iso_nn, oce_sig_nn = plot_summary_ood(files, res_folder_kdn_ood, res_folder_kdn_baseline_ood, model='kdn', parent='dn', color=['b','seagreen','magenta'], linestyle=linestyles, ax=ax[1][2])


ax[1][1].plot(0,0,c='r',linewidth=4, label='KDF')
ax[1][1].plot(0,0,c='chocolate',linewidth=3, linestyle='--', label='Isotonic RF')
ax[1][1].plot(0,0,c='purple',linewidth=3, linestyle='-.', label='Sigmoid RF')
ax[1][1].plot(0,0,c='k',linewidth=3, linestyle='--', label='Parent RF')

handles, labels = ax[1][1].get_legend_handles_labels()
fig.legend(handles, labels, ncol=1, loc="upper right", bbox_to_anchor=(1.2,.8), fontsize=30, frameon=False)

ax[0][1].plot(0,0,c='b',linewidth=4, label='KDN')
ax[0][1].plot(0,0,c='seagreen',linewidth=3, linestyle='--', label='Isotonic DN')
ax[0][1].plot(0,0,c='magenta',linewidth=3, linestyle='-.', label='Sigmoid DN')
ax[0][1].plot(0,0,c='k',linewidth=3, linestyle='--', label='Parent DN')


handles, labels = ax[0][1].get_legend_handles_labels()
fig.legend(handles, labels, ncol=1, loc="upper right", bbox_to_anchor=(1.2,.4), fontsize=30, frameon=False)
#     
ax[1][0].set_xlim([100, 10000])
ax[1][1].set_xlim([100, 10000])
ax[0][0].set_xlim([100, 10000])
ax[0][1].set_xlim([100, 10000])


#ax[0][0].set_title(r'$(P_{iso}, P_{sig}) = (0.04, 0.84)$', fontsize=30)

ax[0][0].set_xscale("log")
ax[0][0].set_ylim([-0.1, .1])
ax[0][0].set_yticks([-.10,0,.10])
ax[0][0].set_xticks([])

ax[0][0].set_ylabel('Improvement over parent', fontsize=35)
#ax[0][0].text(100, .05, 'KGF wins')
#ax[0][0].text(100, -.08, 'RF wins')

###ax[0][1].set_title('ID Calibration', fontsize=40)
#ax[0][1].set_title(r'$(P_{iso}, P_{sig})= (0.70, 0.20)$', fontsize=30)

ax[0][1].set_xscale("log")
ax[0][1].set_ylim([-.5, .8])
ax[0][1].set_yticks([-.5,0,1])
ax[0][1].set_xticks([])
ax[0][1].set_ylabel('', fontsize=35)
#ax[0][1].text(100, .3, 'KGF wins')
#ax[0][1].text(100, -.05, 'RF wins')
#ax[1][0].set_title(r'$(P_{iso}, P_{sig}) = (0.00, 0.01)$', fontsize=30)

ax[1][0].set_xscale("log")
ax[1][0].set_ylim([-0.06, .06])
ax[1][0].set_yticks([-.05,0,.05])
ax[1][0].set_ylabel('Improvement over parent', fontsize=35)
#ax[1][0].text(100, .05, 'KGN wins')
#ax[1][0].text(100, -.08, 'DN wins')

#ax[1][1].set_title(r'$(P_{iso}, P_{sig}) = (0.38, 0.34)$', fontsize=30)

ax[1][1].set_xscale("log")
ax[1][1].set_ylim([-.2, 1])
ax[1][1].set_yticks([-.2,0,1])
ax[1][1].set_ylabel('', fontsize=35)
#ax[1][1].text(100, .05, 'KGN wins')
#ax[1][1].text(100, -.08, 'DN wins')

ax[0][2].set_ylim([-0.25, .25])
ax[0][2].set_yticks([-.2,0,.2])
ax[0][2].set_xticks([])
#ax[0][2].set_title(r'$(P_{iso}, P_{sig}) = (0.00, 0.00)$', fontsize=30)
#ax[2][0].set_ylabel('Difference', fontsize=35)
#ax[0][2].text(2, .05, 'KGF wins')
#ax[0][2].text(2, -.08, 'RF wins')
ax[0][2].set_xlim([1, 5])
#ax[0][2].text(.25, .1, 'ID', rotation=90, fontsize=40, color='b')
#ax[0][2].text(1.5, .05, 'OOD', rotation=90, fontsize=40, color='b')
#ax[0][2].axvline(x=1, ymin=-0.2, ymax=1, color='b', linestyle='dashed',linewidth=4)

###ax[0][2].set_title('OOD Calibration', fontsize=40)

#ax[1][2].set_title(r'$(P_{iso}, P_{sig})  = (0.00, 0.00)$', fontsize=30)
ax[1][2].set_ylim([-0.2, .85])
ax[1][2].set_xlim([1, 5])
ax[1][2].set_yticks([-.2,0,.8])
ax[1][2].set_xticks([1,3,5])
#ax[2][0].set_ylabel('Difference', fontsize=35)
#ax[1][2].text(2, .3, 'KGN wins')
#ax[1][2].text(2, -.08, 'DN wins')
#ax[2][0].set_ylabel('Difference', fontsize=35)
#ax[1][2].text(.25, .5, 'ID', rotation=90, fontsize=40, color='b')
#ax[1][2].text(1.5, .4, 'OOD', rotation=90, fontsize=40, color='b')
#ax[1][2].axvline(x=1, ymin=-0.2, ymax=1, color='b', linestyle='dashed',linewidth=4)
#ax[1][2].set_xlabel('Distance')

#ax[0][0].legend()
for j in range(2):
    for i in range(2):
        ax[j][i].hlines(0, 10,1e5, colors='k', linestyles='dashed',linewidth=4)

        ax[j][i].tick_params(labelsize=30)
        right_side = ax[j][i].spines["right"]
        right_side.set_visible(False)
        top_side = ax[j][i].spines["top"]
        top_side.set_visible(False)

for i in range(2):
    ax[i][2].hlines(0, 0,5, colors='k', linestyles='dashed',linewidth=4)

    ax[i][2].tick_params(labelsize=30)
    right_side = ax[i][2].spines["right"]
    right_side.set_visible(False)
    top_side = ax[i][2].spines["top"]
    top_side.set_visible(False)

fig.text(0.43, -0.01, "Number of Training Samples (log)", ha="center", fontsize=35)
fig.text(0.83, -0.01, "Distance", ha="center", fontsize=35)

fig.text(0.22, 1, "Classification", ha="center", fontsize=50)
fig.text(0.53, 1, "ID Calibration", ha="center", fontsize=50)
fig.text(0.85, 1, "OOD Calibration", ha="center", fontsize=50)

plt.tight_layout()
plt.savefig('/Users/jayantadey/kdg/benchmarks/plots/openml_summary.pdf', bbox_inches='tight')
# %%
from scipy.stats import ranksums

a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(err_kdf[ii]):
        a.append(err_kdf[ii])
        b.append(err_iso_rf[ii])
        c.append(err_sig_rf[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %%
a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(ece_kdf[ii]):
        a.append(ece_kdf[ii])
        b.append(ece_iso_rf[ii])
        c.append(ece_sig_rf[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %%
a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(oce_kdf[ii]):
        a.append(oce_kdf[ii])
        b.append(oce_iso_rf[ii])
        c.append(oce_sig_rf[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %%
a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(err_kdn[ii]):
        a.append(err_kdn[ii])
        b.append(err_iso_nn[ii])
        c.append(err_sig_nn[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %%
a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(ece_kdn[ii]):
        a.append(ece_kdn[ii])
        b.append(ece_iso_nn[ii])
        c.append(ece_sig_nn[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %%
a =[]
b = []
c = []

for ii in range(45):
    if ~np.isnan(oce_kdn[ii]):
        a.append(oce_kdn[ii])
        b.append(oce_iso_nn[ii])
        c.append(oce_sig_nn[ii])


stat_equal_iso = ranksums(a,b,'less')
stat_greater_iso = ranksums(a,b,'greater')
stat_equal_sig = ranksums(a,c,'less')
stat_greater_sig = ranksums(a,c,'greater')

print("p value for classification error less than isotonic ", stat_equal_iso.pvalue)
print("p value for classification error greater than isotonic ", stat_greater_iso.pvalue)

print("p value for classification error less than sigmoid ", stat_equal_sig.pvalue)
print("p value for classification error greater than sigmoid ", stat_greater_sig.pvalue)

# %% Do Appendix figure

def plot_err(file, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=['-', '--', '-.'], ax=None, dataset_id=None):
    df = pd.read_csv(file)
    #df_baseline = pd.read_csv(baseline_folder+'/'+file)
    samples = np.unique(df['samples'])
    err_kdx_med = []
    err_x_med = []
    err_isotonic_med = []
    err_sigmoid_med = []

    err_kdx_25 = []
    err_x_25 = []
    err_isotonic_25 = []
    err_sigmoid_25 = []

    err_kdx_75 = []
    err_x_75 = []
    err_isotonic_75 = []
    err_sigmoid_75 = []
    
    for sample in samples:
        kdx = df['err_'+model][df['samples']==sample]
        x = df['err_'+parent][df['samples']==sample]
        isotonic = df['err_isotonic'][df['samples']==sample]
        sigmoid = df['err_sigmoid'][df['samples']==sample]

        err_kdx_med.append(
            np.median(kdx)
        )

        err_x_med.append(
            np.median(x)
        )
        
        err_isotonic_med.append(
            np.median(isotonic)
        )

        err_sigmoid_med.append(
            np.median(sigmoid)
        )

        qunatiles = np.nanquantile(np.array(kdx),[.25,.75],axis=0)
        err_kdx_25.append(
            qunatiles[0]
        )
        err_kdx_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(x),[.25,.75],axis=0)
        err_x_25.append(
            qunatiles[0]
        )
        err_x_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(isotonic),[.25,.75],axis=0)
        err_isotonic_25.append(
            qunatiles[0]
        )
        err_isotonic_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(sigmoid),[.25,.75],axis=0)
        err_sigmoid_25.append(
            qunatiles[0]
        )
        err_sigmoid_75.append(
            qunatiles[1]
        )

    ax.plot(samples, err_kdx_med, linewidth=4, c=color[0], linestyle=linestyle[0], label=model[:3].upper())    
    ax.fill_between(samples, err_kdx_25, err_kdx_75, facecolor=color[0], alpha=.1)
    ax.plot(samples, err_isotonic_med, linewidth=3, c=color[1], linestyle=linestyle[1], label='Isotonic-'+parent.upper())    
    ax.fill_between(samples, err_isotonic_25, err_isotonic_75, facecolor=color[1], alpha=.1)
    ax.plot(samples, err_sigmoid_med, linewidth=3, c=color[2], linestyle=linestyle[2], label='Sigmoid'+parent.upper())    
    ax.fill_between(samples, err_sigmoid_25, err_sigmoid_75, facecolor=color[2], alpha=.1)
    ax.plot(samples, err_x_med, linewidth=3, c='k', label=parent.upper())    
    ax.fill_between(samples, err_x_25, err_x_75, facecolor='k', alpha=.1)

    if dataset_id != None:
        ax.set_ylabel('Dataset ID ' + str(dataset_id), fontsize=35)
    else:
        ax.set_ylabel('Error', fontsize=35)

    ax.set_xscale("log")
    ax.tick_params(labelsize=30)
    right_side = ax.spines["right"]
    right_side.set_visible(False)
    top_side = ax.spines["top"]
    top_side.set_visible(False)


def plot_ece(file, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=['-', '--', '-.'], ax=None):
    df = pd.read_csv(file)
    #df_baseline = pd.read_csv(baseline_folder+'/'+file)
    samples = np.unique(df['samples'])
    err_kdx_med = []
    err_x_med = []
    err_isotonic_med = []
    err_sigmoid_med = []

    err_kdx_25 = []
    err_x_25 = []
    err_isotonic_25 = []
    err_sigmoid_25 = []

    err_kdx_75 = []
    err_x_75 = []
    err_isotonic_75 = []
    err_sigmoid_75 = []
    
    for sample in samples:
        kdx = df['ece_'+model][df['samples']==sample]
        x = df['ece_'+parent][df['samples']==sample]
        isotonic = df['ece_isotonic'][df['samples']==sample]
        sigmoid = df['ece_sigmoid'][df['samples']==sample]

        err_kdx_med.append(
            np.median(kdx)
        )

        err_x_med.append(
            np.median(x)
        )
        
        err_isotonic_med.append(
            np.median(isotonic)
        )

        err_sigmoid_med.append(
            np.median(sigmoid)
        )

        qunatiles = np.nanquantile(np.array(kdx),[.25,.75],axis=0)
        err_kdx_25.append(
            qunatiles[0]
        )
        err_kdx_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(x),[.25,.75],axis=0)
        err_x_25.append(
            qunatiles[0]
        )
        err_x_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(isotonic),[.25,.75],axis=0)
        err_isotonic_25.append(
            qunatiles[0]
        )
        err_isotonic_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(sigmoid),[.25,.75],axis=0)
        err_sigmoid_25.append(
            qunatiles[0]
        )
        err_sigmoid_75.append(
            qunatiles[1]
        )

    ax.plot(samples, err_kdx_med, linewidth=4, c=color[0], linestyle=linestyle[0], label=model.upper())    
    ax.fill_between(samples, err_kdx_25, err_kdx_75, facecolor=color[0], alpha=.1)
    ax.plot(samples, err_isotonic_med, linewidth=3, c=color[1], linestyle=linestyle[1], label='Isotonic-'+parent.upper())    
    ax.fill_between(samples, err_isotonic_25, err_isotonic_75, facecolor=color[1], alpha=.1)
    ax.plot(samples, err_sigmoid_med, linewidth=3, c=color[2], linestyle=linestyle[2], label='Sigoid'+parent.upper())    
    ax.fill_between(samples, err_sigmoid_25, err_sigmoid_75, facecolor=color[2], alpha=.1)
    ax.plot(samples, err_x_med, linewidth=3, c='k', label=parent.upper())    
    ax.fill_between(samples, err_x_25, err_x_75, facecolor='k', alpha=.1)

    #ax.set_ylabel('MCE', fontsize=35)
    ax.set_xscale("log")
    ax.tick_params(labelsize=30)
    right_side = ax.spines["right"]
    right_side.set_visible(False)
    top_side = ax.spines["top"]
    top_side.set_visible(False)

def plot_ood(file, file_baseline, model='kdf', parent='rf', color=['r','#8E388E','k'], linestyle=['-', '--', '-.'], ax=None):
    r = np.arange(0,5,.5)
    r[1:] += .5

    if parent == 'dn':
        parent_ = 'nn'
    else:
        parent_ = parent

    df = pd.read_csv(file)
    df_baseline = pd.read_csv(file_baseline)

    err_kdx_med = []
    err_x_med = []
    err_isotonic_med = []
    err_sigmoid_med = []

    err_kdx_25 = []
    err_x_25 = []
    err_isotonic_25 = []
    err_sigmoid_25 = []

    err_kdx_75 = []
    err_x_75 = []
    err_isotonic_75 = []
    err_sigmoid_75 = []
    for dist in r:
        kdx = df['conf_'+model][df['distance']==dist]
        x = df['conf_'+parent][df['distance']==dist]
        isotonic = df_baseline['conf_'+parent_+'_isotonic'][df_baseline['distance']==dist]
        sigmoid = df_baseline['conf_'+parent_+'_sigmoid'][df_baseline['distance']==dist]

        err_kdx_med.append(
            np.median(kdx)
        )

        err_x_med.append(
            np.median(x)
        )
        
        err_isotonic_med.append(
            np.median(isotonic)
        )

        err_sigmoid_med.append(
            np.median(sigmoid)
        )

        qunatiles = np.nanquantile(np.array(kdx),[.25,.75],axis=0)
        err_kdx_25.append(
            qunatiles[0]
        )
        err_kdx_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(x),[.25,.75],axis=0)
        err_x_25.append(
            qunatiles[0]
        )
        err_x_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(isotonic),[.25,.75],axis=0)
        err_isotonic_25.append(
            qunatiles[0]
        )
        err_isotonic_75.append(
            qunatiles[1]
        )

        qunatiles = np.nanquantile(np.array(sigmoid),[.25,.75],axis=0)
        err_sigmoid_25.append(
            qunatiles[0]
        )
        err_sigmoid_75.append(
            qunatiles[1]
        )

    ax.plot(r, err_kdx_med, linewidth=4, c=color[0], linestyle=linestyle[0], label=model.upper())    
    ax.fill_between(r, err_kdx_25, err_kdx_75, facecolor=color[0], alpha=.1)
    ax.plot(r, err_isotonic_med, linewidth=3, c=color[1], linestyle=linestyle[1], label='Isotonic-'+parent.upper())    
    ax.fill_between(r, err_isotonic_25, err_isotonic_75, facecolor=color[1], alpha=.1)
    ax.plot(r, err_sigmoid_med, linewidth=3, c=color[2], linestyle=linestyle[2], label='Sigoid'+parent.upper())    
    ax.fill_between(r, err_sigmoid_25, err_sigmoid_75, facecolor=color[2], alpha=.1)
    ax.plot(r, err_x_med, linewidth=3, c='k', label=parent.upper())    
    ax.fill_between(r, err_x_25, err_x_75, facecolor='k', alpha=.1)

    #ax.set_ylabel('Mean Max Conf.', fontsize=35)
    ax.tick_params(labelsize=30)
    right_side = ax.spines["right"]
    right_side.set_visible(False)
    top_side = ax.spines["top"]
    top_side.set_visible(False)

#%%
linestyles = ['-', '--', '-.']

sns.set(
    color_codes=True, palette="bright", style="white", context="talk", font_scale=1.5
)

fig=plt.figure(figsize=(40,60))
#fig, ax = plt.subplots(12, 6, figsize=(40,60), sharex=True)

for ii, file in enumerate(files[:12]):

    data_id = file[:-4]
    data_id = int(data_id[8:])

    ax1 = plt.subplot(12,6,ii+5*ii+1, sharex=ax1 if ii!=0 else None)

    if ii==0:
        ax1.set_title('Classification Error', fontsize=40)

    plot_err(res_folder_kdf+'/'+file, model='kdf_geod',ax=ax1, dataset_id=data_id)
    
    ax2 = plt.subplot(12,6,ii+5*ii+2, sharex=ax2 if ii!=0 else None)
    plot_ece(res_folder_kdf+'/'+file, model='kdf_geod',ax=ax2)
    
    if ii==0:
        ax2.set_title('MCE', fontsize=40)

    ax3 = plt.subplot(12,6,ii+5*ii+4, sharex=ax3 if ii!=0 else None)
    plot_err(res_folder_kdn+'/'+file, model='kdn_geod', parent='dn', color=['b','seagreen','magenta'],ax=ax3)
    if ii==0:
        ax3.set_title('Classification Error', fontsize=40)

    
    ax4 = plt.subplot(12,6,ii+5*ii+5, sharex=ax4 if ii!=0 else None)
    plot_ece(res_folder_kdn+'/'+file, model='kdn_geod', parent='dn', color=['b','seagreen','magenta'],ax=ax4)

    if ii==0:
        ax4.set_title('MCE', fontsize=40)

    ax5 = plt.subplot(12,6,ii+5*ii+3, sharex=ax5 if ii!=0 else None)
    plot_ood(res_folder_kdf_ood+'/'+file, res_folder_kdf_baseline_ood+'/'+file, model='kdf_geod', parent='rf', ax=ax5)

    if ii==0:
        ax5.set_title('Mean Max Conf.', fontsize=40)

    ax6 = plt.subplot(12,6,ii+5*ii+6, sharex=ax6 if ii!=0 else None)
    plot_ood(res_folder_kdn_ood+'/'+file, res_folder_kdn_baseline_ood+'/'+file, model='kdn_geod', parent='dn', color=['b','seagreen','magenta'], ax=ax6)

    if ii==0:
        ax6.set_title('Mean Max Conf.', fontsize=40)

handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, ncol=4, loc="lower left", bbox_to_anchor=(0.1,-0.04), fontsize=30, frameon=False)

handles, labels = ax3.get_legend_handles_labels()
fig.legend(handles, labels, ncol=4, loc="lower right", bbox_to_anchor=(0.95,-0.04), fontsize=30, frameon=False)
fig.text(0.2, -0.01, "Number of Training Samples (log)", ha="center", fontsize=35)
fig.text(0.45, -0.01, "Distance", ha="center", fontsize=35)

fig.text(0.7, -0.01, "Number of Training Samples (log)", ha="center", fontsize=35)
fig.text(0.95, -0.01, "Distance", ha="center", fontsize=35)

fig.text(0.28, 1, "KDF and RF", ha="center", fontsize=60)
fig.text(0.78, 1, "KDN and DN", ha="center", fontsize=60)
plt.subplots_adjust(hspace=.6,wspace=.6)
plt.tight_layout()
plt.savefig('/Users/jayantadey/kdg/benchmarks/plots/openml_detailed1.pdf', bbox_inches='tight')
# %%
