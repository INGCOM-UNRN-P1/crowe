"""`crowe run`: ejecución con qemu y comparación con la nativa (revisión 07)."""

import subprocess
from pathlib import Path

import crowe.core.emulacion as emulacion


def _instalados(*nombres):
    return lambda n: f"/usr/bin/{n}" if n in nombres else None


def _fuente(tmp_path: Path) -> Path:
    f = tmp_path / "p.c"
    f.write_text("int main(void){return 0;}\n", encoding="utf-8")
    return f


def test_compara_con_la_nativa(tmp_path, monkeypatch):
    monkeypatch.setattr(emulacion, "arquitectura_nativa", lambda: "x86_64")
    monkeypatch.setattr(emulacion.shutil, "which", _instalados("gcc", "aarch64-linux-gnu-gcc", "qemu-aarch64"))
    llamadas = []

    def correr(cmd, **kwargs):
        llamadas.append(cmd)
        if "-static" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        salida = "-1\n" if cmd[0] == "qemu-aarch64" else "255\n"  # char con y sin signo
        return subprocess.CompletedProcess(cmd, 0, salida, "")

    monkeypatch.setattr(emulacion.subprocess, "run", correr)
    res = emulacion.ejecutar_en_arquitecturas([_fuente(tmp_path)])
    estados = {c.arquitectura: c.estado for c in res.corridas}
    assert estados == {"x86_64": "ok", "aarch64": "ok", "riscv64": "sin-toolchain"}
    assert res.diferencias == ["aarch64"] and not res.to_dict()["passed"]
    assert any(c[0] == "qemu-aarch64" for c in llamadas)


def test_sin_emulador(tmp_path, monkeypatch):
    monkeypatch.setattr(emulacion, "arquitectura_nativa", lambda: "x86_64")
    monkeypatch.setattr(emulacion.shutil, "which", _instalados("gcc", "riscv64-linux-gnu-gcc"))
    monkeypatch.setattr(emulacion.subprocess, "run", lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "1\n", ""))
    res = emulacion.ejecutar_en_arquitecturas([_fuente(tmp_path)], arquitecturas=["x86_64", "riscv64"])
    assert [(c.arquitectura, c.estado) for c in res.corridas] == [("x86_64", "ok"), ("riscv64", "sin-emulador")]
    assert "qemu-riscv64" in res.corridas[1].detalle and res.diferencias == []
