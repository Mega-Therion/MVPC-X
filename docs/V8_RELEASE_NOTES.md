# MVPC-X v8.0.0

## Priorities completed in this release train

1. **Hardening wired** into `hardened_pipeline.py` (sign manifests, optional multi-engine vote, CAS double-check, CPS interval/rate, transitive scan, repair loop).
2. **Kernel backend adapters** — `kernel_backends.py` invokes real `lean`/`lake`, `coqc`, `isabelle`, `dafny` when on PATH via sandboxed subprocess; otherwise falls back to heuristic scan with explicit `driver_mode`.
3. **CAS Z3 fallback** when SymPy fails (`hardening/cas_doublecheck.py`).
4. **CLI bridge** — `python -m mvpc.cli_bridge` exposes unified nexus + harden commands; documents integration into main `mvpc` CLI.
5. **CI** upgraded workflow (pytest multi-version, ruff optional).
6. **Version** pinned at `8.0.0`.

## Still environment-dependent

- Branch protection must be enabled in GitHub repo settings (API not always available).
- OS cgroups require container runtime; quotas remain best-effort in-process + subprocess timeouts.
- Full Pantograph/SerAPI/PIDE remain optional integrations.
