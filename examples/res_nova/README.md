# Res Nova Fixture Pack

These fixtures teach MVPC-X how **not** to over-certify the current Res Nova repository.

They are examples only. No Res Nova physics is imported into `src/mvpc`.

## Current judgment targets

| Claim | Expected judgment | Reason |
|---|---:|---|
| `D1.2` dual-channel algebraic identity | D2 local | `DualChannelDerivation.lean` exists and elaborates, but RUN_007 is one local walk, not independent D3/D4 |
| `D3.1` `lim μ(x)=1` | refuse D2 | no asymptotic-limit theorem exists in the tracked suite |
| `F7` Lean suite | D2 local | 17/17 gate pass after `lake exe cache get`; not a cold-machine proof, not CI, not independent |
| `O1` horizon `a0` identity | D0/D1 | open physical hypothesis; measurement exists, derivation does not |
| phantom Lean modules | reject | names such as `HorizonScale.lean` or `PPNParameters.lean` are not tracked on Res Nova main |

The point is not to summarize Res Nova. The point is to prove MVPC-X can refuse the failure modes it already produced.
