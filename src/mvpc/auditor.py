import os
from typing import List
from mvpc.engine import VerificationEngine
from mvpc.claim import Claim
from mvpc.policy import PolicyLevel
from mvpc.backends.registry import get_default_registry

def audit_directory(path: str, policy_level: PolicyLevel, recursive: bool = True) -> List[Claim]:
    engine = VerificationEngine(policy_level, get_default_registry())
    claims = []
    
    if os.path.isfile(path):
        claims.append(engine.verify_artifact(path))
        return claims
        
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip hidden files
            if file.startswith('.'):
                continue
            claims.append(engine.verify_artifact(file_path))
            
        if not recursive:
            break
            
    return claims
