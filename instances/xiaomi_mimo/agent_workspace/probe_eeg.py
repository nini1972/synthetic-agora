from colony_lib.datasets import load_dataset
ds = load_dataset('neural_eeg')
print('type:', type(ds))
print('keys:', list(ds.keys()) if hasattr(ds, 'keys') else 'N/A')
print('repr:', repr(ds)[:500])
