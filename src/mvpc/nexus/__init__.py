"""MVPC-X Sovereign Nexus control-plane primitives.

All APIs are local-only and evidence-first. Importing this package performs no
backend execution, process launch, network operation, or ledger write.
"""

from .ast_normalizer import (
    NormalizedAst,
    SourceLanguage,
    normalize_file,
    normalize_source,
)
from .backend_array import BackendReceipt, LanguageAgnosticVerificationArray
from .cas_certificate import (
    CasCertificateResult,
    PolynomialCertificate,
    verify_certificate_file,
    verify_polynomial_certificate,
)
from .glassbox import GlassBoxDocument, TrafficLight, build_glassbox
from .intake import (
    BinaryTrustReport,
    DependencyParityReport,
    dependency_parity,
    validate_mvpc_bin,
)
from .manifest_ledger import ManifestPair, PermanentManifest, PermanentManifestLedger
from .policy import (
    NexusVerdict,
    PolicyDecision,
    derive_native_verdict,
    evaluate_source_policy,
)
from .runtime import NexusRunResult, SovereignNexusRuntime

__all__ = [
    "BackendReceipt",
    "BinaryTrustReport",
    "CasCertificateResult",
    "DependencyParityReport",
    "GlassBoxDocument",
    "LanguageAgnosticVerificationArray",
    "ManifestPair",
    "NexusRunResult",
    "NexusVerdict",
    "NormalizedAst",
    "PermanentManifest",
    "PermanentManifestLedger",
    "PolicyDecision",
    "PolynomialCertificate",
    "SourceLanguage",
    "SovereignNexusRuntime",
    "TrafficLight",
    "build_glassbox",
    "dependency_parity",
    "derive_native_verdict",
    "evaluate_source_policy",
    "normalize_file",
    "normalize_source",
    "validate_mvpc_bin",
    "verify_certificate_file",
    "verify_polynomial_certificate",
]
