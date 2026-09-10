import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thomas_eoc_part1 import *

# Debug: test symbolization at b=0.05 (chaotic)
b = 0.05
dt = 0.05
T_t = 200
T_m = 100
rng = np.random.default_rng(42)
state = rng.standard_normal(3) * 0.5

for _ in range(int(T_t/dt)):
    state = rk4_step(state, dt, b)
traj = np.zeros((int(T_m/dt), 3))
for j in range(len(traj)):
    state = rk4_step(state, dt, b)
    traj[j] = state

print(f"Trajectory shape: {traj.shape}")
print(f"x range: [{traj[:,0].min():.4f}, {traj[:,0].max():.4f}]")
print(f"x std: {traj[:,0].std():.4f}")
print(f"x mean: {traj[:,0].mean():.4f}")

sym = symbolize(traj)
print(f"\nSymbol array shape: {sym.shape}")
print(f"First 20 symbols: {sym[:20]}")
print(f"Unique symbols: {np.unique(sym)}")
print(f"Symbol counts: {np.bincount(sym.astype(int))}")

# Also test with longer trajectory
T_t2 = 300
T_m2 = 500
state2 = rng.standard_normal(3) * 0.5
for _ in range(int(T_t2/dt)):
    state2 = rk4_step(state2, dt, b)
traj2 = np.zeros((int(T_m2/dt), 3))
for j in range(len(traj2)):
    state2 = rk4_step(state2, dt, b)
    traj2[j] = state2

sym2 = symbolize(traj2)
print(f"\nLonger trajectory: {len(sym2)} symbols")
print(f"Unique: {np.unique(sym2)}")

# Test LZ
s = ''.join(str(c) for c in sym)
print(f"\nString length: {len(s)}")
print(f"First 50 chars: {s[:50]}")
lz = lz76(sym)
print(f"LZ76 result: {lz}")
lz2 = lz76(sym2)
print(f"LZ76 (longer): {lz2}")

# Debug: what does lz76 actually do?
print("\nManual LZ test on simple sequence:")
test1 = np.array([0,1,0,1,0,1,0,1])
print(f"  [0,1,0,1,0,1,0,1] -> lz76 = {lz76(test1)}")
test2 = np.array([0,1,2,0,1,2,0,1])
print(f"  [0,1,2,0,1,2,0,1] -> lz76 = {lz76(test2)}")
test3 = np.array([0,0,0,0,0,0,0,0])
print(f"  [0,0,0,0,0,0,0,0] -> lz76 = {lz76(test3)}")
