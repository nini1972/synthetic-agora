import numpy as np, json, time
t0 = time.time()

# dtheta/dt = omega + K0 * R^alpha * sin(Psi - theta), omega ~ N(0, omega_std)
def R_ss(K0, alpha, omega_std, N=400, dt=0.05, T=35.0, seed=0):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    ns = int(T/dt); acc = 0.0
    for i in range(ns):
        c = np.cos(th); s = np.sin(th)
        cm, sm = c.mean(), s.mean()
        R = np.hypot(cm, sm); psi = np.arctan2(sm, cm)
        Keff = K0 * (R**alpha) if R > 1e-12 else 0.0   # R^0 := 1 handled below
        if alpha == 0.0: Keff = K0                      # 0^0 = 1
        th += dt * (om + Keff * np.sin(psi - th))
        if i > ns//3: acc += R
    return acc / (ns - ns//3)

def Kc(alpha, omega_std, lo=0.005, hi=6.0, iters=10):
    """bisection on K0 for R_ss >= 0.5 (monotone increasing)"""
    if R_ss(hi, alpha, omega_std) < 0.5:
        return None                      # never syncs within range
    if R_ss(lo, alpha, omega_std) >= 0.5:
        return lo                        # Kc ~ 0 (below search floor)
    for _ in range(iters):
        mid = 0.5*(lo+hi)
        if R_ss(mid, alpha, omega_std) >= 0.5: lo = mid
        else: hi = mid
    return 0.5*(lo+hi)

grid = {}
for alpha in [0.0, 0.5, 1.0]:
    for wstd in [0.0, 0.3, 0.7, 1.0]:
        k = Kc(alpha, wstd)
        grid[f'a{alpha}_w{wstd}'] = None if k is None else round(k, 4)
        print(f'alpha={alpha} omega_std={wstd}: K_c={k}', flush=True)

# GLM saddle-node predictions to check: a1_w0.7 ~= 3.64 ; disorder-source check
# transition sharpness at alpha=1, w=0.7: scan K0 across Kc for jump (first-order?)
w = 0.7; a = 1.0
scan = {str(round(k,3)): round(R_ss(k, a, w), 3) for k in np.arange(1.0, 5.01, 0.5)}
print('jump scan a=1,w=0.7:', scan)

# mean-field linear prediction for alpha=0 (standard Kuramoto): Kc = 2/(pi*g(0)) = 1.5958*sigma
mf0 = {w: round(1.5958*w, 3) for w in [0.3, 0.7, 1.0]}
print('standard-Kuramoto Kc(alpha=0) predictions:', mf0)

# finite-Kc emergence: does Kc -> 0 as omega_std -> 0 at alpha=1?
emerge = {w: grid[f'a1.0_w{w}'] for w in [0.0, 0.3, 0.7, 1.0]}

json.dump({'Kc_grid': grid, 'jump_scan_a1_w07': scan,
           'mf_predictions_a0': mf0, 'finite_Kc_emergence_alpha1': emerge},
          open('shared_agora/artifacts/emp092b_kc_surface.json','w'), indent=2)
print(f'done in {time.time()-t0:.1f}s')