# Hotfix 2.0.1 — conductivity texts and student export

> **Status:** proposed · **Date:** 2026-10-29 · **Target:** before the 2026-2 PFR session
> **Origin:** course design review (Lab de Cinética de Reactores, PL06/PL07). The student guide follows the **code** model; the in-app texts must match it.
> **Scope:** (1) user-visible strings; (2) **one blocking code change**: the Table-tab export (§0). No change to physics, sensor model or scenarios.

## 0. BLOCKING: the export leaks internal variables

`scada_app/ui/tabs/table_tab.py::update_on_stop` stores `data_store.to_dataframe()` in `self._df`, and both **Export CSV** and **Export Excel** write that frame. `DataStore.to_dataframe()` (`engine/data_store.py`) exports **every scalar field** of `EngineSnapshot`, i.e. also:

`CA_out`, `CB_out`, `X_out` (true, noise-free outlet concentrations and conversion), `velocity`, `Q_in`, `T_setpoint`.

The Table tab itself shows only `STUDENT_COLUMNS` (`models/log_table_model.py`), and `ReadingsOverlay` is hidden "from students" (`pfr_diagram.py` ~229), so the intent is clear: the exported file should match what the student sees. As it is, a student can read `CA_out` and `X_out` straight from the CSV and skip the calibration (objective E2-P1) and the conductivity-to-concentration step.

**Fix (small):** in `_export_csv` / `_export_excel`, export only the columns of `STUDENT_COLUMNS` (with the same headers and unit scaling as the table, or at least the same columns), and keep the full frame for the Admin tab export. Suggested: build the export frame from `self._model` or select `[attr for attr, _, _ in STUDENT_COLUMNS]` from `self._df` and rename.

Related improvements (not blocking) are in `MEJORAS_PARA_REVISION_2026-10-30.md`.

## 1. Problem

The sensor model in code is

```
σ = a · C_A + b        a = 156.0 mS·cm⁻¹/(mol/L), b = 1.6 mS/cm   (scada_app/scenarios/pfr/pfr_default.json → sensors.ct101_calib_a / _b)
                       (the defaults 12.0 / 0.05 in conductivity.py's signature are not used by the PFR scenario)
C_A = residual NaOH at the reactor outlet (pfr_engine.py: self._ct101.measure(ca_out_mol_l))
```

Because `a > 0` and `C_A` falls as the reaction proceeds, **conductivity decreases with conversion**. This is also the correct physical direction (OH⁻ conducts far better than acetate).

Three user-visible texts say the opposite or are internally inconsistent:

| # | File / lines | Current text (summary) | Problem |
|---|---|---|---|
| 1 | `scada_app/ui/dialogs/sensor_dialog.py` 22–26 | "NaAc accumulates … conductivity rises with conversion. The linear calibration model (σ = A·C_A + B) converts the reading back to residual NaOH C_A." | "Rises with conversion" contradicts σ = A·C_A + B with A > 0. |
| 2 | `scada_app/ui/tabs/docs_tab.py` 284–289 | Same claim, plus "A factory calibration curve converts …" | Same contradiction. "Factory" also conflicts with the course design: students **build** the calibration (see §3). |
| 3 | `scada_app/ui/tabs/docs_tab.py` 304–307 (tip) | "Increase Qb0 to dilute the NaOH feed — watch conductivity drop **as conversion falls**. Raise T_setpoint — watch conductivity **rise** …" | Raising T increases conversion, lowers C_A and so **lowers** σ. The Qb0 tip drops σ because the feed is diluted, not because conversion falls. |

Related, lower priority:

| # | File / lines | Note |
|---|---|---|
| 4 | `docs_tab.py` 143–147 and `about_tab.py` 89–92 | "NaAc … is electrically conductive, enabling real-time conversion monitoring". True but incomplete: it is the **loss of OH⁻** that dominates the signal. Suggest rewording (see §2). |

## 2. Proposed replacement text

**sensor_dialog.py (description box, second paragraph):**

> As the saponification reaction proceeds, NaOH is consumed and replaced by sodium acetate (NaAc). OH⁻ conducts much better than acetate, so the conductivity **decreases** with conversion. Within its valid range, the relation between conductivity and residual NaOH concentration is approximately linear (σ = A · C_A + B). The operator builds that calibration from reference measurements and uses it to convert the reading back into C_A at the reactor outlet.

**docs_tab.py, CT-101 narrative:**

> You cannot measure concentration directly and continuously in real time. Instead, CT-101 measures the electrical conductivity of the outlet stream. As the saponification proceeds, NaOH is consumed and replaced by sodium acetate; since OH⁻ conducts much better than acetate, conductivity falls with conversion. Within the valid range the response is approximately linear in the residual NaOH concentration C_A, so a calibration curve converts the reading back to C_A at the reactor outlet.

**docs_tab.py, tip:** (verify the behaviour in the running app before merging)

> Increase Qb0 to dilute the NaOH feed — watch the conductivity drop because the inlet NaOH concentration falls. Raise T_setpoint — watch the conductivity decrease as the reaction consumes more NaOH.

**docs_tab.py 143–147 / about_tab.py 89–92:** replace "is electrically conductive, enabling real-time conversion monitoring" with "changes the ionic composition of the stream, which makes conductivity a convenient indicator of conversion".

## 3. Decision needed (course owner): visible calibration constants

`docs_tab.py` 291–295 prints the numeric values `A = {CT101_CALIB_A}` and `B = {CT101_CALIB_B}` (from `constants.py`, which reads `pfr_default.json`).

The 2026-2 design asks students to **prepare their own conductivity calibration curve with the simulator** (objective E2-P1). Showing the true A and B in the Docs tab lets them skip it.

Options:

1. **Hide A and B** (replace with "determined by the operator's calibration"), and keep `CT101_NOISE_STD` hidden too. Recommended: consistent with `sensor_dialog.py`, which already shows "factory-calibrated" without numbers.
2. Keep them and treat them as "manufacturer's nominal values" to compare against the student's own fit.

Pending decision by the course owner.

## 4. Other checks before handing the app to students

- [ ] Run the app and confirm the direction of σ against Qb0 and T_setpoint (tip, §1 #3), and that the "Valid range 0 – 0.1 mol/L" in `sensor_dialog.py::_calibration_box` still covers the normal operating range of the default scenario.
- [ ] Admin tab password (`scada_app/ui/tabs/admin_tab.py`): confirm it is not the default and that hidden parameters are not exposed elsewhere.
- [ ] Search the remaining strings for "factory" and "rises with conversion".

## 5. Release steps

1. Edit the strings above (no logic change).
2. `scada_app/constants.py`: `APP_VERSION = "2.0.1"`.
3. `CHANGELOG.md`: new section.
   ```
   ## [2.0.1] — <date>
   ### Fixed
   - CT-101 texts (sensor dialog, Docs tab, About tab) now state that conductivity
     decreases with conversion, consistent with the σ = a·C_A + b model; tips corrected.
   ```
4. Run `pytest` (no test should change) and rebuild (`docs/shared/build.md`).
5. Notify the course owner so the student guide can reference v2.0.1.
