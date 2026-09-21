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

        # Sin `-Werror`: esto verifica portabilidad (¿compila en cada arquitectura?),
        # no estilo. Con `-Werror` una variable sin usar tumbaba el gate; ahora solo
        # un error real de compilación lo hace fallar y los warnings se informan.
        # `-fsyntax-only` en vez de `-c ... -o /dev/null`: con más de un archivo,
        # `-c` exige un `.o` por archivo y rechaza un único `-o` compartido
        # ("cannot specify '-o' with '-c' ... with multiple files"), lo que
        # hacía fallar SIEMPRE la verificación multi-archivo, presentándose
        # como un fallo de portabilidad que no tiene nada que ver con eso.
        # `-fsyntax-only` no emite objetos, así que no colisiona con `-o` ni
        # con la cantidad de archivos.
        cmd = [compiler_bin, "-fsyntax-only", "-Wall", "-Wextra", "-pedantic", "-std=c11"] + [str(f) for f in files]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            results.append(TargetArchStatus(
                architecture=arch,
                compiler_available=True,
                compilation_passed=(res.returncode == 0),
                compiler_output=(
                    res.stderr if res.returncode != 0
                    else (res.stderr or "Compilación limpia sin advertencias.")
                )
            ))
        except Exception as e:
            results.append(TargetArchStatus(
                architecture=arch,
                compiler_available=True,
                compilation_passed=False,
                compiler_output=f"Fallo al invocar compilador: {e}"
            ))

    return results
