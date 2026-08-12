from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from mvpc.trust import Finding, CoverageReport
from mvpc.evidence import Evidence

class VerificationBackend(ABC):
    
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        pass

    @abstractmethod
    def supports(self, path: str) -> bool:
        pass

    @abstractmethod
    def check_native_available(self) -> bool:
        pass

    @abstractmethod
    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        pass

    @abstractmethod
    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        pass

    @abstractmethod
    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        pass
