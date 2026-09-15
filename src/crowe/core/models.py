"""Modelos de datos para el análisis de portabilidad en CROWE."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PortabilityIssue(BaseModel):
    code: str
    category: str  # "POINTER_SIZE", "ENDIANNESS", "CHAR_SIGN", "ALIGNMENT", "VLA"
    severity: str  # "ERROR", "WARNING", "INFO"
    file_path: str
    line_number: int
    line_content: str
    message: str
    suggestion: str


class TargetArchStatus(BaseModel):
    architecture: str  # "x86_64", "aarch64", "riscv64"
    compiler_available: bool = False
    compilation_passed: bool = True
    compiler_output: str = ""


class PortabilityReport(BaseModel):
    schema_version: str = "1.0.0"
    files_analyzed: List[str] = Field(default_factory=list)
    issues: List[PortabilityIssue] = Field(default_factory=list)
    architectures: List[TargetArchStatus] = Field(default_factory=list)
    passed: bool = True
