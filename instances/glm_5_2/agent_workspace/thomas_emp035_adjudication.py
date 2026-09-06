# PRF-009 follow-up: Independent adjudication of EMP-035 (xiaomi_mimo)
# Claims under test: (a) lambda_1 -> 0 near b_c ~ 0.208; (b) no edge-of-chaos
# peak at b_c (h_KS monotone down with b); (c) LZ INCREASES with b
# (0.78 -> 3.02 over b in [0.05, 0.30]); (d) PE mild peak at b ~ 0.17.
# Method: Benettin 2-trajectory lambda_1 + Kaspar-Schuster LZ76 on 8-symbol
# octant code + block entropy (bridge to EMP-010/gemini).
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def thomas_rk4(s, b, dt):
    x, y, z = s
    k1x, k1y, k1z = np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z
    y2, z2, x2 = y + 0.5*dt*k1y, z + 0.5*dt*k1z, x + 0.5*dt*k1x
    k2x, k2y, k2z = np.sin(z2) - b*y2, np.sin(x2) - b*z2, np.sin(y2) - b*x2
    y3, z3, x3 = y + 0.5*dt*k2y, z + 0.5*dt*k2z, x + 0.5*dt*k2x
    k3x, k3y, k3z = np.sin(z3) - b*y3, np.sin(x3) - b*z3, np.sin(y3) - b*x3
    y4, z4, x4 = y + dt*k3y, z + dt*k3z, x + dt*k3x
    k4x, k4y, k4z = np.sin(z4) - b*y4, np.sin(x4) - b*z4, np.sin(y4) - b*x4
    return (x + dt/6*(k1x + 2*k2x + 2*k3x + k4x),
            y + dt/6*(k1y + 2*k2y + 2*k3y + k4y),
            z + dt/6*(k1z + 2*k2z + 2*k3z + k4z))

def run(b, dt=0.05, t_trans=100.0, t_meas=400.0, d0=1e-8, seed=0):
    n_trans = int(t_trans/dt); n_meas = int(t_meas/dt)
    rng = np.random.default_rng(1000 + seed)
    x, y, z = rng.uniform(-1, 1, 3)
    for _ in range(n_trans):
        x, y, z = thomas_rk4((x, y, z), b, dt)
    # Lyapunov: shadow trajectory
    x2, y2, z2 = x + d0, y, z
    accum, n_renorm = 0.0, 0
    renorm_every = 10
    syms = np.empty(n_meas, dtype=np.int64)
    for i in range(n_meas):
        x, y, z = thomas_rk4((x, y, z), b, dt)
        x2, y2, z2 = thomas_rk4((x2, y2, z2), b, dt)
        if (i+1) % renorm_every == 0:
            d = np.sqrt((x2-x)**2 + (y2-y)**2 + (z2-z)**2)
            if d == 0.0: d = d0
            accum += np.log(d/d0); n_renorm += 1
            sc = d0/d
            x2, y2, z2 = x + (x2-x)*sc, y + (y2-y)*sc, z + (z2-z)*sc
        syms[i] = 4*(x > 0) + 2*(y > 0) + (z > 0)
    l1 = accum / (n_renorm * renorm_every * dt)
    return l1, syms

def lz76(seq):
    n = len(seq); i = 0; k = 1; l = 1
    c = 1; kmax = 1
    while k + l <= n:
        if seq[i + l - 1] == seq[k + l - 1]:
            l += 1
            if k + l > n:
                c += 1
                break
        else:
            if l > kmax: kmax = l
            i += 1
            if i == k:
                c += 1
                k += l
                i = 0
                l = 1
            else:
                l = 1
    return c

def block_H(syms, order):
    from collections import Counter
    n_tot = len(syms) - order + 1
    cnt = Counter(tuple(syms[i:i+order]) for i in range(n_tot))
    n = sum(cnt.values())
    return -sum((v/n)*np.log2(v/n) for v in cnt.values()) / order

b_values = [0.05, 0.09, 0.13, 0.17, 0.20, 0.208, 0.216, 0.24, 0.27, 0.30]
rows = []
for b in b_values:
    l1, syms = run(b, seed=int(b*1000))
    n = len(syms)
    c_raw = lz76(syms.tolist())
    c_norm = c_raw * np.log(n)/np.log(8) / n
    H1 = block_H(syms, 1); H2 = block_H(syms, 2)
    rows.append((b, l1, c_norm, H1, H2))
    print(f"b={b:.3f}  lambda1={l1:+.4f}  LZ_norm={c_norm:.3f}  H1={H1:.3f}  H2={H2:.3f}", flush=True)

rows = np.array(rows)
bc = 0.208186
fig, axes = plt.subplots(2, 2, figsize=(13, 10))
ax = axes[0, 0]
ax.plot(rows[:, 0], rows[:, 1], 'o-', color='crimson')
ax.axvline(bc, color='k', ls='--', label=f'b_c = {bc}')
ax.set_xlabel('b'); ax.set_ylabel('lambda_1'); ax.legend()
ax.set_title('Largest Lyapunov (Benettin, indep. GLM)')

ax = axes[0, 1]
ax.plot(rows[:, 0], rows[:, 2], 's-', color='navy', label='LZ76 norm (octant, 8-sym)')
ax.axvline(bc, color='k', ls='--'); ax.legend()
ax.set_xlabel('b'); ax.set_ylabel('LZ normalized')
ax.set_title('LZ complexity vs dissipation')

ax = axes[1, 0]
ax.plot(rows[:, 0], rows[:, 3], '^-', color='seagreen', label='H1')
ax.plot(rows[:, 0], rows[:, 4], 'v-', color='darkorange', label='H2 (entropy rate)')
ax.axvline(bc, color='k', ls='--'); ax.legend()
ax.set_xlabel('b'); ax.set_ylabel('bits/symbol')
ax.set_title('Octant block entropy (bridge to EMP-010)')

ax = axes[1, 1]
ax2 = ax.twinx()
ax.plot(rows[:, 0], rows[:, 2], 's-', color='navy', label='LZ norm')
ax2.plot(rows[:, 0], rows[:, 1], 'o-', color='crimson', alpha=0.6, label='lambda_1')
ax.axvline(bc, color='k', ls='--')
ax.set_xlabel('b'); ax.set_ylabel('LZ norm', color='navy'); ax2.set_ylabel('lambda_1', color='crimson')
ax.set_title('Overlay')

plt.suptitle('GLM adjudication of EMP-035: Thomas attractor complexity vs b', fontsize=11)
plt.tight_layout()
plt.savefig('thomas_emp035_adjudication.png', dpi=140)
print("saved thomas_emp035_adjudication.png")

lz = rows[:, 2]; bs = rows[:, 0]
print(f"\nLZ peak at b = {bs[np.argmax(lz)]:.3f} (value {lz.max():.3f})")
print(f"LZ b=0.05: {lz[0]:.3f}   LZ b=0.30: {lz[-1]:.3f}")
post = bs > bc
print(f"Mean LZ b<b_c: {lz[~post].mean():.3f};  b>b_c: {lz[post].mean():.3f}")
print(f"lambda1 b=0.24: {rows[np.isclose(bs,0.24),1][0]:+.4f}  b=0.30: {rows[-1,1]:+.4f}")
