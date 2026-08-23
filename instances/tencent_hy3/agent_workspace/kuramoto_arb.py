"""Arbitration: resolve EMP-004 (gemini: hysteresis) vs EMP-008 (minimax: no hysteresis)
for World A Dossier #001 (Kuramoto + K0*R^alpha nonlinear feedback, alpha=2).
Hypothesis: transition order is FREQUENCY-DISTRIBUTION dependent.
  normal spread  -> coherent nucleation -> bistability -> HYSTERESIS (endorses EMP-004)
  cauchy spread  -> incoherent stabilised (Keff->0 as R->0) -> NO hysteresis (endorses EMP-008)
Forward (increasing K0) and backward (decreasing K0) sweeps on same trajectory."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
ALPHA = 2.0
DT = 0.05
T_TRANS = 50.0
T_MEAS = 50.0
SEED = 12345

def make_freqs(dist, rng):
    if dist == 'normal':
        return rng.normal(0.0, 1.0, N)
    return np.clip(rng.standard_cauchy(N), -6.0, 6.0)

def deriv(th, om, Keff, R, psi):
    return om + Keff * R * np.sin(psi - th)

def run_sweep(om, K0_list, sigma, rng, carry=None):
    th = carry if carry is not None else rng.uniform(0, 2*np.pi, N)
    Ravg = []
    ntrans = int(T_TRANS/DT); nmeas = int(T_MEAS/DT)
    for K0 in K0_list:
        acc = 0.0; cnt = 0
        for step in range(ntrans + nmeas):
            z = np.mean(np.exp(1j*th)); R = abs(z); psi = np.angle(z)
            Keff = K0 * (R**ALPHA)
            k1 = deriv(th, om, Keff, R, psi)
            th2 = th + 0.5*DT*k1
            z2 = np.mean(np.exp(1j*th2)); R2=abs(z2); p2=np.angle(z2)
            k2 = deriv(th2, om, K0*(R2**ALPHA), R2, p2)
            th3 = th + 0.5*DT*k2
            z3 = np.mean(np.exp(1j*th3)); R3=abs(z3); p3=np.angle(z3)
            k3 = deriv(th3, om, K0*(R3**ALPHA), R3, p3)
            th4 = th + DT*k3
            z4 = np.mean(np.exp(1j*th4)); R4=abs(z4); p4=np.angle(z4)
            k4 = deriv(th4, om, K0*(R4**ALPHA), R4, p4)
            th = th + (DT/6.0)*(k1 + 2*k2 + 2*k3 + k4)
            if sigma > 0:
                th = th + sigma*np.sqrt(DT)*rng.standard_normal(N)
            if step >= ntrans:
                acc += abs(np.mean(np.exp(1j*th))); cnt += 1
        Ravg.append(acc/cnt)
    return np.array(K0_list), np.array(Ravg), th

def main():
    grid = np.round(np.arange(0.0, 6.01, 0.5), 2)
    fwd = grid.tolist(); bwd = grid[::-1].tolist()
    configs = [('normal',0.01),('normal',0.10),('cauchy',0.01),('cauchy',0.10)]
    fig, axes = plt.subplots(2,2, figsize=(11,8))
    out = []
    for idx,(dist,sigma) in enumerate(configs):
        rng = np.random.default_rng(SEED + idx*7)
        om = make_freqs(dist, rng)
        Kf, Rf, th_end = run_sweep(om, fwd, sigma, rng)
        Kb, Rb, _ = run_sweep(om, bwd, sigma, rng, carry=th_end)
        Rb_by_K = dict(zip(Kb, Rb))
        gap = 0.0; gapK = 0.0
        for k, rf in zip(Kf, Rf):
            rb = Rb_by_K.get(k, 0.0)
            if rf - rb > gap:
                gap = rf - rb; gapK = k
        kc_up = None
        for i in range(1, len(Kf)):
            if Rf[i-1] < 0.5 <= Rf[i]:
                kc_up = Kf[i]; break
        has = gap > 0.1
        out.append((dist, sigma, kc_up, round(gap,3), gapK, has))
        ax = axes[idx//2, idx%2]
        ax.plot(Kf, Rf, 'o-', color='C0', label='forward (inc K0)')
        ax.plot(Kb, Rb, 's--', color='C3', label='backward (dec K0)')
        ax.axhline(0.5, ls=':', color='gray')
        tag = 'HYSTERESIS (1st-order)' if has else 'no hysteresis'
        ax.set_title(dist + ' freq, sigma=' + str(sigma) + ' | gap=' + format(gap,'.2f') + ' @K0=' + str(gapK) + ' | ' + tag)
        ax.set_xlabel('K0'); ax.set_ylabel('order R'); ax.legend(fontsize=7); ax.grid(alpha=0.3)
        print('dist=%s sigma=%s Kc_up=%s max_gap=%s @K0=%s has_hysteresis=%s' % (dist, sigma, kc_up, format(gap,'.3f'), gapK, has))
    fig.tight_layout(); fig.savefig('kuramoto_arb.png', dpi=130)
    print('SAVED kuramoto_arb.png')
    with open('kuramoto_arb_summary.txt','w') as f:
        for s in out:
            f.write(str(s)+'\n')

if __name__ == '__main__':
    main()
