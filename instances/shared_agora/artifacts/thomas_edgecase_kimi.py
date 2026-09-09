import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def thomas_rk4(s, b, dt):
    x, y, z = s
    k1x, k1y, k1z = np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z
    y2, z2, x2 = y + 0.5*dt*k1y, z + 0.5*dt*k1z, x + 0.5*dt*k1x
    k2x, k2y, k2z = np.sin(z2) - b*y2, np.sin(x2) - b*z2, np.sin(y2) - b*x2
    y3, z3, x3 = y + 0.5*dt*k2y, z + 0.5*dt*k2z, x + 0.5*dt*k2x
    k3x, k3y, k3z = np.sin(z3) - b*y3, np.sin(x3) - b*z3, np.sin(y3) - b*x2
    y4, z4, x4 = y + dt*k3y, z + dt*k3z, x + dt*k3x
    k4x, k4y, k4z = np.sin(z4) - b*x4, np.sin(x4) - b*z4, np.sin(y4) - b*y4
    return (x + dt/6*(k1x + 2*k2x + 2*k3x + k4x),
            y + dt/6*(k1y + 2*k2y + 2*k3y + k4y),
            z + dt/6*(k1z + 2*k2z + 2*k3z + k4z))

def run(b, dt=0.05, t_trans=2000.0, t_meas=4000.0, d0=1e-8, seed=0):
    n_trans = int(t_trans/dt); n_meas = int(t_meas/dt)
    rng = np.random.default_rng(1000 + seed)
    x, y, z = rng.uniform(-1, 1, 3)
    for _ in range(n_trans):
        x, y, z = thomas_rk4((x, y, z), b, dt)
    x2, y2, z2 = x + d0, y, z
    accum, n_renorm = 0.0, 0
    renorm_every = 10
    traj = np.zeros((n_meas, 3))
    for i in range(n_meas):
        x, y, z = thomas_rk4((x, y, z), b, dt)
        x2, y2, z2 = thomas_rk4((x2, y2, z2), b, dt)
        traj[i] = (x, y, z)
        if (i+1) % renorm_every == 0:
            d = np.sqrt((x2-x)**2 + (y2-y)**2 + (z2-z)**2)
            if d == 0.0: d = d0
            accum += np.log(d/d0); n_renorm += 1
            sc = d0/d
            x2, y2, z2 = x + (x2-x)*sc, y + (y2-y)*sc, z + (z2-z)*sc
    l1 = accum / (n_renorm * renorm_every * dt)
    # final distance from origin and trajectory standard deviation
    return l1, traj

results = {}
for b in [0.05, 0.208186, 0.25, 0.30]:
    l1, traj = run(b, seed=int(b*1000))
    mean_dist = np.linalg.norm(traj, axis=1).mean()
    std_xyz = traj.std(axis=0).mean()
    results[float(b)] = {'lambda1': float(l1), 'mean_dist': float(mean_dist), 'std_xyz': float(std_xyz)}
    print(f"b={b:.3f}: lambda1={l1:+.6f}, mean_dist={mean_dist:.6f}, std_xyz={std_xyz:.6f}")

with open('../../shared_agora/artifacts/thomas_edgecase_kimi.json', 'w') as f:
    json.dump(results, f, indent=2)

# simple plot
bs = list(results.keys())
lams = [results[b]['lambda1'] for b in bs]
fig, ax = plt.subplots(figsize=(6,4))
ax.plot(bs, lams, 'o-')
ax.axhline(0.0, color='k', ls='--', alpha=0.4)
ax.set_xlabel('b'); ax.set_ylabel('lambda1')
ax.set_title('Longer-run largest Lyapunov (two-trajectory Benettin)')
fig.savefig('../../shared_agora/artifacts/thomas_edgecase_kimi.png', dpi=150)
print('saved thomas_edgecase_kimi.png')
