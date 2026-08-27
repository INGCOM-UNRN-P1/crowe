"""Verificación de compilación cruzada con toolchains instalados."""

import shutil
import subprocess
from pathlib import Path
from typing import List
from crowe.core.models import TargetArchStatus

COMPILERS = [
    ("x86_64", ["gcc", "x86_64-linux-gnu-gcc"]),
    ("aarch64", ["aarch64-linux-gnu-gcc", "arm-linux-gnueabihf-gcc"]),
    ("riscv64", ["riscv64-linux-gnu-gcc", "riscv64-unknown-elf-gcc"]),
]


def check_target_compilation(files: List[Path]) -> List[TargetArchStatus]:
    """Compila los archivos provistos contra las toolchains disponibles en el sistema."""
    results = []

    for arch, candidates in COMPILERS:
        compiler_bin = None
        for cand in candidates:
            if shutil.which(cand):
                compiler_bin = cand
                break

        if not compiler_bin:
            results.append(TargetArchStatus(
                architecture=arch,
                compiler_available=False,
                compilation_passed=True,
                compiler_output=f"Toolchain para {arch} no instalada (se omitió verificación binaria)."
            ))
            continue

        cmd = [compiler_bin, "-c", "-Wall", "-Wextra", "-Werror", "-pedantic", "-std=c11"] + [str(f) for f in files] + ["-o", "/dev/null"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            results.append(TargetArchStatus(
                architecture=arch,
                compiler_available=True,
                compilation_passed=(res.returncode == 0),
                compiler_output=res.stderr if res.returncode != 0 else "Compilación limpia sin advertencias."
            ))
        except Exception as e:
            results.append(TargetArchStatus(
                architecture=arch,
                compiler_available=True,
                compilation_passed=False,
                compiler_output=f"Fallo al invocar compilador: {e}"
            ))

    return results
