"""Plugin de CROWE para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any, List
from crowe.core.portability_linter import lint_file_portability


class CrowePlugin:
    """Plugin de portabilidad multi-arquitectura para Ripley."""

    name = "portability"
    description = "Linter de portabilidad (endianness, tamaños de puntero, compatibilidad 64/32 bits)"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        c_files = list(source_dir.glob("*.c")) + list(source_dir.glob("*.h"))

        issues_found = []
        has_critical = False

        for f in c_files:
            issues = lint_file_portability(f)
            for iss in issues:
                if iss.severity == "ERROR":
                    has_critical = True
                issues_found.append({
                    "code": iss.code,
                    "severity": iss.severity,
                    "file": f.name,
                    "line": iss.line_number,
                    "message": iss.message,
                    "suggestion": iss.suggestion
                })

        return {
            "passed": not has_critical,
            "issues_count": len(issues_found),
            "issues": issues_found
        }
