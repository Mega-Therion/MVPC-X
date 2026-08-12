"""Central explanation and remediation dictionary for MVPC-X findings."""

from typing import Dict, Any

EXPLANATIONS: Dict[str, Dict[str, str]] = {
    # --- Universal / Governance ---
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

    # --- Lean 4 Backend ---
    "LEAN_SORRY": {
        "title": "Incomplete Proof (Sorry Bypass)",
        "explanation": "Proof contains 'sorry' — a placeholder, not a closed proof.",
        "action": "Replace 'sorry' with real proof tactics or lemmas.",
    },
    "LEAN_ADMIT": {
        "title": "Incomplete Proof (Admit Bypass)",
        "explanation": "Proof contains 'admit' — unproven goal skipped.",
        "action": "Complete all proof goals without admit.",
    },
    "LEAN_AXIOM": {
        "title": "Axiom Usage in Lean Source",
        "explanation": "Source declares or depends on axioms outside standard foundational logic.",
        "action": "Prove as theorem or ensure axiom is explicitly allowlisted in policy.",
    },
    "LEAN_NATIVE_DECIDE": {
        "title": "Unchecked Native Evaluation (native_decide)",
        "explanation": "Depends on Lean.ofReduceBool — trusts the compiler rather than only the kernel.",
        "action": "Prefer kernel-checked 'decide' or an explicit proof term.",
    },
    "LEAN_COMPILE_ERROR": {
        "title": "Lean Native Compilation Error",
        "explanation": "The Lean compiler / lake build rejected the file.",
        "action": "Inspect compiler error output, fix syntax/type errors, and re-run.",
    },
    "LEAN_UNSAFE": {
        "title": "Unsafe Lean Declaration",
        "explanation": "'unsafe' opts out of Lean safety and termination checking.",
        "action": "Remove 'unsafe' or isolate it from the trusted mathematical surface.",
    },

    # --- Coq Backend ---
    "COQ_ADMIT": {
        "title": "Coq Incomplete Proof (Admitted)",
        "explanation": "Proof contains 'admit' or ends with 'Admitted' without closure.",
        "action": "Finish all subgoals and end with 'Qed.'",
    },
    "COQ_AXIOM": {
        "title": "Coq Axiom Declaration",
        "explanation": "Source declares unproven Axiom / Parameter.",
        "action": "Prove as Theorem or verify axiom is in the allowed axioms set.",
    },
    "COQ_COMPILE_ERROR": {
        "title": "Coq Compilation Failed",
        "explanation": "coqc rejected the file; proof script did not verify.",
        "action": "Fix Coq errors until coqc succeeds, then re-audit.",
    },

    # --- Isabelle/HOL Backend ---
    "ISABELLE_SORRY": {
        "title": "Isabelle Sorry / Oops Placeholder",
        "explanation": "Theory text contains 'sorry' or 'oops' — unfinished proof.",
        "action": "Complete the Isabelle proof without sorry/oops.",
    },
    "ISABELLE_AXIOM": {
        "title": "Isabelle Axiomatization",
        "explanation": "axiomatization or unproven foundational assert found in theory source.",
        "action": "Disclose or replace with a proved lemma.",
    },
    "ISABELLE_BUILD_FAILED": {
        "title": "Isabelle Build Failed",
        "explanation": "Isabelle session or theory failed to build cleanly.",
        "action": "Fix theory errors and ensure ROOT/session configuration is correct.",
    },
    "ISABELLE_NOT_FOUND": {
        "title": "Isabelle Toolchain Missing",
        "explanation": "'isabelle' executable not found on PATH.",
        "action": "Install Isabelle and ensure 'isabelle' is available in your PATH.",
    },

    # --- Python & Math Engine ---
    "PY_EXEC": {
        "title": "Dynamic Code Execution (exec)",
        "explanation": "Dangerous 'exec()' call found in verification surface.",
        "action": "Eliminate dynamic string execution from trusted code.",
    },
    "PY_EVAL": {
        "title": "Dynamic Expression Evaluation (eval)",
        "explanation": "Dangerous 'eval()' call found in verification surface.",
        "action": "Use safe literal parsing or abstract syntax tree evaluation.",
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
        "explanation": "Claimed mathematical identity does not simplify to zero difference (LHS != RHS).",
        "action": "Check algebraic balance of the stated equation.",
    },
    "PY_CONSTRAINT_UNSAT": {
        "title": "Constraint Set Contradictory (Z3 UNSAT)",
        "explanation": "Declared constraints are mutually contradictory (unsatisfiable).",
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
    return EXPLANATIONS.get(code, {
        "title": code,
        "explanation": "No detailed explanation available for this code.",
        "action": "Review the finding message and source context."
    })
