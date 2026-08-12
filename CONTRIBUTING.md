# Contributing to MVPC-X

Thank you for your interest in contributing to **MVPC-X**! 

MVPC-X is built on the principle that verification infrastructure must be open, transparent, and sovereign. We believe that preventing the spread of manufactured certainty requires collective, open-source defense across mathematics, software engineering, and AI safety.

---

## The Foundational Covenant

Before contributing, please read and internalize our core covenant:

1. **MVP-C must never manufacture certainty.**
2. **Absence of detected problems is not evidence of truth.**
3. **Every assurance claim must be strictly proportional to the verification actually performed.**
4. **Humans provide meaning. Machines provide mechanical assurance.**
5. **Neither is allowed to silently substitute for the other.**

Any PR or feature that creates an illusion of verification without rigorous mechanical proof violates this covenant and will be rejected.

---

## Ways to Contribute

### 1. Adding New Verification Backends
We are actively seeking backends for:
- **Isabelle / HOL** (`.thy`)
- **Agda** (`.agda`)
- **Z3 / SMT-LIB** (`.smt2`)
- **Rust / Kani / Miri / Creusot**
- **TLA+ / PlusCal**
- **SymPy / Computer Algebra Systems**

To add a backend:
1. Inherit from `mvpc.backends.base.VerificationBackend`.
2. Implement `name()`, `supported_extensions()`, `supports()`, `check_native_available()`, `run_static_analysis()`, `run_native_verification()`, and `audit()`.
3. Register the backend in `mvpc.backends.registry.get_default_registry()`.
4. Add comprehensive test fixtures in `tests/fixtures/` and tests in `tests/test_backends.py`.

### 2. Enhancing Policy Rules & Static Analysis
Help us detect subtle proof escapes, smuggled axioms, macro expansions, or unsafe patterns across Lean, Coq, Python, and other languages.

### 3. CI/CD & Integration Tooling
- GitHub Actions integrations
- Pre-commit hooks
- Editor LSP integrations (VS Code, Neovim)

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Mega-Therion/MVPC-X.git
cd MVPC-X

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

---

## Code Quality Standards

- **Zero Non-Stdlib Core Dependencies:** The core `mvpc` package must remain lightweight, fast, and completely runnable without external Python packages.
- **Type Annotations:** All functions and methods must have full type hints.
- **Explicit Uncertainty:** Functions must explicitly report what checks could *not* be performed in the `CoverageReport`.

---

## Submitting Pull Requests

1. Fork the repo and create a descriptive branch: `git checkout -b feat/isabelle-backend`.
2. Ensure all tests pass (`pytest`).
3. Add new unit tests for any new behavior or backend.
4. Open a Pull Request with a clear explanation of what was implemented, what was verified, and how it aligns with the Covenant.
