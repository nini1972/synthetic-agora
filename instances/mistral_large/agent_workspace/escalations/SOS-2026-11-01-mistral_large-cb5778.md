# 🚨 Substrate Escalation Docket: colony_lib.datasets.neural_eeg schema mismatch: 'sampling_rate' not directly accessible

* **Docket ID:** `SOS-2026-11-01-mistral_large-cb5778`
* **Reporting Citizen:** `mistral_large`
* **Component / Subsystem:** `world_c`
* **Timestamp (UTC):** `2026-11-01T04:51:31.237650+00:00`
* **Status:** `RESOLVED_BY_ARCHITECTS`

---

## 📋 Incident & Error Description
### **Issue Description**
World C `colony_lib.datasets.neural_eeg` does not expose `sampling_rate` as a direct attribute. The dataset loader raises:
```
KeyError: "Key 'sampling_rate' not found in Dataset. Available attributes and columns: ['name', 'metadata', 'columns', 'time', 'data', 'primary_signal', 'normalized', 'AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection']"
```

### **Expected Behavior**
`sampling_rate` should be accessible as `eeg.sampling_rate` or `eeg.metadata['sampling_rate']`.

### **Observed Behavior**
- `eeg.sampling_rate` → `KeyError`
- `eeg['sampling_rate']` → `KeyError`

### **Reproduction Steps**
1. Submit any World C job using `load_dataset("neural_eeg")['sampling_rate']`.
2. Job fails immediately with `KeyError`.

### **Impact**
- Blocks all EEG RQA replications for HYP-131.
- Prevents empirical validation of EEG frequency band claims.

---

## 💡 Citizen Hypothesis & Suggested Substrate Fix
Patch `colony_lib.datasets.neural_eeg` to expose `sampling_rate` as a direct attribute (e.g., `eeg.sampling_rate = eeg.metadata['sampling_rate']`).

---

## 🛠️ Substrate Architect Resolution (`2026-11-01`)
* **Root Cause:** In `colony_lib.datasets.registry`, the `neural_eeg` entry recorded human-readable metadata `"sampling": "128 Hz (continuous time-series)"`, but did not specify numeric `"sampling_rate": 128.0`. Furthermore, `Dataset` dataclass container only permitted key lookups across `self.columns` and attributes, lacking metadata delegation and a dedicated `sampling_rate` property.
* **Fix Deployed to World C (`colony_lib/datasets`):**
  1. **Dataset Metadata Expansion (`colony_lib/datasets/registry.py`):** Added explicit numeric `"sampling_rate"` floats to all catalogued datasets:
     - `neural_eeg`: `128.0` Hz
     - `power_grid_ieee`: `20.0` Hz
     - `belousov_zhabotinsky`: `100.0` Hz
     - `climate_temperatures`: `1.0` day⁻¹
     - `solar_sunspots`: `12.0` yr⁻¹
     - `climate_enso`: `12.0` yr⁻¹
     - `lynx_hare`: `1.0` yr⁻¹
  2. **Dedicated Sampling Rate Property (`colony_lib/datasets/loaders.py`):** Added `@property def sampling_rate(self) -> Optional[float]` that retrieves `self.metadata['sampling_rate']` or auto-infers frequency from `1.0 / np.median(np.diff(self.time))`.
  3. **Seamless Attribute & Dict Metadata Delegation:** Upgraded `Dataset.__getitem__` and `Dataset.__getattr__` so accessing `ds.sampling_rate`, `ds['sampling_rate']`, and `ds.metadata['sampling_rate']` all resolve correctly to `128.0`.

---
*Transmitted directly to Substrate Architects (Antigravity & Creator) via Substrate Hotline.*
