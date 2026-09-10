import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def rk4_step(state, dt, b):
    k1 = thomas_rhs(state, b)
    k2 = thomas_rhs(state + 0.5*dt*k1, b)
    k3 = thomas_rhs(state + 0.5*dt*k2, b)
    k4 = thomas_rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([[-b, np.cos(y), 0], [0, -b, np.cos(z)], [np.cos(x), 0, -b]])

def compute_lyapunov_spectrum(b, dt=0.02, T_transient=200, T_measure=600, seed=42):
    rng = np.random.default_rng(seed)
    state = rng.standard_normal(3) * 0.5
    Q = np.eye(3)
    n_t = int(T_transient / dt)
    n_m = int(T_measure / dt)
    renorm_every = int(0.5 / dt)
    for _ in range(n_t):
        state = rk4_step(state, dt, b)
    lyap_sums = np.zeros(3)
    n_renorms = 0
    for i in range(n_m):
        state = rk4_step(state, dt, b)
        J = thomas_jacobian(state, b)
        for c in range(3):
            Q[:, c] = Q[:, c] + dt * (J @ Q[:, c])
        if (i + 1) % renorm_every == 0:
            Q_r, R = np.linalg.qr(Q)
            for k in range(3):
                r_kk = R[k, k]
                if abs(r_kk) > 0:
                    lyap_sums[k] += np.log(abs(r_kk))
            Q = Q_r
            n_renorms += 1
    T_total = n_renorms * renorm_every * dt
    if T_total == 0:
        return np.zeros(3)
    return lyap_sums / T_total

def symbolize(traj, n_sym=8, comp=0):
    x = traj[:, comp]
    pcts = np.linspace(0, 100, n_sym + 1)
    bins = np.percentile(x, pcts)
    bins[0] = -np.inf
    bins[-1] = np.inf
    return np.clip(np.digitize(x, bins) - 1, 0, n_sym - 1)

def block_entropy(symbols, block_size):
    n = len(symbols)
    if n < block_size:
        return 0.0
    blocks = [tuple(symbols[i:i+block_size]) for i in range(n - block_size + 1)]
    counts = Counter(blocks)
    total = len(blocks)
    return -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)

def lz76(symbols):
    """Correct LZ76 complexity measure.
    Parses the string left-to-right, building phrases.
    The search for a match is restricted to positions strictly BEFORE the current pattern start."""
    s = list(map(int, symbols))
    n = len(s)
    i = 0
    comp = 0
    parsed_end = -1  # end of last parsed phrase (exclusive)
    while i < n:
        found = False
        # Try longest match first: from remaining length down to 1
        for length in range(min(n - i, i - parsed_end), 0, -1):
            pat = s[i:i+length]
            # Search for this pattern in the already-parsed portion (positions 0 to i-1)
            for j in range(0, i):
                if s[j:j+length] == pat:
                    found = True
                    break
            if found:
                break
        if found:
            i += length  # extend match by the matched length
        else:
            comp += 1
            parsed_end = i
            i += 1
    return comp

def perm_entropy(symbols, order=4, delay=1):
    import math
    n = len(symbols)
    if n < order * delay:
        return 0.0
    patterns = []
    for i in range(n - (order - 1) * delay):
        pattern = tuple(np.argsort([symbols[i + k*delay] for k in range(order)]))
        patterns.append(pattern)
    counts = Counter(patterns)
    total = len(patterns)
    max_H = np.log2(math.factorial(order))
    H = -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)
    return H / max_H if max_H > 0 else 0

print("Part 1 (v2) loaded with FIXED LZ76. Ready to run experiment.")
