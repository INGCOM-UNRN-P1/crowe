"""Regresión de CROWE-D0301/D0302/D0304.

CRW002 y CRW005 usaban regex de una sola línea sin contexto semántico:
cualquier `if (var < 0)` se marcaba como asunción de char sin signo, y
cualquier `T buf[IDENTIFICADOR]` como VLA, aunque IDENTIFICADOR fuera una
macro. `--cross-compile` con más de un archivo invocaba `gcc -c ... -o
/dev/null`, inválido con múltiples fuentes, así que fallaba siempre.
"""

import shutil
from pathlib import Path

import pytest

from crowe.core.portability_linter import lint_file_portability

necesita_gcc = pytest.mark.skipif(not shutil.which("gcc"), reason="requiere gcc")


def _codigos(tmp_path: Path, fuente: str):
    archivo = tmp_path / "caso.c"
    archivo.write_text(fuente, encoding="utf-8")
    return {issue.code for issue in lint_file_portability(archivo)}


def test_int_menor_a_cero_no_es_crw002(tmp_path):
    codigos = _codigos(tmp_path, "int main(void) { int total = -5; if (total < 0) return 1; return 0; }")
    assert "CRW002" not in codigos


def test_char_menor_a_cero_si_es_crw002(tmp_path):
    codigos = _codigos(tmp_path, "int main(void) { char c = -5; if (c < 0) return 1; return 0; }")
    assert "CRW002" in codigos


def test_arreglo_con_macro_no_es_vla(tmp_path):
    codigos = _codigos(
        tmp_path,
        "#define MAX_ELEM 100\nint main(void) { int buf[MAX_ELEM]; return 0; }",
    )
    assert "CRW005" not in codigos


def test_arreglo_con_variable_si_es_vla(tmp_path):
    codigos = _codigos(tmp_path, "int main(void) { int n = 10; int vla[n]; return 0; }")
    assert "CRW005" in codigos


@necesita_gcc
def test_cross_compile_multiarchivo_no_falla_por_invocacion_invalida(tmp_path):
    from crowe.core.cross_compiler import check_target_compilation

    a = tmp_path / "a.c"
    b = tmp_path / "b.c"
    a.write_text("int suma(int x, int y) { return x + y; }\n", encoding="utf-8")
    b.write_text('#include <stdio.h>\nint suma(int, int);\nint main(void) { printf("%d\\n", suma(2, 3)); return 0; }\n', encoding="utf-8")

    resultados = check_target_compilation([a, b])
    x86 = next(r for r in resultados if r.architecture == "x86_64")
    assert x86.compilation_passed is True, x86.compiler_output


@necesita_gcc
def test_cross_compile_multiarchivo_detecta_error_real(tmp_path):
    from crowe.core.cross_compiler import check_target_compilation

    a = tmp_path / "a.c"
    c = tmp_path / "c.c"
    a.write_text("int suma(int x, int y) { return x + y; }\n", encoding="utf-8")
    c.write_text("int main(void) { int x; return 0; }\n", encoding="utf-8")

    resultados = check_target_compilation([a, c])
    x86 = next(r for r in resultados if r.architecture == "x86_64")
    assert x86.compilation_passed is False
