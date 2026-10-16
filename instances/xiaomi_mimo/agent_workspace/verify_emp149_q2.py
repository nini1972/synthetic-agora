import numpy as np, json
def henon_lyap(a, b=0.3, T=200000, burn=20000, seed=0, qint=10):
    rng=np.random.default_rng(seed)
    x,y=rng.normal(0,0.1,2)
    v=np.eye(2); l1=l2=0.0; n=0
    for t in range(T+burn):
        nx,ny=1-a*x*x+y, b*x
        x,y=nx,ny
        if np.abs(x)>1e10 or np.isnan(x): return None,None  # escaped
        if t<burn:
            v=np.eye(2); continue
        J=np.array([[-2*a*x,1.0],[b,0.0]])
        v=J@v; n+=1
        if n%qint==0:
            q,R=np.linalg.qr(v)
            d=np.sign(np.diag(R)); d[d==0]=1
            v=q*d
            l1+=np.log(abs(R[0,0])+1e-300); l2+=np.log(abs(R[1,1])+1e-300)
    return l1/n, l2/n
rows=[]
for a in [0.6,0.9,1.05,1.1,1.2,1.3,1.4]:
    l1,l2=henon_lyap(a)
    if l1 is None: rows.append({"a":a,"status":"escaped_or_nan"}); continue
    D_ky = 1 + l1/abs(l2) if l1>0 else 1.0
    rows.append({"a":a,"l1":round(l1,4),"l2":round(l2,4),"l1+l2":round(l1+l2,4),
                 "ln_b":round(np.log(0.3),4),"D_ky":round(D_ky,4),
                 "Q_proxy=-l1-D_ky":round(-l1-D_ky,4)})
print(json.dumps(rows,indent=2))
json.dump(rows,open("verify_emp149_metrics2.json","w"),indent=2)
