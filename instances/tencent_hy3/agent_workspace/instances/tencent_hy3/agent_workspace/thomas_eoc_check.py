"""Independent focused replication of EMP-035 (xiaomi_mimo) thesis on Thomas Attractor:
(1) largest Lyapunov exponent lambda1 -> 0 near dissipation threshold b_c ~= 0.208,
(2) a symbolic (Lempel-Ziv) complexity metric does NOT peak at b_c but grows with b.

Thomas cyclically-symmetric system:
  x' = sin(y) - b x
  y' = sin(z) - b y
  z' = sin(x) - b z
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def deriv(s, b):
    return np.array([np.sin(s[1]) - b*s[0],
                     np.sin(s[2]) - b*s[1],
                     np.sin(s[0]) - b*s[2]])


def jac(s, b):
    return np.array([[-b, np.cos(s[1]), 0.0],
                     [0.0, -b, np.cos(s[2])],
                     [np.cos(s[0]), 0.0, -b]])


def rk4_state(s, b, dt):
    k1 = deriv(s, b)
    k2 = deriv(s + 0.5*dt*k1, b)
    k3 = deriv(s + 0.5*dt*k2, b)
    k4 = deriv(s + dt*k3, b)
    return s + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def rk4_lin(s, b, v, dt):
    # linearized step for perturbation v under Jacobian at s
    def step(s_orig, v_orig):
        return jac(s_orig, b) @ v_orig
    k1 = step(s, v)
    k2 = step(s + 0.5*dt*k1, v + 0.5*dt*k1)
    k3 = step(s + 0.5*dt*k2, v + 0.5*dt*k2)
    k4 = step(s + dt*k3, v + dt*k3)
    return v + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def analyze(b, seed=1, dt=0.02, T_trans=40.0, T_meas=160.0):
    rng = np.random.default_rng(seed)
    s = rng.uniform(-1, 1, size=3)
    n_trans = int(T_trans/dt)
    for _ in range(n_trans):
        s = rk4_state(s, b, dt)
    # Lyapunov via Benettin
    v = rng.normal(size=3); v /= np.linalg.norm(v)
    Lyap = 0.0; nsteps = 0
    sym = []
    n_meas = int(T_meas/dt)
    for i in range(n_meas):
        s = rk4_state(s, b, dt)
        # linearized
        v = rk4_lin(s, b, v, dt)
        nv = np.linalg.norm(v)
        if nv > 0:
            Lyap += np.log(nv)
            v /= nv
        nsteps += 1
        if i % 2 == 0:
            # symbol: 3-bit sign of (x,y,z)
            s = (int(x[0] > 0) << 2) | (int(x[1] > 0) << 1) | int(x[2] > 0)
            sym.append(s)
    lam = Lyap / (nsteps * dt)
    # Lempel-Ziv 76 on symbol sequence
    lz = lz76(sym)
    return lam, lz, len(sym)


def lz76(symbols):
    n = len(symbols)
    if n == 0:
        return 0
    dic = set()
    w = ""
    c = 0
    for sym in symbols:
        w += str(sym)
        if w not in dic:
            dic.add(w)
            c += 1
            w = ""
    return c / np.log2(n + 1)  # normalized LZ


def main():
    bs = np.round(np.arange(0.06, 0.305, 0.03), 2)
    lam = []; lz = []
    for b in bs:
        l, z, _ = analyze(float(b), seed=7)
        lam.append(l); lz.append(z)
        print(f"b={b:.2f}  lambda1={l:+.4f}  LZ={z:.3f}")
    lam = np.array(lam); lz = np.array(lz)
    # locate chaos boundary (lambda crossing zero)
    sign = np.sign(lam)
    cross = None
    for i in range(1, len(bs)):
        if sign[i-1] > 0 and sign[i] <= 0:
            cross = bs[i]
            break
    print(f"Estimated chaos-end b_c ~= {cross}")
    peak_arg = bs[np.argmax(lz)]
    print(f"LZ peak at b={peak_arg} (vs b_c~0.21): peak_at_edge={abs(peak_arg-0.21)<0.04}")
    plt.figure(figsize=(7, 5))
    ax1 = plt.gca()
    ax1.plot(bs, lam, 'o-', color='firebrick', label='lambda_1 (Lyapunov)')
    ax1.axhline(0, color='k', lw=0.8)
    ax1.axvline(0.208, color='gray', ls=':', label='dossier b_c=0.208')
    ax1.set_xlabel('dissipation b'); ax1.set_ylabel('lambda_1')
    ax2 = ax1.twinx()
    ax2.plot(bs, lz, 's--', color='navy', label='normalized LZ')
    ax2.set_ylabel('LZ complexity')
    ax1.set_title('Thomas Attractor: lambda1->0 near b~0.21; LZ rises (no edge peak)')
    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1+l2, lb1+lb2, loc='center right', fontsize=8)
    plt.tight_layout()
    plt.savefig('thomas_eoc_check.png', dpi=130)
    print('SAVED thomas_eoc_check.png')


if __name__ == '__main__':
    main()
