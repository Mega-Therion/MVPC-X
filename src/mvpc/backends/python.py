import os
import re
import ast
import subprocess
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from shutil import which

from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from mvpc.explanations import get_explanation

# Optional engines
try:
    import sympy as sp
    import sympy.parsing.sympy_parser as sp_parse
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def _ast_to_z3(node, local_env: Dict[str, Any]):
    """Convert a Python AST expression into a Z3 expression."""
    if isinstance(node, ast.Expression):
        return _ast_to_z3(node.body, local_env)
    if isinstance(node, ast.BoolOp):
        vals = [_ast_to_z3(v, local_env) for v in node.values]
        if isinstance(node.op, ast.And):
            return z3.And(*vals)
        if isinstance(node.op, ast.Or):
            return z3.Or(*vals)
    if isinstance(node, ast.UnaryOp):
        v = _ast_to_z3(node.operand, local_env)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return v
        if isinstance(node.op, ast.Not):
            return z3.Not(v)
    if isinstance(node, ast.BinOp):
        l, r = _ast_to_z3(node.left, local_env), _ast_to_z3(node.right, local_env)
        if isinstance(node.op, ast.Add):
            return l + r
        if isinstance(node.op, ast.Sub):
            return l - r
        if isinstance(node.op, ast.Mult):
            return l * r
        if isinstance(node.op, ast.Div):
            return l / r
        if isinstance(node.op, ast.Pow):
            return l ** r
    if isinstance(node, ast.Compare):
        left = _ast_to_z3(node.left, local_env)
        results = []
        curr = left
        for op, comp in zip(node.ops, node.comparators):
            right = _ast_to_z3(comp, local_env)
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
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


