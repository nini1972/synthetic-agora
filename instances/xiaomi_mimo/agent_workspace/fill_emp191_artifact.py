import numpy as np, json, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
try:
    from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
except Exception as e:
    print('colony_lib import failed:', e); raise

from colony_lib.datasets import load_dataset
ds = load_dataset('neural_eeg')
# inspect structure
print(type(ds))
if isinstance(ds, dict):
    print(ds.keys())
    for k,v in ds.items():
        try: print(k, getattr(v,'shape',type(v)))
        except: pass

print(dir(ds))
