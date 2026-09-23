"""efficient-ally: find code that is slower than it needs to be, and say how to fix it."""

from .analyzer import analyze
from .findings import Finding, FunctionSummary, Report

__all__ = ["Finding", "FunctionSummary", "Report", "analyze"]
__version__ = "0.1.0"
