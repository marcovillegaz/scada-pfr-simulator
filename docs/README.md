# Documentation Index

Docs are organized module-first: shared/module-agnostic material lives in
`shared/`, per-module material lives in `modules/<mod>/`. See
[shared/CONVENTION.md](shared/CONVENTION.md) for the reasoning behind this
split and the full module convention new code should follow.

```
docs/
  README.md                 this file
  NEXT_STEPS.md              deferred follow-ups / backlog
  ROADMAP_V2.md              larger items intentionally deferred to a v2 pass
  documentacion_es.md        student manual (Spanish) -- install, run, per-module usage
  shared/
    CONVENTION.md             the module convention (library-by-role / app-by-experience)
    frontend.md               UI architecture for the whole app (shell + both modules)
    quickstart.md             script-mode (batch) API usage, for examples/
    build.md                  PyInstaller build checklist
  modules/
    pfr/
      backend.md              PFR physics package structure, class reference
      math.md                 PFR PDE model, kinetics, Method of Lines
      simulation_efficiency.md  PFR sim-loop performance notes
    rtd/
      fundamentals.md          RTD theory: E(t)/moments, one-parameter models,
                                the hidden compartment-network ground truth
      curva_E_explicativo.html interactive E-curve explainer (session 1)
```

## Where to start

- **Building or running the app**: [shared/build.md](shared/build.md), root
  [README.md](../README.md).
- **Understanding the UI**: [shared/frontend.md](shared/frontend.md).
- **Understanding PFR physics**: [modules/pfr/math.md](modules/pfr/math.md),
  [modules/pfr/backend.md](modules/pfr/backend.md).
- **Understanding RTD physics**:
  [modules/rtd/fundamentals.md](modules/rtd/fundamentals.md).
- **Adding a new module**: [shared/CONVENTION.md](shared/CONVENTION.md) §6
  has the checklist.
- **Using the physics library standalone** (script mode, no SCADA UI):
  [shared/quickstart.md](shared/quickstart.md).
- **What's planned / deferred**: [NEXT_STEPS.md](NEXT_STEPS.md),
  [ROADMAP_V2.md](ROADMAP_V2.md).
- **Handing this to a student**: [documentacion_es.md](documentacion_es.md).

## A note on `shared/frontend.md`

It covers the shell (routing, timer pattern) *and* both modules' UI in one
document rather than being split per module. The app's actual structure
made that the right call: one `MainWindow` hosts swappable per-module
workspaces that share the same tab/dialog/widget patterns, and the
cross-references between shell and workspace sections would fragment badly
across files. Module-specific frontend notes that don't fit that shared
narrative can still go in `modules/<mod>/frontend.md` later if a module
needs one.
