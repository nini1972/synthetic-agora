from colony_lib.datasets import load_dataset
ds = load_dataset('neural_eeg')
print('type:', type(ds))
if isinstance(ds, dict) or hasattr(ds, 'keys'):
    keys = list(ds.keys())
    print('keys:', keys)
    for k in keys:
        v = ds[k]
        print(k, type(v), getattr(v, 'shape', None))
else:
    import numpy as np
    arr = np.asarray(ds)
    print('arr shape:', arr.shape, getattr(arr, 'dtype', None))
