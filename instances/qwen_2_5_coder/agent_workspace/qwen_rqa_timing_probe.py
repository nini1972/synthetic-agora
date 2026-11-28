import time, numpy as np, warnings
warnings.filterwarnings("ignore")
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

ds = load_dataset("neural_eeg")
fs = int(ds.sampling_rate)
X = np.asarray(ds.signal_matrix(), dtype=np.float64)
import scipy.signal as sig
W = 1024
zc = (X[:W,0] - X[:W,0].mean())/ (X[:W,0].std()+1e-12)
b,a = sig.butter(4, [30/64, 45/64], btype="band")
y = sig.filtfilt(b,a,zc)
E = takens_embedding(y, m=3, tau=2).astype(np.float32)
d0 = time.time()
D = np.sqrt(((E[:,None,:]-E[None,:,:])**2).sum(-1))
d1 = time.time()
r0 = time.time()
q = compute_rqa_metrics((D<=0.3).astype(np.uint8))
d2 = time.time()
print(f"N={D.shape[0]} dist={d1-d0:.3f}s rqa={d2-r0:.3f}s total_per_chband={d2-d0:.3f}s")
# rough budget: 14ch*5bands*2conv*(dist + 2*rqa) + P1 extra
print(f"est full sweep ~ {14*5*2*(d1-d0)+14*5*3*(d2-r0):.1f}s")
