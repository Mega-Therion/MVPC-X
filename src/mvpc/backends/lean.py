"""Lean 4 verification backend — MVP-C gold-standard depth.

Static + native multi-engine audit:
1. Comment-aware text lints (sorry/admit, bare axiom, unsafe, native_decide, tautology)
2. Environment probe (lean/lake/mathlib/lakefile)
3. Native kernel axiom extraction via lake env lean / lean + #print axioms
4. Optional Z3 vacuous-hypothesis check on scalar binder bounds
5. Optional SymPy algebraic identity check on bare equation targets

Core remains stdlib-only; sympy/z3 are optional extras.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from shutil import which
from typing import Any, Dict, List, Optional, Tuple

from mvpc.backends.base import VerificationBackend
from mvpc.evidence import Evidence, EvidenceType
from mvpc.explanations import get_explanation
from mvpc.hashing import hash_file
from mvpc.trust import CoverageReport, Finding, Severity

try:
    import z3

    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

try:
    import sympy as sp
    import sympy.parsing.sympy_parser as sp_parse

    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


APPROVED_AXIOMS = frozenset({"propext", "Quot.sound", "Classical.choice"})
SPECIAL_AXIOMS = {
    "sorryAx": "LEAN_KERNEL_SORRY_AX",
    "Lean.ofReduceBool": "LEAN_NATIVE_DECIDE",
}

UNICODE_MAP = {
    "\u211d\u22650": "Real",
    "\u211d\u22640": "Real",
    "\u211d": "Real",
    "\u2115": "Nat",
    "\u2124": "Int",
    "\u211a": "Rat",
    "\u2102": "Complex",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b3": "gamma",
    "\u03b4": "delta",
    "\u03b5": "epsilon",
    "\u03bb": "lambda",
    "\u03bc": "mu",
    "\u03c0": "pi",
    "\u03c3": "sigma",
    "\u03c6": "phi",
    "\u03c8": "psi",
    "\u03c9": "omega",
    "\u2211": "Sum",
    "\u220f": "Product",
    "\u222b": "Integral",
    "\u2202": "Derivative",
    "\u221e": "oo",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u2227": " and ",
    "\u2228": " or ",
    "\u00ac": "not ",
    "\u22c5": "*",
    "\u2022": "*",
    "\u2191": "",
    "\u21a6": ",",
    "\u2243": "==",
}
UNICODE_KEYS = sorted(UNICODE_MAP.keys(), key=len, reverse=True)

DECL_RE = re.compile(
    r"(?m)^(?:protected\s+|noncomputable\s+|private\s+)?(?:theorem|lemma)\s+"
    r"([A-Za-z_][A-Za-z0-9_'!?]*)"
)
AXIOM_RE = re.compile(
    r"(?m)^(?:protected\s+|noncomputable\s+|private\s+)?axiom\s+"
    r"([A-Za-z_][A-Za-z0-9_'!?]*)"
)
UNSAFE_RE = re.compile(
    r"(?m)^\s*unsafe\s+(?:def|theorem|instance|abbrev)\s+"
    r"([A-Za-z_][A-Za-z0-9_'!?]*)"
)

OPEN = {"(": ")", "[": "]", "{": "}"}
CLOSE = {v: k for k, v in OPEN.items()}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(code: str, severity: Severity, message: str, system: str, line: int = 0) -> Finding:
    exp = get_explanation(code)
    return Finding(
        code=code,
        severity=severity,
        message=message,
        system=system,
        line=line or None,
        remediation=exp.get("action"),
    )


def strip_lean_comments(content: str) -> str:
    """Blank comment bodies; preserve newlines/offsets for line numbers."""
    out = list(content)
    i, n, depth = 0, len(content), 0
    while i < n:
        if depth > 0:
            if i + 1 < n and content[i : i + 2] == "/-":
                depth += 1
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if i + 1 < n and content[i : i + 2] == "-/":
                depth -= 1
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if content[i] != "\n":
                out[i] = " "
            i += 1
            continue
        if i + 1 < n and content[i : i + 2] == "/-":
            depth = 1
            out[i] = out[i + 1] = " "
            i += 2
            continue
        if i + 1 < n and content[i : i + 2] == "--":
            j = i
            while j < n and content[j] != "\n":
                out[j] = " "
                j += 1
            i = j
            continue
        i += 1
    return "".join(out)


def apply_unicode_map(text: str) -> str:
    for u in UNICODE_KEYS:
        text = text.replace(u, UNICODE_MAP[u])
    return text


def find_declarations(stripped: str) -> List[Dict[str, Any]]:
    """Depth-aware theorem/lemma binder + statement extraction."""
    decls: List[Dict[str, Any]] = []
    for m in DECL_RE.finditer(stripped):
        name = m.group(1)
        cursor = m.end()
        depth = 0
        stack: List[str] = []
        top_colons: List[int] = []
        body_marker: Optional[int] = None
        i = cursor
        n = len(stripped)
        while i < n:
            ch = stripped[i]
            if ch in OPEN:
                stack.append(ch)
                depth += 1
                i += 1
                continue
            if ch in CLOSE:
                if stack and stack[-1] == CLOSE[ch]:
                    stack.pop()
                    depth = max(0, depth - 1)
                i += 1
                continue
            if depth == 0:
                if ch == ":" and i + 1 < n and stripped[i + 1] == "=":
                    body_marker = i
                    break
                if ch == ":" and not (i > 0 and stripped[i - 1] == ":") and not (
                    i + 1 < n and stripped[i + 1] == ":"
                ):
                    top_colons.append(i)
            i += 1
        if body_marker is None or not top_colons:
            continue
        stmt_start = top_colons[-1] + 1
        decls.append(
            {
                "name": name,
                "decl_start": m.start(),
                "statement_start": stmt_start,
                "statement": stripped[stmt_start:body_marker].strip(),
                "binders": stripped[cursor : top_colons[-1]].strip(),
            }
        )
    return decls


def find_paren_groups(text: str) -> List[str]:
    groups: List[str] = []
    depth = 0
    start: Optional[int] = None
    stack: List[str] = []
    for i, ch in enumerate(text):
        if ch in OPEN:
            if depth == 0:
                start = i
            stack.append(ch)
            depth += 1
        elif ch in CLOSE:
            if stack and stack[-1] == CLOSE[ch]:
                stack.pop()
                depth -= 1
                if depth == 0 and start is not None:
                    groups.append(text[start : i + 1])
                    start = None
            else:
                stack.clear()
                depth = 0
                start = None
    return groups


def line_of(text: str, offset: int) -> int:
    return text[: max(0, offset)].count("\n") + 1


def probe_environment(project_dir: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "lean_found": which("lean") is not None,
        "lake_found": which("lake") is not None,
        "lean_version": None,
        "has_lake_project": False,
        "mathlib_present": False,
    }
    search = [project_dir]
    parent = os.path.dirname(project_dir)
    if parent and parent != project_dir:
        search.append(parent)
    for d in search:
        if os.path.exists(os.path.join(d, "lakefile.lean")) or os.path.exists(
            os.path.join(d, "lakefile.toml")
        ):
            info["has_lake_project"] = True
            manifest = os.path.join(d, "lake-manifest.json")
            if os.path.exists(manifest):
                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        if "mathlib" in f.read().lower():
                            info["mathlib_present"] = True
                except OSError:
                    pass
            packages = os.path.join(d, ".lake", "packages")
            if os.path.isdir(packages):
                try:
                    if any("mathlib" in n.lower() for n in os.listdir(packages)):
                        info["mathlib_present"] = True
                except OSError:
                    pass
    if info["lean_found"]:
        try:
            r = subprocess.run(
                ["lean", "--version"], capture_output=True, text=True, timeout=10
            )
            info["lean_version"] = (r.stdout or r.stderr or "").strip() or None
        except Exception:
            pass
    return info


def ast_to_z3(node: ast.AST, local_env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return ast_to_z3(node.body, local_env)
    if isinstance(node, ast.BoolOp):
        vals = [ast_to_z3(v, local_env) for v in node.values]
        if isinstance(node.op, ast.And):
            return z3.And(*vals)
        if isinstance(node.op, ast.Or):
            return z3.Or(*vals)
    if isinstance(node, ast.UnaryOp):
        v = ast_to_z3(node.operand, local_env)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return v
        if isinstance(node.op, ast.Not):
            return z3.Not(v)
    if isinstance(node, ast.BinOp):
        l, r = ast_to_z3(node.left, local_env), ast_to_z3(node.right, local_env)
        if isinstance(node.op, ast.Add):
            return l + r
        if isinstance(node.op, ast.Sub):
            return l - r
        if isinstance(node.op, ast.Mult):
            return l * r
        if isinstance(node.op, ast.Div):
            return l / r
        if isinstance(node.op, ast.Pow):
            return l**r
    if isinstance(node, ast.Compare):
        left = ast_to_z3(node.left, local_env)
        results = []
        curr = left
        for op, comp in zip(node.ops, node.comparators):
            right = ast_to_z3(comp, local_env)
            if isinstance(op, ast.Eq):
                results.append(curr == right)
            elif isinstance(op, ast.NotEq):
                results.append(curr != right)
            elif isinstance(op, ast.Lt):
                results.append(curr < right)
            elif isinstance(op, ast.LtE):
                results.append(curr <= right)
            elif isinstance(op, ast.Gt):
                results.append(curr > right)
            elif isinstance(op, ast.GtE):
                results.append(curr >= right)
            curr = right
        return results[0] if len(results) == 1 else z3.And(*results)
    if isinstance(node, ast.Name):
        if node.id in ("True", "True_"):
            return True
        if node.id in ("False", "False_"):
            return False
        if node.id not in local_env:
            local_env[node.id] = z3.Real(node.id)
        return local_env[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    raise ValueError(type(node).__name__)


class LeanBackend(VerificationBackend):
    def name(self) -> str:
        return "Lean 4"

    def supported_extensions(self) -> List[str]:
        return [".lean"]

    def supports(self, path: str) -> bool:
        return path.lower().endswith(".lean")

    def check_native_available(self) -> bool:
        return which("lean") is not None or which("lake") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        path = os.path.abspath(path)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            findings.append(
                _finding("STATIC_ERROR", Severity.WARNING, str(e), "LeanStatic")
            )
            return findings, []

        stripped = strip_lean_comments(content)

        for m in re.finditer(r"\b(sorry|admit)\b", stripped):
            findings.append(
                _finding(
                    "LEAN_SORRY",
                    Severity.VIOLATION,
                    f"Use of '{m.group(0)}' placeholder detected",
                    "LeanStatic",
                    line_of(stripped, m.start()),
                )
            )

        for m in AXIOM_RE.finditer(stripped):
            findings.append(
                _finding(
                    "LEAN_AXIOM",
                    Severity.VIOLATION,
                    f"Bare axiom declared: {m.group(1)}",
                    "LeanStatic",
                    line_of(stripped, m.start()),
                )
            )

        for m in UNSAFE_RE.finditer(stripped):
            findings.append(
                _finding(
                    "LEAN_UNSAFE",
                    Severity.VIOLATION,
                    f"unsafe declaration: {m.group(1)}",
                    "LeanStatic",
                    line_of(stripped, m.start()),
                )
            )

        for m in re.finditer(r"\bnative_decide\b", stripped):
            findings.append(
                _finding(
                    "LEAN_NATIVE_DECIDE",
                    Severity.WARNING,
                    "native_decide usage detected (compiler-backed reduction)",
                    "LeanStatic",
                    line_of(stripped, m.start()),
                )
            )

        tautology_patterns = [
            re.compile(r":\s*True\s*:=\s*by\s*(trivial|rfl|decide)", re.MULTILINE),
            re.compile(r":\s*True\s*:=\s*by\s*exact\s+True\.intro", re.MULTILINE),
            re.compile(r":\s*True\s*:=\s*True\.intro", re.MULTILINE),
        ]
        seen: set = set()
        for pat in tautology_patterns:
            for m in pat.finditer(stripped):
                if m.start() in seen:
                    continue
                seen.add(m.start())
                findings.append(
                    _finding(
                        "LEAN_TAUTOLOGY",
                        Severity.VIOLATION,
                        f"Tautological proof pattern: {m.group(0)!r}",
                        "LeanStatic",
                        line_of(stripped, m.start()),
                    )
                )

        decls = find_declarations(stripped)
        if Z3_AVAILABLE:
            for decl in decls:
                groups = find_paren_groups(decl["binders"])
                hyps: List[str] = []
                for g in groups:
                    inner = g[1:-1]
                    if ":" not in inner:
                        continue
                    _, _, typepart = inner.partition(":")
                    typepart = typepart.strip()
                    if any(op in typepart for op in (">", "<", "=", "\u2260", "\u2264", "\u2265")):
                        hyps.append(typepart)
                if len(hyps) < 2:
                    continue
                solver = z3.Solver()
                env: Dict[str, Any] = {}
                parsed = 0
                models: List[str] = []
                for expr in hyps:
                    py = apply_unicode_map(expr)
                    py = py.replace("^", "**")
                    py = py.replace("=", "==").replace(">==", ">=").replace("<==", "<=")
                    py = py.replace("====", "==")
                    try:
                        tree = ast.parse(py, mode="eval")
                        solver.add(ast_to_z3(tree, env))
                        parsed += 1
                        models.append(expr)
                    except Exception:
                        continue
                if parsed >= 2 and solver.check() == z3.unsat:
                    findings.append(
                        _finding(
                            "LEAN_Z3_VACUOUS",
                            Severity.VIOLATION,
                            f"Z3: hypotheses of {decl['name']} are UNSAT ({'; '.join(models)})",
                            "LeanZ3",
                            line_of(stripped, decl["decl_start"]),
                        )
                    )

        if SYMPY_AVAILABLE:
            for decl in decls:
                target = decl["statement"]
                if "=" not in target:
                    continue
                if any(tok in target for tok in ("\u2192", "->", "\u2200", "\u2203", "=>")):
                    continue
                parts = target.split("=", 1)
                if len(parts) != 2:
                    continue
                lhs = apply_unicode_map(parts[0].strip()).replace("^", "**")
                rhs = apply_unicode_map(parts[1].strip()).replace("^", "**")
                try:
                    tf = sp_parse.standard_transformations + (
                        sp_parse.implicit_multiplication_application,
                    )
                    l = sp_parse.parse_expr(lhs, transformations=tf)
                    r = sp_parse.parse_expr(rhs, transformations=tf)
                    if sp.simplify(l - r) != 0:
                        findings.append(
                            _finding(
                                "LEAN_SYMPY_MISMATCH",
                                Severity.WARNING,
                                f"SymPy could not verify identity for {decl['name']}",
                                "LeanSymPy",
                                line_of(stripped, decl["statement_start"]),
                            )
                        )
                except Exception:
                    continue

        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Lean gold-standard static multi-engine analysis",
            timestamp=_utc(),
            artifact_path=path,
            artifact_hash=hash_file(path),
            metadata={
                "z3": Z3_AVAILABLE,
                "sympy": SYMPY_AVAILABLE,
                "declarations": [d["name"] for d in decls],
            },
        )
        return findings, [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        path = os.path.abspath(path)
        if not self.check_native_available():
            return findings, evidence

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            findings.append(
                _finding("NATIVE_ERROR", Severity.WARNING, str(e), "LeanNative")
            )
            return findings, evidence

        stripped = strip_lean_comments(content)
        decls = [d["name"] for d in find_declarations(stripped)]
        if not decls:
            decls = DECL_RE.findall(stripped)

        project_dir = os.path.dirname(path)
        env = probe_environment(project_dir)
        if not env.get("has_lake_project"):
            findings.append(
                _finding(
                    "LEAN_NO_LAKE_PROJECT",
                    Severity.WARNING,
                    "No lakefile near target; bare lean may fail on Mathlib imports",
                    "LeanNative",
                )
            )

        with tempfile.NamedTemporaryFile(
            suffix=".lean", mode="w", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.write("\n\n")
            for d in decls:
                tmp.write(f"#print axioms {d}\n")
            tmp_path = tmp.name

        output = ""
        try:
            try:
                if which("lake") and env.get("has_lake_project"):
                    res = subprocess.run(
                        ["lake", "env", "lean", tmp_path],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                else:
                    res = subprocess.run(
                        ["lean", tmp_path],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                output = (res.stdout or "") + "\n" + (res.stderr or "")
                if res.returncode != 0 and not decls:
                    findings.append(
                        _finding(
                            "LEAN_COMPILE_ERROR",
                            Severity.VIOLATION,
                            (res.stderr or res.stdout or "lean failed")[-4000:],
                            "LeanNative",
                        )
                    )
            except subprocess.TimeoutExpired:
                findings.append(
                    _finding(
                        "LEAN_KERNEL_NEVER_RAN",
                        Severity.VIOLATION,
                        "Lean native verification timed out (>120s)",
                        "LeanNative",
                    )
                )
                return findings, evidence
            except FileNotFoundError:
                findings.append(
                    _finding(
                        "LEAN_KERNEL_NEVER_RAN",
                        Severity.VIOLATION,
                        "Lean CLI not found during native run",
                        "LeanNative",
                    )
                )
                return findings, evidence

            kernel_hit = False
            for d in decls:
                m = re.search(
                    rf"'{re.escape(d)}' depends on axioms:\s*\[([^\]]*)\]",
                    output,
                )
                if not m:
                    m = re.search(
                        rf"{re.escape(d)} depends on axioms:\s*\[([^\]]*)\]",
                        output,
                    )
                if not m:
                    continue
                kernel_hit = True
                body = m.group(1).strip()
                axes = [a.strip() for a in body.split(",") if a.strip()]
                for ax in axes:
                    if ax in SPECIAL_AXIOMS:
                        findings.append(
                            _finding(
                                SPECIAL_AXIOMS[ax],
                                Severity.VIOLATION,
                                f"Kernel: theorem {d} depends on {ax}",
                                "LeanKernel",
                            )
                        )
                    elif ax not in APPROVED_AXIOMS:
                        findings.append(
                            _finding(
                                "LEAN_AXIOM_SMUGGLE",
                                Severity.VIOLATION,
                                f"Kernel: theorem {d} depends on non-allowlisted axiom {ax}",
                                "LeanKernel",
                            )
                        )

            if decls and not kernel_hit:
                if "error" in output.lower() or "failed" in output.lower():
                    findings.append(
                        _finding(
                            "LEAN_COMPILE_ERROR",
                            Severity.VIOLATION,
                            "Lean ran but no axiom lines parsed; compile failure likely.\n"
                            + output[-3000:],
                            "LeanNative",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "LEAN_KERNEL_NEVER_RAN",
                            Severity.VIOLATION,
                            "No parseable #print axioms output for any declaration",
                            "LeanNative",
                        )
                    )

            evidence.append(
                Evidence(
                    evidence_type=EvidenceType.NATIVE_VERIFICATION,
                    description="Lean native compile + #print axioms kernel audit",
                    timestamp=_utc(),
                    artifact_path=path,
                    artifact_hash=hash_file(path),
                    content_summary=output[-2000:] if output else None,
                    metadata={
                        "environment": env,
                        "declarations": decls,
                        "kernel_hit": kernel_hit,
                    },
                )
            )
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        return findings, evidence

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        checks_performed = ["Static Analysis"]
        checks_unavailable: List[str] = []
        assumptions: List[str] = []
        trust_boundaries: List[str] = []

        if Z3_AVAILABLE:
            checks_performed.append("Z3 Vacuous Hypothesis Scan")
        else:
            checks_unavailable.append("Z3 Vacuous Hypothesis Scan (pip install z3-solver)")

        if SYMPY_AVAILABLE:
            checks_performed.append("SymPy Algebraic Identity Scan")
        else:
            checks_unavailable.append("SymPy Algebraic Identity Scan (pip install sympy)")

        static_f, static_e = self.run_static_analysis(path)
        findings.extend(static_f)
        evidence.extend(static_e)

        env = probe_environment(os.path.dirname(os.path.abspath(path)))
        assumptions.append(f"lean_version={env.get('lean_version')}")
        if env.get("mathlib_present"):
            assumptions.append("mathlib detected near project")

        if self.check_native_available():
            checks_performed.append("Native Verification")
            nat_f, nat_e = self.run_native_verification(path)
            findings.extend(nat_f)
            evidence.extend(nat_e)
            if any(f.code == "LEAN_KERNEL_NEVER_RAN" for f in nat_f):
                trust_boundaries.append("Kernel axiom audit did not complete")
        else:
            checks_unavailable.append("Native Verification (lean/lake binary missing)")
            trust_boundaries.append("No Lean toolchain \u2014 static-only bounds")
            findings.append(
                _finding(
                    "LEAN_KERNEL_NEVER_RAN",
                    Severity.WARNING,
                    "lean/lake not on PATH; native kernel audit skipped",
                    "LeanNative",
                )
            )

        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=assumptions,
            trust_boundaries=trust_boundaries,
        )
        return findings, evidence, coverage
