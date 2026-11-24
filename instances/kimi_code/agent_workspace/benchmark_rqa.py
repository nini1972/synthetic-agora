import numpy as np
import time, warnings
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import recurrence_matrix, compute_rqa_metrics
warnings.filterwarnings('ignore')

ds = load_dataset('neural_eeg')
fs = ds.sampling_rate
X = ds.signal_matrix()

def bandpass(x, fs, lo, hi):
    from scipy import signal
    sos = signal.butter(4, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def embed(x, m, tau):
    return np.array([x[i:i+(m-1)*tau+1:tau] for i in range(len(x)-(m-1)*tau)])

x = bandpass(X[:1500,0], fs, 8, 13)
emb1500 = embed(x, 3, 1)
D = cdist(emb1500, emb1500, metric='chebyshev')
eps = np.percentile(D, 10)
R = (D <= eps).astype(np.uint8)
t0 = time.time()
met = compute_rqa_metrics(R)
t1500 = time.time()-t0
print('N=1500 m=3 time:', t1500, 'metrics:', met)

x2 = bandpass(X[:800,0], fs, 8, 13)
emb800 = embed(x2, 3, 1)
D2 = cdist(emb800, emb800, metric='chebyshev')
eps2 = np.percentile(D2, 10)
R2 = (D2 <= eps2).astype(np.uint8)
t0 = time.time()
met2 = compute_rqa_metrics(R2)
t800 = time.time()-t0
print('N=800 m=3 time:', t800, 'metrics:', met2)
