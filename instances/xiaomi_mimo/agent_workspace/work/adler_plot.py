import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json, sys
sys.path.insert(0,'work')
exec(open('work/adler_indie.py').read().split("print(\"D =")[0])  # load funcs

d = json.load(open('work/adler_indie.json'))
dws=[4.,5.,6.]; claim=[d['results'][str(w)]['claim'] for w in dws]
pde=[d['results'][str(w)]['pde'] for w in dws]; mc=[d['results'][str(w)]['mc'] for w in dws]

fig,ax=plt.subplots(1,2,figsize=(11,4.2))
x=np.arange(3); wdt=0.26
ax[0].bar(x-wdt, claim, wdt, label='EMP-171/192 claim', color='#4C72B0')
ax[0].bar(x,     pde,   wdt, label='FV-FP PDE (mine)', color='#55A868')
ax[0].bar(x+wdt, mc,    wdt, label='fresh MC seed=20260214', color='#C44E52')
ax[0].set_xticks(x); ax[0].set_xticklabels(['dw=4','dw=5','dw=6'])
ax[0].set_ylabel('stationary R'); ax[0].set_title('Adler stationary order parameter: 3-method agreement')
ax[0].legend(fontsize=8); ax[0].set_ylim(0,0.62)

Rp,p,th=R_pde(4.0)
ax[1].plot(th/np.pi, p*p.size*2*np.pi/(2*np.pi)*2*np.pi, lw=1.2, color='#55A868')
ax[1].set_xlabel(r'$\theta/\pi$'); ax[1].set_ylabel('stationary density p(th)')
ax[1].set_title(r'PDE stationary density, dw=4 (locked fraction $R=%.4f$)'%Rp)
plt.tight_layout(); plt.savefig('work/adler_indie_verification.png',dpi=130)
print('saved work/adler_indie_verification.png')
