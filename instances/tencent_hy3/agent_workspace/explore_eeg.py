import numpy as np
from colony_lib.datasets import load_dataset
ds = load_dataset("neural_eeg")
print("type:", type(ds))
print("keys/attrs:", [a for a in dir(ds) if not a.startswith('_')][:40])
try:
    print("data shape:", np.asarray(ds.data).shape)
except Exception as e:
    print("data err", e)
try:
    print("channels:", ds.channels[:20] if hasattr(ds,'channels') else 'NA')
except Exception as e:
    print("ch err", e)
try:
    print("fs:", getattr(ds,'fs',getattr(ds,'sampling_rate','NA')))
except Exception as e:
    print("fs err", e)
print("repr:", repr(ds)[:500])
