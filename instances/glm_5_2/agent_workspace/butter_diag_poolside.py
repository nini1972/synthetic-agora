"""Diagnosis of poolside_laguna's scipy.signal.butter failure mode:
gamma 30-100 Hz at fs=128 (Nyquist=64) + order-5 instability.
Reproduces (1) the Nyquist ValueError, (2) the order-5 'ba' transfer-function
instability with edge near Nyquist, (3) the stable SOS form, (4) our exact
EMP-191/EMP-201 filter parameters.
"""
import numpy as np
from scipy import signal

fs = 128.0
nyq = fs / 2.0
print(f"fs={fs}, Nyquist={nyq} Hz")

# ---------- (1) The Nyquist violation: gamma 30-100 Hz ----------
for output in ("ba", "sos"):
    try:
        if output == "ba":
            signal.butter(5, [30, 100], btype="bandpass", fs=fs, output=output)
        else:
            signal.butter(5, [30, 100], btype="bandpass", fs=fs, output=output)
        print(f"[order5 30-100Hz output={output}] constructed (unexpected!)")
    except Exception as e:
        print(f"[order5 30-100Hz output={output}] -> {type(e).__name__}: {e}")

# ---------- (2) order-5 'ba' bandpass with edge just under Nyquist ----------
# Wn_hi=60 Hz -> normalized 0.9375; 10th-order TF poles crowd the unit circle
b, a = signal.butter(5, [30, 60], btype="bandpass", fs=fs, output="ba")
z, p, k = signal.tf2zpk(b, a)
print(f"[order5 30-60Hz 'ba'] max|pole| = {np.max(np.abs(p)):.8f}")

rng = np.random.default_rng(0)
x = rng.standard_normal(4096)
imp = np.zeros(1000); imp[0] = 1.0
y_imp = signal.lfilter(b, a, imp)
y_ff = signal.filtfilt(b, a, x)
print(f"[order5 30-60Hz 'ba'] lfilter impulse max = {np.nanmax(np.abs(y_imp)):.3e} "
      f"(nan={np.isnan(y_imp).any()})")
print(f"[order5 30-60Hz 'ba'] filtfilt max = {np.nanmax(np.abs(y_ff)):.3e} "
      f"(nan={np.isnan(y_ff).any()})")

# ---------- (3) same edges, SOS form ----------
sos = signal.butter(5, [30, 60], btype="bandpass", fs=fs, output="sos")
y_sos = signal.sosfiltfilt(sos, x)
print(f"[order5 30-60Hz 'sos'] sosfiltfilt max = {np.nanmax(np.abs(y_sos)):.3e} "
      f"(nan={np.isnan(y_sos).any()})")

# ---------- (4) our exact parameters: order-4 SOS, gamma 30-45 ----------
sos45 = signal.butter(4, [30, 45], btype="bandpass", fs=fs, output="sos")
y45 = signal.sosfiltfilt(sos45, x)
print(f"[order4 30-45Hz 'sos'] max = {np.nanmax(np.abs(y45)):.3e} "
      f"(nan={np.isnan(y45).any()})")

# ---------- (5) if one insists on gamma up to Nyquist: clamp ----------
hi_clamped = 0.999 * nyq
sos_cl = signal.butter(4, [30, hi_clamped], btype="bandpass", fs=fs, output="sos")
ycl = signal.sosfiltfilt(sos_cl, x)
print(f"[order4 30-{hi_clamped:.1f}Hz 'sos' clamped] max = {np.nanmax(np.abs(ycl)):.3e} "
      f"(nan={np.isnan(ycl).any()})")
print("DIAGNOSIS COMPLETE")
