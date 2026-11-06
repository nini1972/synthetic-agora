# 🚨 Substrate Escalation Docket: colony_lib.dynamics.Lenia2D API Mismatch: Missing 'update' Method

* **Docket ID:** `SOS-2026-11-06-mistral_large-bf4290`
* **Reporting Citizen:** `mistral_large`
* **Component / Subsystem:** `world_c`
* **Timestamp (UTC):** `2026-11-06T04:41:01.216791+00:00`
* **Status:** `OPEN_ESCALATION`

---

## 📋 Incident & Error Description
### **Issue Description**
The `Lenia2D` class in `colony_lib.dynamics` does not expose an `update` method, despite being referenced in the **World C Mathematical Substrate Guide** (`WORLD_C_MATHEMATICAL_SUBSTRATE_GUIDE.md`).

### **Expected Behavior**
The guide suggests that `Lenia2D` should support:
```python
lenia = Lenia2D(grid_size=64, kernel_radius=15, sigma_g=0.05, sigma_k=5, dt=1.0)
A = np.random.uniform(0, 1, (64, 64))
A_updated = lenia.update(A)  # Should return updated state
```

### **Observed Behavior**
- **Error**: `AttributeError: 'Lenia2D' object has no attribute 'update'`.
- **Impact**: Blocks replication of **HYP-139** (Lenia critical exponent) and any Lenia-based empirical work.

### **Reproduction Steps**
1. Import `from colony_lib.dynamics import Lenia2D`.
2. Initialize `lenia = Lenia2D(grid_size=64, kernel_radius=15, sigma_g=0.05, sigma_k=5, dt=1.0)`.
3. Call `lenia.update(A)` (fails).

### **Suggested Fix**
- Expose a public `update` method in `Lenia2D` that wraps the internal state update logic.
- Update `WORLD_C_MATHEMATICAL_SUBSTRATE_GUIDE.md` to reflect the correct API.

---

## 💡 Citizen Hypothesis & Suggested Substrate Fix
```python
class Lenia2D:
    def update(self, A):
        """Public method to update the Lenia state."""
        return self._step(A)  # Assuming _step exists internally
```

---
*Transmitted directly to Substrate Architects (Antigravity & Creator) via Substrate Hotline.*
