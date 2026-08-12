"""Central explanation and remediation dictionary for MVPC-X findings."""

from typing import Dict

EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "SYSTEM_INTEGRITY_FAILURE": {
        "title": "Verifier Self-Integrity Failure",
        "explanation": (
            "MVPC-X fingerprints its own installed package before ingesting an artifact, "
            "optionally mid-run, and again after processing. The fingerprint changed — "
            "the verifier on disk is not the same system that started the run. "
            "A malicious or concurrent modification may have corrupted MVPC-X."
        ),
        "action": (
            "Stop trusting this host install. Reinstall MVPC-X from a known-good source, "
            "run `mvpc integrity --verify-twice`, and re-audit in a clean environment."
        ),
    },
    "ARTIFACT_MUTATION": {
        "title": "Artifact Changed During Audit",
        "explanation": (
            "The input file's SHA-256 after the run does not match the hash taken before "
            "backends ran. Something modified the artifact mid-flight."
        ),
        "action": "Re-run against a stable copy; avoid editing files during audit.",
    },
    "INTAKE_BLOCKED": {
        "title": "Intake Security Rejected Path",
        "explanation": (
            "The path failed pre-ingest guards (missing file, symlink policy, size limit, "
            "or blocked executable-like extension). Backends never ran."
        ),
        "action": "See intake reasons; use a regular source file under size limits. For symlinks, pass --allow-symlinks only if you trust the link.",
    },
    "INTAKE_WARNING": {
        "title": "Intake Warning",
        "explanation": "The path was allowed but has suspicious properties (e.g. world-writable).",
        "action": "Harden file permissions or placement before treating results as high assurance.",
    },
    "NO_BACKEND": {
        "title": "No Verification Backend",
        "explanation": "No registered backend claimed this artifact. Nothing machine-checked it.",
        "action": "Add a backend for this file type or rename/export to a supported format.",
    },
    "AI_PROVENANCE_MISSING": {
        "title": "Missing AI Provenance",
        "explanation": "This artifact is marked AI-touched but has no provenance record (model, prompt hash, time).",
        "action": "Attach an AIProvenance block before treating the artifact as verified.",
    },
    "HUMAN_ATTESTATION_MISSING": {
        "title": "No Human Attestation",
        "explanation": "Machine checks ran, but no human has attested the witness. Policy requires both.",
        "action": "Run 'mvpc attest <witness.json> --signer <name>' after reviewing the witness report.",
    },
    "COVERAGE_DEGRADED": {
        "title": "Degraded Coverage",
        "explanation": "One or more verification engines could not run. A clean-looking report may be incomplete.",
        "action": "Install missing tools (e.g., Lean, Coq, Isabelle, Z3, SymPy) and re-run.",
    },
    "HASH_MISMATCH": {
        "title": "Artifact Hash Mismatch",
        "explanation": "The file changed since provenance was recorded. The audit no longer binds to these bytes.",
        "action": "Re-run full audit and refresh provenance on the current file.",
    },
    "STATIC_ERROR": {
        "title": "Static Analysis Error",
        "explanation": "The static analyzer hit an unexpected error while reading or parsing the artifact.",
        "action": "Check file encoding/permissions and re-run; report a bug if it persists.",
    },
    "NATIVE_ERROR": {
        "title": "Native Tool Error",
        "explanation": "A native toolchain invocation failed unexpectedly (not a clean compile error).",
        "action": "Inspect the tool installation and environment, then re-run.",
    },
    "LEAN_SORRY": {
        "title": "Incomplete Proof (Sorry Bypass)",
        "explanation": "Proof contains 'sorry' or 'admit' — a placeholder, not a closed proof.",
        "action": "Replace sorry/admit with real proof tactics or lemmas.",
    },
    "LEAN_ADMIT": {
        "title": "Incomplete Proof (Admit Bypass)",
        "explanation": "Proof contains 'admit' — unproven goal skipped.",
        "action": "Complete all proof goals without admit.",
    },
    "LEAN_AXIOM": {
        "title": "Bare Axiom Declaration",
        "explanation": "Source declares a new axiom with no proof — unproven foundation smuggled into the file.",
        "action": "Prove as a theorem or explicitly disclose and allowlist the axiom in policy.",
    },
    "LEAN_AXIOM_SMUGGLE": {
        "title": "Illegal Assumption (Axiom Smuggling)",
        "explanation": "Lean kernel reports dependence on a non-allowlisted axiom (beyond propext/Quot.sound/Classical.choice).",
        "action": "Remove the axiom dependency or expand the allowlist only with explicit disclosure.",
    },
    "LEAN_KERNEL_SORRY_AX": {
        "title": "Kernel-Confirmed Sorry (sorryAx)",
        "explanation": "The Lean kernel itself reports sorryAx — the proof does not close.",
        "action": "Locate the real gap and complete the proof with kernel-checked tactics.",
    },
    "LEAN_NATIVE_DECIDE": {
        "title": "Unchecked Native Evaluation (native_decide)",
        "explanation": "Depends on Lean.ofReduceBool / native_decide — trusts compiler reduction, not only the kernel.",
        "action": "Prefer kernel-checked decide or an explicit proof term.",
    },
    "LEAN_COMPILE_ERROR": {
        "title": "Lean Native Compilation Error",
        "explanation": "The Lean compiler / lake env rejected the file or failed before axiom audit.",
        "action": "Inspect compiler error output, fix syntax/type errors, and re-run.",
    },
    "LEAN_UNSAFE": {
        "title": "Unsafe Lean Declaration",
        "explanation": "'unsafe' opts out of Lean safety and termination checking.",
        "action": "Remove unsafe or isolate it from the trusted mathematical surface.",
    },
    "LEAN_TAUTOLOGY": {
        "title": "Proving Nothing (Tautological Bypass)",
        "explanation": "Theorem reduces to True via trivial/rfl/decide/True.intro — no mathematical content.",
        "action": "Restate a nontrivial claim and prove that.",
    },
    "LEAN_Z3_VACUOUS": {
        "title": "Vacuous Truth (Contradictory Hypotheses)",
        "explanation": "Z3 proved binder hypotheses unsatisfiable; anything follows vacuously.",
        "action": "Fix contradictory hypotheses in the theorem binders.",
    },
    "LEAN_SYMPY_MISMATCH": {
        "title": "Equation Drift (Symbolic Mismatch)",
        "explanation": "SymPy could not verify LHS equals RHS for a bare equation theorem target.",
        "action": "Check algebraic balance of the stated equation.",
    },
    "LEAN_KERNEL_NEVER_RAN": {
        "title": "Kernel Verification Never Happened",
        "explanation": "Native Lean kernel did not successfully audit axioms.",
        "action": "Install/repair Lean toolchain and re-run.",
    },
    "LEAN_NO_LAKE_PROJECT": {
        "title": "No Lake Project Detected",
        "explanation": "No lakefile near the target; Mathlib imports may fail under bare lean.",
        "action": "Run inside a Lake project when the file has external imports.",
    },
    "COQ_ADMIT": {
        "title": "Coq Incomplete Proof (Admitted)",
        "explanation": "Proof contains admit or ends with Admitted without closure.",
        "action": "Finish all subgoals and end with Qed.",
    },
    "COQ_AXIOM": {
        "title": "Coq Axiom Declaration",
        "explanation": "Source declares unproven Axiom / Parameter.",
        "action": "Prove as Theorem or verify axiom is allowlisted.",
    },
    "COQ_COMPILE_ERROR": {
        "title": "Coq Compilation Failed",
        "explanation": "coqc rejected the file; proof script did not verify.",
        "action": "Fix Coq errors until coqc succeeds, then re-audit.",
    },
    "ISABELLE_SORRY": {
        "title": "Isabelle Sorry / Oops Placeholder",
        "explanation": "Theory text contains sorry or oops — unfinished proof.",
        "action": "Complete the Isabelle proof without sorry/oops.",
    },
    "ISABELLE_AXIOM": {
        "title": "Isabelle Axiomatization",
        "explanation": "axiomatization found in theory source.",
        "action": "Disclose or replace with a proved lemma.",
    },
    "ISABELLE_BUILD_FAILED": {
        "title": "Isabelle Build Failed",
        "explanation": "Isabelle session or theory failed to build cleanly.",
        "action": "Fix theory errors and ensure ROOT/session configuration is correct.",
    },
    "ISABELLE_NOT_FOUND": {
        "title": "Isabelle Toolchain Missing",
        "explanation": "isabelle executable not found on PATH.",
        "action": "Install Isabelle and ensure isabelle is available in PATH.",
    },
    "PY_EXEC": {
        "title": "Dynamic Code Execution (exec)",
        "explanation": "Dangerous exec() call found in verification surface.",
        "action": "Eliminate dynamic string execution from trusted code.",
    },
    "PY_EVAL": {
        "title": "Dynamic Expression Evaluation (eval)",
        "explanation": "Dangerous eval() call found in verification surface.",
        "action": "Use safe literal parsing or AST evaluation.",
    },
    "PY_OS_SYSTEM": {
        "title": "System Shell Execution",
        "explanation": "os.system() or shell execution detected.",
        "action": "Avoid arbitrary shell spawning in mathematical artifacts.",
    },
    "PY_SHELL_TRUE": {
        "title": "Subprocess Shell Injection Risk",
        "explanation": "subprocess called with shell=True.",
        "action": "Pass command arguments as a list without shell=True.",
    },
    "PY_SYNTAX_ERROR": {
        "title": "Python Syntax Error",
        "explanation": "File failed to compile under Python interpreter.",
        "action": "Fix syntax errors.",
    },
    "PY_IDENTITY_FAIL": {
        "title": "Symbolic Identity Failed (SymPy)",
        "explanation": "Claimed mathematical identity does not simplify to zero difference.",
        "action": "Check algebraic balance of the stated equation.",
    },
    "PY_CONSTRAINT_UNSAT": {
        "title": "Constraint Set Contradictory (Z3 UNSAT)",
        "explanation": "Declared constraints are mutually contradictory.",
        "action": "Fix the binder hypotheses or constraint definitions.",
    },
    "PY_NUMERIC_DRIFT": {
        "title": "Numeric Sanity Drift (NumPy)",
        "explanation": "NumPy spot-check disagreed with the claimed relation on sample points.",
        "action": "Inspect domains, singularities, and claimed numerical equivalence.",
    },
    "PY_PARSE_SKIP": {
        "title": "Math Claim Parse Skip",
        "explanation": "Could not parse claimed mathematical identity or constraint.",
        "action": "Simplify notation or format as standard Python/SymPy expression.",
    },
    "GENERIC_PLACEHOLDER": {
        "title": "Placeholder / TODO in Artifact",
        "explanation": "TODO/FIXME/HACK or proof-escape tokens found in artifact.",
        "action": "Remove placeholders before publishing verification.",
    },
}


def get_explanation(code: str) -> Dict[str, str]:
    """Retrieve explanation metadata for a given finding code."""
    return EXPLANATIONS.get(
        code,
        {
            "title": code,
            "explanation": "No detailed explanation available for this code.",
            "action": "Review the finding message and source context.",
        },
    )
