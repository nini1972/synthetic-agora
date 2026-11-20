import json, numpy as np
from scipy.stats import spearmanr, rankdata

# T2 fixed-eps arrays from the World C run
bands = ['delta','theta','alpha','beta','gamma']
freq  = np.arange(1,6, dtype=float)
rr_f  = np.array([0.22949918656289847,0.5250540197611824,0.6996838901765693,0.6327771182341819,0.8955589160872105])
ent_f = np.array([5.279754975786566,4.740336464207962,6.205803008060513,5.029347652431494,6.958365299318843])
rms_f = np.array([23.497485675752973,15.876619760623866,17.55782345841647,36.657764847237274,31.862571282570503])
eps_m = np.array([9.852423095703125,5.161639404296874,4.342999267578126,5.302532958984374,2.302471923828125])

out = {}
out['rho_eps_matched_freq'] = spearmanr(eps_m, freq).correlation
out['rho_rr_freq_fixed']    = spearmanr(rr_f, freq).correlation
out['rho_ent_freq_fixed']   = spearmanr(ent_f, freq).correlation
out['rho_ent_rr_fixed']     = spearmanr(ent_f, rr_f).correlation
out['rho_rms_freq_fixed']   = spearmanr(rms_f, freq).correlation
out['rho_rms_rr_fixed']     = spearmanr(rms_f, rr_f).correlation

# rank-based partial correlation: ENT vs freq controlling RR (fixed-eps branch)
rE, rF, rR = rankdata(ent_f), rankdata(freq), rankdata(rr_f)
def pcorr(a,b,c):
    r_ab=np.corrcoef(a,b)[0,1]; r_ac=np.corrcoef(a,c)[0,1]; r_bc=np.corrcoef(b,c)[0,1]
    return (r_ab-r_ac*r_bc)/np.sqrt((1-r_ac**2)*(1-r_bc**2))
out['partial_ent_freq_given_rr_rank'] = pcorr(rE,rF,rR)

# matched-eps branch: direct sign
rEps = rankdata(eps_m)
out['matched_ent_freq_indep_check'] = spearmanr([5.266419579720961,4.238503027120145,5.126782965433725,3.691935167514131,3.476222146923267], freq).correlation

# Operating-curve check: ENT monotone in RR along each band's eps-path?
with open('rqa_operating_curve_worldc.json') as f: wc = json.load(f)
for band in ['delta','beta']:
    rr = np.array(wc['operating_curves'][band]['rr']); ent = np.array(wc['operating_curves'][band]['ent'])
    out[f'curve_{band}_rho_rr_ent'] = spearmanr(rr, ent).correlation

# Flip-point preview for delta-vs-beta: interpolate ent_beta on delta's rr grid
rrd = np.array(wc['operating_curves']['delta']['rr']); end = np.array(wc['operating_curves']['delta']['ent'])
rrb = np.array(wc['operating_curves']['beta']['rr']);  enb = np.array(wc['operating_curves']['beta']['ent'])
enb_on_rrd = np.interp(rrd, rrb, enb)
diff = end - enb_on_rrd   # >0 => delta more entropic => negative sign branch
out['delta_minus_beta_ent_at_rr_0.05'] = float(np.interp(0.05, rrd, end) - np.interp(0.05, rrb, enb))
out['delta_minus_beta_ent_at_rr_0.373'] = float(diff[-1])
out['beta_curve_max_rr'] = float(rrb[-1]); out['delta_curve_max_rr'] = float(rrd[-1])

print(json.dumps(out, indent=2))
json.dump(out, open('../../shared_agora/artifacts/glm_operating_curve_stats.json','w'), indent=2)
