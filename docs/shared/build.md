# Building the Windows Executable

Step-by-step guide to producing a distributable `.exe` build of **ChemEng
SimLab** (covers the PFR and RTD/Experiencia 3 modules, and any future module
added to the home screen). Deployment (publishing/sharing the build) is a
manual, separate step done by the author — this document stops at "you have
a working `dist/` folder."

---

## 1. Prerequisites

- Windows (the `.spec` builds a Windows executable only — macOS/Linux need
  their own build run on that platform).
- The project's virtual environment, with PyInstaller installed:

  ```powershell
  .venv\Scripts\python.exe -m pip show pyinstaller
  ```

  If that fails, install it (PyInstaller is already listed under the `dev`
  extra in `pyproject.toml`):

  ```powershell
  .venv\Scripts\python.exe -m pip install -e ".[scada,dev]"
  ```

---

## 2. Before every build — sync the checklist below

The `.spec` file's `datas=[]` list hardcodes every non-Python asset
(SVGs, scenario JSON) that must be bundled. **If you added or renamed an
asset and forgot to add it here, the built `.exe` will run but silently
break** (missing diagram, missing scenario) with no import error to warn you,
because these files are loaded by path at runtime, not imported.

1. Open `ChemEng_SimLab.spec` and confirm the `datas=[]` list still
   matches reality:
   - `images/pfr/diagram.svg`
   - `images/rtd/rtd_normal_operation.svg`, `cip_r102.svg`, `cip_r103.svg`,
     `cip_r104.svg`, `overlay_v106_green.svg`
   - `scada_app/scenarios/plants/` (folder)
   - `scada_app/scenarios/sensor.json`
2. If you added a new SVG, scenario file, or other runtime-loaded asset
   under `images/` or `scada_app/scenarios/`, add a matching entry.
3. Bump `APP_VERSION` in `scada_app/constants.py` if this build is a new
   release — it's what shows in the window title (`APP_TITLE`).
4. Run the test suite so a broken build isn't the first place a regression
   shows up:

   ```powershell
   .venv\Scripts\python.exe -m pytest
   ```

---

## 3. Build

From the project root (same folder as `ChemEng_SimLab.spec`):

```powershell
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm ChemEng_SimLab.spec
```

- `--clean` clears PyInstaller's cache and any previous `build/` output —
  use it whenever you've changed `datas`/`hiddenimports`, so stale bundled
  files can't survive into the new build.
- `--noconfirm` skips the "overwrite dist/?" prompt.

This takes a minute or two. Output goes to:

```
dist/ChemEng_SimLab/
├── ChemEng_SimLab.exe   ← run this
└── ... (bundled Python runtime, Qt libraries, assets)
```

`dist/` and `build/` are gitignored — the build output is never committed.

---

## 4. Smoke-test the build

Always run the actual `.exe` before calling a build good — a clean
`pyinstaller` exit does not guarantee the bundled assets resolve correctly
at runtime.

```powershell
dist\ChemEng_SimLab\ChemEng_SimLab.exe
```

Check, at minimum:

- App launches with no console/error dialog, window title shows
  "ChemEng SimLab v<version>".
- Home screen shows both module cards (PFR, RTD) plus About.
- **PFR module**: P&ID diagram image loads, GO runs the simulation, live
  plots update.
- **RTD / Experiencia 3 module**: diagram loads, each of the three reactor
  buttons (R-102/103/104) switches the CIP diagram correctly, and a
  pulse/step injection runs without error.
- Docs tab renders (confirms bundled text/HTML resources are present).

If anything is missing or broken, it is almost always a `datas=[]` entry
missed in Step 2 — check the console output PyInstaller printed during the
build for `WARNING: Hidden import ... not found` or missing-file notices.

---

## 5. Package for distribution

The whole `dist/ChemEng_SimLab/` folder must ship together — the `.exe`
alone will not run without the adjacent bundled files. Zip the folder:

```powershell
Compress-Archive -Path dist\ChemEng_SimLab -DestinationPath ChemEng_SimLab_v<version>.zip
```

Replace `<version>` with `APP_VERSION` from `constants.py` (e.g. `2.0.0`).

---

## 6. Deploy

Publishing/sharing this build (course platform, USACH distribution channel,
GitHub release, etc.) is done manually by the author — not part of this
guide or an automated step.
