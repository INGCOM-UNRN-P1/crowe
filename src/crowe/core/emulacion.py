"""Ejecución real en otras arquitecturas con qemu (revisión 07, crowe).

`crowe check` solo verifica que el programa compile en x86_64, aarch64 y riscv64. Muchos errores de
portabilidad compilan igual y aparecen al correr: `char` sin signo en ARM, `long` de otro tamaño, un
`int` leído byte a byte. Con la toolchain y `qemu-<arquitectura>` instalados, `crowe run` compila
estático para cada arquitectura, ejecuta con la misma entrada y compara la salida con la nativa.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from crowe.core.cross_compiler import COMPILERS

EMULADORES: Dict[str, List[str]] = {
    "x86_64": ["qemu-x86_64"],
    "aarch64": ["qemu-aarch64", "qemu-arm"],
    "riscv64": ["qemu-riscv64"],
}


@dataclass
class Corrida:
    arquitectura: str
    estado: str  # "ok", "sin-toolchain", "sin-emulador", "no-compila", "error"
    salida: str = ""
    codigo: Optional[int] = None
    detalle: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {"arquitectura": self.arquitectura, "estado": self.estado, "salida": self.salida,
                "codigo": self.codigo, "detalle": self.detalle}


@dataclass
class ComparacionEjecucion:
    nativa: str
    corridas: List[Corrida] = field(default_factory=list)

    @property
    def diferencias(self) -> List[str]:
        base = next((c for c in self.corridas if c.arquitectura == self.nativa and c.estado == "ok"), None)
        if base is None:
            return []
        return [c.arquitectura for c in self.corridas
                if c.estado == "ok" and c.arquitectura != self.nativa and (c.salida, c.codigo) != (base.salida, base.codigo)]

    def to_dict(self) -> Dict[str, object]:
        return {"schema_version": "1.0.0", "nativa": self.nativa, "corridas": [c.to_dict() for c in self.corridas],
                "diferencias": self.diferencias, "passed": not self.diferencias}


def _primera(candidatos: List[str]) -> Optional[str]:
    return next((c for c in candidatos if shutil.which(c)), None)


def arquitectura_nativa() -> str:
    maquina = platform.machine().lower()
    return {"amd64": "x86_64", "arm64": "aarch64"}.get(maquina, maquina)


def ejecutar_en_arquitecturas(fuentes: List[Path], entrada: str = "", timeout: float = 10.0,
                              arquitecturas: Optional[List[str]] = None) -> ComparacionEjecucion:
    nativa = arquitectura_nativa()
    resultado = ComparacionEjecucion(nativa=nativa)
    with tempfile.TemporaryDirectory(prefix="crowe-run-") as tmp:
        for arq, compiladores in COMPILERS:
            if arquitecturas and arq not in arquitecturas:
                continue
            gcc = "gcc" if arq == nativa and shutil.which("gcc") else _primera([c for c in compiladores if c != "gcc"])
            if gcc is None:
                resultado.corridas.append(Corrida(arq, "sin-toolchain", detalle=f"instalá {compiladores[-1]}"))
                continue
            emulador = None if arq == nativa else _primera(EMULADORES.get(arq, []))
            if arq != nativa and emulador is None:
                resultado.corridas.append(Corrida(arq, "sin-emulador", detalle=f"instalá {EMULADORES[arq][0]} (paquete qemu-user)"))
                continue
            binario = Path(tmp) / f"prog-{arq}"
            comp = subprocess.run([gcc, "-static", "-std=c11", "-O0", *map(str, fuentes), "-o", str(binario)],
                                  capture_output=True, text=True, check=False)
            if comp.returncode != 0:
                resultado.corridas.append(Corrida(arq, "no-compila", detalle=comp.stderr.strip()[:500]))
                continue
            comando = [str(binario)] if emulador is None else [emulador, str(binario)]
            try:
                corrida = subprocess.run(comando, input=entrada, capture_output=True, text=True, timeout=timeout, check=False)
            except subprocess.TimeoutExpired:
                resultado.corridas.append(Corrida(arq, "error", detalle=f"superó {timeout:g} s"))
                continue
            resultado.corridas.append(Corrida(arq, "ok", salida=corrida.stdout, codigo=corrida.returncode))
    return resultado