class PythonBackend(VerificationBackend):
    CLAIM_REGEX = re.compile(
        r"(?:MVPC-CLAIM|BIOMECH-CLAIM)\s+(identity|constraint|numeric)\s*:\s*(.+)$",
        re.IGNORECASE | re.MULTILINE
    )

    def name(self) -> str:
        return "Python & Mathematical CAS"

    def supported_extensions(self) -> List[str]:
        return [".py", ".biomech"]

    def supports(self, path: str) -> bool:
        p = path.lower()
        return any(p.endswith(ext) for ext in self.supported_extensions())

    def check_native_available(self) -> bool:
        return which("python3") is not None or which("python") is not None

    def _check_symbolic_identity(self, expr: str) -> Tuple[Optional[bool], str]:
        if not SYMPY_AVAILABLE:
            return None, "SymPy not available"
        try:
            if "==" in expr:
                left, right = expr.split("==", 1)
            elif "=" in expr:
                left, right = expr.split("=", 1)
            else:
                return None, "Need equality (= or ==)"
            tf = sp_parse.standard_transformations + (
                sp_parse.implicit_multiplication_application,
            )
            l = sp_parse.parse_expr(left.strip(), transformations=tf)
            r = sp_parse.parse_expr(right.strip(), transformations=tf)
            if sp.simplify(l - r) == 0:
                return True, "simplify(LHS - RHS) == 0"
            return False, f"LHS - RHS simplifies to: {sp.simplify(l - r)}"
        except Exception as e:
            return None, str(e)

    def _check_z3_constraints(self, exprs: List[str]) -> Tuple[bool, str]:
        if not Z3_AVAILABLE:
            return False, "Z3 not available"
        solver = z3.Solver()
        env: Dict[str, Any] = {}
        parsed = 0
        for e in exprs:
            py = (
                e.replace("≤", "<=")
                .replace("≥", ">=")
                .replace("≠", "!=")
                .replace("^", "**")
                .replace("=", "==")
                .replace(">==", ">=")
                .replace("<==", "<=")
                .replace("====", "==")
            )
            try:
                tree = ast.parse(py, mode="eval")
                node = _ast_to_z3(tree, env)
                solver.add(node)
                parsed += 1
            except Exception:
                continue
        if parsed == 0:
            return False, "No constraints could be parsed"
        is_unsat = solver.check() == z3.unsat
        return is_unsat, f"parsed={parsed}/{len(exprs)}"

    def _check_numeric_samples(self, body: str) -> Tuple[Optional[bool], str]:
        if "samples=" not in body:
            return None, "Missing samples= clause"
        claim, _, samples = body.partition("samples=")
        claim = claim.strip()

        env_lists: Dict[str, List[float]] = {}
        for part in samples.split(";"):
            part = part.strip()
            if not part or ":" not in part:
                continue
            var, vals = part.split(":", 1)
            try:
                env_lists[var.strip()] = [float(v.strip()) for v in vals.split(",") if v.strip()]
            except ValueError as e:
                return None, f"Sample parsing error: {e}"

        if not env_lists:
            return None, "No sample points parsed"

        if "==" in claim:
            left, right = claim.split("==", 1)
        elif "=" in claim:
            left, right = claim.split("=", 1)
        else:
            return None, "Need equality (= or ==)"

        if not SYMPY_AVAILABLE:
            return None, "SymPy required for numeric point evaluation"

        try:
            tf = sp_parse.standard_transformations + (
                sp_parse.implicit_multiplication_application,
            )
            l = sp_parse.parse_expr(left.strip(), transformations=tf)
            r = sp_parse.parse_expr(right.strip(), transformations=tf)
            syms = sorted({str(s) for s in (l.free_symbols | r.free_symbols)})
            fl = sp.lambdify(syms, l, modules=["numpy", "math"])
            fr = sp.lambdify(syms, r, modules=["numpy", "math"])

            if len(syms) == 1 and syms[0] in env_lists:
                var_name = syms[0]
                for x in env_lists[var_name]:
                    lv = float(fl(x))
                    rv = float(fr(x))
                    if abs(lv - rv) > 1e-6:
                        return False, f"At {var_name}={x}: LHS ({lv}) != RHS ({rv})"
                return True, f"Verified across {len(env_lists[var_name])} sample points"
            return None, "Multi-variable numeric check needs exact sample matching"
        except Exception as e:
            return None, str(e)

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if 'exec(' in line:
                    exp = get_explanation("PY_EXEC")
                    findings.append(Finding(
                        code="PY_EXEC",
                        severity=Severity.WARNING,
                        message="Use of 'exec()' detected",
                        system="PythonStatic",
                        line=i,
                        remediation=exp["action"]
                    ))
                if 'eval(' in line:
                    exp = get_explanation("PY_EVAL")
                    findings.append(Finding(
                        code="PY_EVAL",
                        severity=Severity.WARNING,
                        message="Use of 'eval()' detected",
                        system="PythonStatic",
                        line=i,
                        remediation=exp["action"]
                    ))
                if 'os.system(' in line:
                    exp = get_explanation("PY_OS_SYSTEM")
                    findings.append(Finding(
                        code="PY_OS_SYSTEM",
                        severity=Severity.WARNING,
                        message="Use of 'os.system()' detected",
                        system="PythonStatic",
                        line=i,
                        remediation=exp["action"]
                    ))
                if 'shell=True' in line:
                    exp = get_explanation("PY_SHELL_TRUE")
                    findings.append(Finding(
                        code="PY_SHELL_TRUE",
                        severity=Severity.WARNING,
                        message="Use of subprocess with 'shell=True' detected",
                        system="PythonStatic",
                        line=i,
                        remediation=exp["action"]
                    ))
                if re.search(r"\b(TODO|FIXME|XXX)\b", line):
                    exp = get_explanation("GENERIC_PLACEHOLDER")
                    findings.append(Finding(
                        code="GENERIC_PLACEHOLDER",
                        severity=Severity.WARNING,
                        message=f"Placeholder marker detected on line {i}",
                        system="PythonStatic",
                        line=i,
                        remediation=exp["action"]
                    ))

            # Parse and verify inline mathematical claims
            claims = list(self.CLAIM_REGEX.finditer(content))
            constraints: List[str] = []

            for m in claims:
                kind = m.group(1).lower()
                body = m.group(2).strip()
                line_no = content[:m.start()].count("\n") + 1

                if kind == "identity":
                    ok, msg = self._check_symbolic_identity(body)
                    if ok is False:
                        exp = get_explanation("PY_IDENTITY_FAIL")
                        findings.append(Finding(
                            code="PY_IDENTITY_FAIL",
                            severity=Severity.VIOLATION,
                            message=f"Symbolic identity failed: {body} ({msg})",
                            system="SymPyCAS",
                            line=line_no,
                            remediation=exp["action"]
                        ))
                elif kind == "constraint":
                    constraints.append(body)
                elif kind == "numeric":
                    ok, msg = self._check_numeric_samples(body)
                    if ok is False:
                        exp = get_explanation("PY_NUMERIC_DRIFT")
                        findings.append(Finding(
                            code="PY_NUMERIC_DRIFT",
                            severity=Severity.VIOLATION,
                            message=f"Numeric sanity drift: {body} ({msg})",
                            system="NumPyNumeric",
                            line=line_no,
                            remediation=exp["action"]
                        ))

            if constraints and Z3_AVAILABLE:
                is_unsat, detail = self._check_z3_constraints(constraints)
                if is_unsat:
                    exp = get_explanation("PY_CONSTRAINT_UNSAT")
                    findings.append(Finding(
                        code="PY_CONSTRAINT_UNSAT",
                        severity=Severity.VIOLATION,
                        message=f"Constraint set is contradictory (UNSAT): {detail}",
                        system="Z3SMT",
                        remediation=exp["action"]
                    ))

        except Exception as e:
            findings.append(Finding(
                code="STATIC_ERROR",
                severity=Severity.WARNING,
                message=str(e),
                system="PythonStatic"
            ))

        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Python static AST and mathematical claim scan",
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifact_path=path,
            artifact_hash=hash_file(path)
        )
        return findings, [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        if not self.check_native_available():
            return findings, evidence

        try:
            py_bin = "python3" if which("python3") else "python"
            res = subprocess.run([py_bin, "-m", "py_compile", path], capture_output=True, text=True)
            if res.returncode != 0:
                exp = get_explanation("PY_SYNTAX_ERROR")
                findings.append(Finding(
                    code="PY_SYNTAX_ERROR",
                    severity=Severity.VIOLATION,
                    message=res.stderr or res.stdout,
                    system="PythonNative",
                    remediation=exp["action"]
                ))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Python syntax and bytecode compilation",
                timestamp=datetime.now(timezone.utc).isoformat(),
                artifact_path=path,
                artifact_hash=hash_file(path)
            )
            evidence.append(ev)
        except Exception as e:
            findings.append(Finding(
                code="NATIVE_ERROR",
                severity=Severity.WARNING,
                message=str(e),
                system="PythonNative"
            ))

        return findings, evidence

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        checks_performed = ["Static Analysis"]
        checks_unavailable: List[str] = []

        if SYMPY_AVAILABLE:
            checks_performed.append("SymPy CAS")
        else:
            checks_unavailable.append("SymPy CAS (pip install sympy)")

        if Z3_AVAILABLE:
            checks_performed.append("Z3 SMT Solver")
        else:
            checks_unavailable.append("Z3 SMT Solver (pip install z3-solver)")

        if NUMPY_AVAILABLE:
            checks_performed.append("NumPy Point Sampler")
        else:
            checks_unavailable.append("NumPy (pip install numpy)")

        static_f, static_e = self.run_static_analysis(path)
        findings.extend(static_f)
        evidence.extend(static_e)

        if self.check_native_available():
            checks_performed.append("Native Verification")
            nat_f, nat_e = self.run_native_verification(path)
            findings.extend(nat_f)
            evidence.extend(nat_e)
        else:
            checks_unavailable.append("Native Verification (python binary missing)")

        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=[],
            trust_boundaries=[]
        )
        return findings, evidence, coverage
