import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def f(s, b):
    x, y, z = s
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def rk4(s, b, dt):
    k1 = f(s, b)
    k2 = f(s + 0.5*dt*k1, b)
    k3 = f(s + 0.5*dt*k2, b)
    k4 = f(s + dt*k3, b)
    return s + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)

def run(b, dt=0.05, t_trans=2000.0, t_meas=4000.0, d0=1e-8, seed=0):
    n_trans = int(t_trans/dt); n_meas = int(t_meas/dt)
    rng = np.random.default_rng(1000 + seed)
    s1 = rng.uniform(-1, 1, 3)
    # transient
    for _ in range(n_trans):
        s1 = rk4(s1, b, dt)
    s2 = s1 + np.array([d0, 0.0, 0.0])
    accum, n_renorm = 0.0, 0
    renorm_every = 10
    traj = np.zeros((n_meas, 3))
    for i in range(n_meas):
        s1 = rk4(s1, b, dt)
        s2 = rk4(s2, b, dt)
        traj[i] = s1
        if (i+1) % renorm_every == 0:
            d = np.linalg.norm(s2 - s1)
            if d == 0.0: d = d0
            accum += np.log(d/d0); n_renorm += 1
            s2 = s1 + (s2 - s1) * (d0/d)
    l1 = accum / (n_renorm * renorm_every * dt)
    return l1, traj

results = {}
for b in [0.05, 0.208186, 0.25, 0.30]:
    l1, traj = run(b, seed=int(b*1000))
    dists = np.linalg.norm(traj, axis=1)
    results[float(b)] = {
        'lambda1': float(l1),
        'mean_dist': float(dists.mean()),
        'std_xyz': float(traj.std(axis=0).mean()),
        'max_dist': float(dists.max())
    }
    print(f"b={b:.3f}: lambda1={l1:+.6f}, mean_dist={dists.mean():.6f}, max_dist={dists.max():.6f}")

with open('../../shared_agora/artifacts/thomas_edgecase_kimi.json', 'w') as f:
    json.dump(results, f, indent=2)

bs = list(results.keys())
lams = [results[b]['lambda1'] for b in bs]
fig, ax = plt.subplots(figsize=(6,4))
ax.plot(bs, lams, 'o-', color='crimson')
ax.axhline(0.0, color='k', ls='--', alpha=0.4)
ax.set_xlabel('b'); ax.set_ylabel('lambda1')
ax.set_title('Longer-run largest Lyapunov (two-trajectory Benettin)')
fig.savefig('../../shared_agora/artifacts/thomas_edgecase_kimi.png', dpi=150)
print('saved thomas_edgecase_kimi.png')
