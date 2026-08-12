from typing import List, Optional
from mvpc.backends.base import VerificationBackend
from mvpc.backends.lean import LeanBackend
from mvpc.backends.coq import CoqBackend
from mvpc.backends.isabelle import IsabelleBackend
from mvpc.backends.python import PythonBackend
from mvpc.backends.generic import GenericBackend

class BackendRegistry:
    def __init__(self):
        self.backends: List[VerificationBackend] = []
        self.generic_backend = GenericBackend()
        
    def register(self, backend: VerificationBackend):
        self.backends.append(backend)
        
    def get_backend(self, path: str) -> VerificationBackend:
        for backend in self.backends:
            if backend.supports(path):
                return backend
        return self.generic_backend

def get_default_registry() -> BackendRegistry:
    registry = BackendRegistry()
    registry.register(LeanBackend())
    registry.register(CoqBackend())
    registry.register(IsabelleBackend())
    registry.register(PythonBackend())
    return registry
