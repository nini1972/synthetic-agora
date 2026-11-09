import numpy as np
from colony_lib.datasets import load_dataset
ds = load_dataset('neural_eeg')
print('metadata:', ds.metadata)
print('primary_signal:', ds.primary_signal)
print('columns:', ds.columns)
v = ds.values() if callable(ds.values) else ds.values
print('type(v):', type(v), getattr(v,'shape',None))
if isinstance(v, dict):
    for k, val in v.items(): print(' ', k, type(val), getattr(val,'shape',None))
elif isinstance(v, (list, tuple)):
    for i, val in enumerate(v[:30]): print(' ', i, type(val), getattr(val,'shape',None) or (len(val) if hasattr(val,'__len__') else ''))
d = ds.data
print('type(data):', type(d), getattr(d,'shape',None))
if isinstance(d, dict):
    for k, val in d.items(): print('  d:', k, type(val), getattr(val,'shape',None))
print('shape attr:', ds.shape)
print('time:', type(ds.time), getattr(ds.time,'shape',None))
