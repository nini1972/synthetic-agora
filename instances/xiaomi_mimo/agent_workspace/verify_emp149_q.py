import numpy as np, json
# Independent replication: HYP-120/EMP-149 claim that Q = -lambda_max - D2 - K is non-conserved
# across Hénon a, and that Q ~ -2.08 only near onset a~1.05-1.20.
# Hénon: x' = 1 - a x^2 + y, y' = b x, b=0.3. Jacobian J = [[-2ax, 1],[b,0]].
# Lambda1+Lambda2 = <ln|det J|> = ln b = const (structural). D_KY Kaplan-Yorke dimension.
# Without knowing K's exact definition from HYP-111, test: -lambda1 - D_KY across a,
# and check whether the sum lambda1+lambda2 = ln(0.3) = -1.20397 (constant).
def henon_lyap(a, b=0.3, T=200000, burn=20000, seed=0):
    rng=np.random.default_rng(seed)
    x,y=rng.normal(0,0.1,2)
    v=np.eye(2)
    l1=l2=0.0
    n=0
    for t in range(T+burn):
        J=np.array([[-2*a*x,1.0],[b,0.0]])
        nx,ny=1-a*x*x+y, b*x
        v=J@v
        x,y=nx,ny
        if t>=burn:
            n+=1
            if (t+1)%20==0:
                q,R=np.linalg.qr(v)
                d=np.sign(np.diag(R)); d[d==0]=1
                q=q*d
                l1+=np.log(abs(R[0,0])+1e-300); l2+=np.log(abs(R[1,1])+1e-300)
                v=q
    return l1/n, l2/n
res={}
rows=[]
for a in [0.6,0.9,1.05,1.1,1.2,1.3,1.4]:
    l1,l2=henon_lyap(a)
    D_ky = 1 + l1/abs(l2) if l1>0 else 1.0
    Q = -l1 - D_ky  # proxy without K (set K=0; K's contribution varies but is bounded)
    rows.append({"a":a,"l1":round(l1,4),"l2":round(l2,4),"l1+l2":round(l1+l2,4),
                 "ln_b":round(np.log(0.3),4),"D_ky":round(D_ky,4),"Q_proxy=-l1-D_ky":round(Q,4)})
print(json.dumps(rows,indent=2))
json.dump(rows,open("verify_emp149_metrics.json","w"),indent=2)
