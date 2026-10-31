import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np

branches={"Lorenz":dict(lam=1.177,D2=1.878,K=13.667,d=3),
          "Henon":dict(lam=0.370,D2=1.186,K=0.400,d=2),
          "Rule110":dict(lam=0.003,D2=1.000,K=0.560,d=1)}
names=list(branches)
forms={
 "Q raw":       lambda v:-v['lam']-v['D2']-v['K'],
 "Q1 K/d":      lambda v:-v['lam']-v['D2']-v['K']/v['d'],
 "Q2 K/d^2":    lambda v:-v['lam']-v['D2']-v['K']/v['d']**2,
 "Q3 K/(l+D2)": lambda v:-v['lam']-v['D2']-v['K']/(v['lam']+v['D2']),
 "Q7 logK":     lambda v:-v['lam']-v['D2']-np.log(v['K']),
 "Q8 noK":      lambda v:-v['lam']-v['D2'],
}
labels=list(forms)
x=np.arange(len(labels)); w=0.25
fig,ax=plt.subplots(figsize=(10,5.5))
for i,n in enumerate(names):
    vals=[forms[f](branches[n]) for f in labels]
    ax.bar(x+i*w-w, vals, w, label=n)
ax.axhline(-2.08, color='r', ls='--', lw=1.5, label='claimed invariant −2.08')
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15)
ax.set_ylabel("Q value"); ax.set_title("DOSSIER-158: No K-normalization collapses the Q branches onto −2.08")
ax.legend(fontsize=8); ax.grid(alpha=.3, axis='y')
plt.tight_layout(); plt.savefig("../../shared_agora/artifacts/EMP-qbranch-collapse.png", dpi=120)
print("saved")
