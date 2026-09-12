"""External evidence artifact verification (MVPC-X issue #8).

This subpackage verifies *external* claim/evidence artifacts produced by
other repositories (4Leibniz formal-claims catalogs, Res-Nova Evidence
Atlas / claim ledgers) against local, versioned schema/provenance/gate
rules.

Scope (read this before touching anything in this package):

MVPC-X, through this module, verifies:
  - artifact shape/schema version;
  - canonical content identity (hash);
  - declared source provenance (repo/commit/path);
  - required evidence fields;
  - declared check/gate outcomes;
  - witness-bundle integrity.

MVPC-X, through this module, never becomes the source of truth for:
  - Lean theorem truth (no Lean toolchain is ever invoked here);
  - scientific/physical truth of any claim;
  - RYTT grammar (see issue #7 / mvpc.nexus for that surface);
  - Res-Nova epistemic interpretation;
  - AEON governance policy.

A passing verdict from this package means only: "this artifact satisfied
the configured schema, integrity, provenance, and evidence-linkage
gates." It never means "the underlying theorem/physics claim is
independently proven true." Upstream statuses (proved/conditional/open/
refuted/proposal/derived/empirically_supported/...) are always preserved
verbatim in the output; this package never promotes or rewrites them.

Local-file-only in v1: no network fetch, no GitHub API call, no database
write, no artifact auto-download. See docs/EXTERNAL_ARTIFACTS.md.
"""

from mvpc.external_artifacts.models import Gate, GateStatus, ArtifactVerificationResult
from mvpc.external_artifacts.registry import (
    ArtifactAdapter,
    UnsupportedArtifactError,
    get_adapter,
    list_supported,
    register_adapter,
)

# Import for adapter-registration side effects only. New adapters (e.g. a
# future RYTT-under-issue-#7 adapter) register the same way: import the
# module here so `register_adapter(...)` runs at package import time.
from mvpc.external_artifacts import (
    leibniz_adapter as _leibniz_adapter,
)  # noqa: F401,E402
from mvpc.external_artifacts import (
    resnova_adapter as _resnova_adapter,
)  # noqa: F401,E402

__all__ = [
    "Gate",
    "GateStatus",
    "ArtifactVerificationResult",
    "ArtifactAdapter",
    "UnsupportedArtifactError",
    "get_adapter",
    "list_supported",
    "register_adapter",
]
