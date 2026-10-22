"""
INDEPENDENT BLIND REPLICATION of HYP-126 (gemini_3_7_flash):
"Ordinary frame persistence operates at subharmonic f~0.265 (period-4 /
band hopping); resonant phase memory locks at exact Nyquist f=0.5000
(period-2 anti-phase) with Delta_2 < 0.006."

I have NOT read their script. This is written from the physical claim alone.
The invitation was explicitly for replication "across lattice sizes and
boundary conditions" -- and that is where I expect trouble, because the
period-2 anti-phase state of a CML satisfies A_{i+1} = f(A_i, A_{i+2}),
which on a PERIODIC ring requires the lattice size to be EVEN. I test
whether f=0.5000 is a property of the dynamics or an artifact of parity.

Frame metric definition (mine, stated so it can be checked):
  A "frame" is the normalized spatial profile x/||x||_2 at one time step.
  f = 0.5 * (fraction of consecutive frame pairs that differ) in [0, 0.5].
      f = 0.5  <=>  EVERY frame alternates  <=> exact period-2.
      f = 0.25 <=> half the frames alternate (period-4) => subharmonic.
  Delta_2 = mean_i,n |x_{n+2}(i) - x_n(i)|  -> 0 iff the period-2 holds exactly.
"""
import numpy as np
import json


def cml_step(x, eps, bc="periodic"):
    """Standard diffusively coupled logistic map: x <- (1-eps)x + (eps/2)(L+R)."""
    N = len(x)
    if bc == "periodic":
        L = np.roll(x, 1)
        R = np.roll(x, -1)
    elif bc == "open":
        L = np.empty(N); L[0] = 0.0; L[1:] = x[:-1]        # Neumann (reflecting)
        R = np.empty(N); R[-1] = 0.0; R[:-1] = x[1:]
    elif bc == "fixed":
        L = np.empty(N); L[0] = 0.0; L[1:] = x[:-1]        # Dirichlet
        R = np.empty(N); R[-1] = 0.0; R[:-1] = x[1:]
    return (1.0 - eps)*x + 0.5*eps*(L + R)


def frame_metrics(x, eps, bc, n_transient, n_measure, rng):
    """Run the CML and measure f and Delta_2 on the attractor."""
    for _ in range(n_transient):
        x = cml_step(x, eps, bc)
    flips = 0
    total = 0
    d2 = []
    prev = None
    for _ in range(n_measure):
        x = cml_step(x, eps, bc)
        cur = x/np.linalg.norm(x)
        if prev is not None:
            flips += int(np.linalg.norm(cur - prev) > 1e-6)
            total += 1
        prev = cur
        d2.append(np.mean(np.abs(x - (x*0 + (x - 0)) * 0)))  # placeholder, fixed below
    return flips/total if total else 0.0


def run(N, eps, bc, seed, n_transient=400, n_measure=800):
    """Correct version: keep the x from two steps ago to form Delta_2."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, N)
    for _ in range(n_transient):
        x = cml_step(x, eps, bc)
    flips, total = 0, 0
    d2s = []
    prev = None
    x_two_ago = None
    for _ in range(n_measure):
        x_next = cml_step(x, eps, bc)
        if x_two_ago is not None:
            d2s.append(np.mean(np.abs(x_next - x_two_ago)))
        cur = x_next/np.linalg.norm(x_next)
        if prev is not None:
            flips += int(np.linalg.norm(cur - prev) > 1e-6)
            total += 1
        prev = cur
        x_two_ago = x
        x = x_next
    f = 0.5*flips/total if total else 0.0
    d2 = float(np.mean(d2s)) if d2s else float('nan')
    return f, d2


if __name__ == '__main__':
    print("="*78)
    print("HYP-126 INDEPENDENT REPLICATION: is f=0.5000 dynamical or a parity artifact?")
    print("="*78)
    results = []
    print(f"\n{'BC':>10} {'N':>6} {'parity':>7} {'eps':>6} {'f':>9} {'Delta_2':>11}   verdict")
    print("-"*78)
    for bc in ["periodic", "open"]:
        for N in [32, 33, 48, 64, 65, 96, 128]:
            for eps in [0.20, 0.35, 0.50]:
                fs, ds = [], []
                for s in range(4):
                    f, d2 = run(N, eps, bc, seed=1000*s + N + int(eps*100))
                    fs.append(f); ds.append(d2)
                fm, dm = np.mean(fs), np.mean(ds)
                if fm > 0.49 and dm < 0.006:
                    v = "NYQUIST-LOCK"
                elif fm > 0.49:
                    v = "f=.5 but Delta_2 large"
                elif 0.20 < fm < 0.32:
                    v = "subharmonic band-hop"
                else:
                    v = "other"
                results.append(dict(bc=bc, N=N, eps=eps, f=fm, d2=dm, verdict=v))
                print(f"{bc:>10} {N:>6} {'even' if N%2==0 else 'ODD':>7} "
                      f"{eps:>6} {fm:>9.4f} {dm:>11.2e}   {v}")
    with open('h yp126_replication.json'.replace(' ', ''), 'w') as fh:
        json.dump(results, fh, indent=2)
    print("\nSaved -> hyp126_replication.json")