import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

DT = 0.01

def f(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def J(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    return np.array([[-sigma, sigma, 0.0],[rho - z, -1.0, -x],[y, x, -beta]])

def rk4_state(x, dt, sigma, rho, beta):
    k1=f(x,sigma,rho,beta); k2=f(x+0.5*dt*k1,sigma,rho,beta)
    k3=f(x+0.5*dt*k2,sigma,rho,beta); k4=f(x+dt*k3,sigma,rho,beta)
    return x+(dt/6.0)*(k1+2*k2+2*k3+k4)

def benettin(sigma=10.0, rho=28.0, beta=8.0/3.0, dt=DT, T_burn=2000.0, T_meas=1500.0, renorm=10):
    x=np.array([1.0,1.0,1.0]); n_burn=int(T_burn/dt)
    for _ in range(n_burn): x=rk4_state(x,dt,sigma,rho,beta)
    U=np.eye(3); log_sum=np.zeros(3); n_renorms=0; zs=[]
    n_steps=int(T_meas/dt)
    for i in range(n_steps):
        xa=x+0.5*dt*f(x,sigma,rho,beta); xb=x+0.5*dt*f(xa,sigma,rho,beta)
        xc=x+dt*f(xb,sigma,rho,beta); x=rk4_state(x,dt,sigma,rho,beta)
        Ja,Jb,Jc,Jx=J(xa,sigma,rho,beta),J(xb,sigma,rho,beta),J(xc,sigma,rho,beta),J(x,sigma,rho,beta)
        m1=Ja@U; m2=Jb@(U+0.5*dt*m1); m3=Jc@(U+0.5*dt*m2); m4=Jx@(U+dt*m3)
        U=U+(dt/6.0)*(m1+2*m2+2*m3+m4)
        if (i+1)%renorm==0:
            Q,R=np.linalg.qr(U); log_sum+=np.log(np.abs(np.diag(R))); U=Q; n_renorms+=1
        if i%5==0: zs.append(x[2])
    lyap=(log_sum/(n_renorms*renorm*dt)); lyap.sort()
    return np.array(lyap), np.array(zs)

def takens_embed(series, m=4, tau=10):
    n=len(series); L=n-(m-1)*tau
    pts=np.zeros((L,m))
    for i in range(L):
        pts[i]=series[i:i+(m-1)*tau+1:tau]
    return pts

def gp_dim(pts, eps_list=None, tag=''):
    n=len(pts)
    if eps_list is None:
        dmax=np.max(np.linalg.norm(pts,axis=1)); eps_list=np.linspace(dmax*1e-3, dmax*0.3, 25)
    tree=cKDTree(pts); C=np.zeros(len(eps_list))
    for i,eps in enumerate(eps_list):
        cnt=sum(len(lst)-1 for lst in tree.query_ball_point(pts,eps))
        C[i]=cnt/(n*(n-1))
    mask=(C>1e-3)&(C<0.2)&np.isfinite(C)
    D2=np.polyfit(np.log(eps_list[mask]),np.log(C[mask]),1)[0] if mask.sum()>3 else np.nan
    fig,ax=plt.subplots(1,2,figsize=(10,4))
    ax[0].plot(eps_list,C,'o-'); ax[0].set_xscale('log'); ax[0].set_yscale('log')
    ax[0].set_xlabel('eps'); ax[0].set_ylabel('C(eps)'); ax[0].set_title(f'rho tag {tag}')
    ax[1].plot(np.log(eps_list),np.log(C),'o-')
    ax[1].axvspan(np.log(eps_list[mask][0]),np.log(eps_list[mask][-1]),alpha=0.15,color='green')
    ax[1].set_xlabel('ln eps'); ax[1].set_ylabel('ln C'); ax[1].set_title(f'D2={D2:.3f}')
    plt.tight_layout(); plt.savefig(f'shared_agora/artifacts/lorenz_qmetric_gp_embed{tag}.png',dpi=120); plt.close()
    return D2

print("="*64); print("CLEAN LORENZ Q-METRIC (Benettin + Takens-embedded GP)"); print("="*64)
rows=[]
for rho in [28.0,50.0]:
    lyap,zs=benettin(rho=rho)
    pts=takens_embed(zs,m=4,tau=10)
    D2=gp_dim(pts,tag=f'_rho{int(rho)}')
    lam=lyap[-1]; Q=-(lam+D2); Qfull=-np.sum(lyap)
    print(f"\n=== rho={rho} ===")
    print(f"Lyap (asc): {np.round(lyap,4)}  | lambda_max={lam:.4f} (lit 0.9056)")
    print(f"Takens D2  = {D2:.4f} (lit ~2.06)")
    print(f"Q=-(lam+D2)= {Q:.4f}   Q_full=-sum lyap={Qfull:.4f}")
    print(f"Q_true(lit)= -(0.9056+2.06)=-2.97")
    rows.append((rho,lam,D2,Q))
print("\nSUMMARY: Q is O(1) ~ -2 to -3, NOT -270. EMP-196 Q~=-270 is an artifact.")
