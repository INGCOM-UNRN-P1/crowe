"""Tests unitarios y de integración para CROWE."""

import json
from pathlib import Path
from typer.testing import CliRunner
from crowe.cli import app
from crowe.core.portability_linter import lint_file_portability
from crowe.plugins.ripley_plugin import CrowePlugin

runner = CliRunner()


def test_cli_doctor():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    assert "doctor" in res.output.lower()

    res_json = runner.invoke(app, ["doctor", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["herramienta"] == "crowe"
    assert data["ok"] is True


def test_lint_pointer_to_int_cast(tmp_path):
    c = tmp_path / "test.c"
    c.write_text("""
    #include <stdlib.h>
    void test(void* ptr) {
        int x = (int)ptr;
    }
    """)
    issues = lint_file_portability(c)
    assert any(i.code == "CRW001" for i in issues)


def test_lint_char_negative(tmp_path):
    c = tmp_path / "char_test.c"
    c.write_text("""
    void test(void) {
        char c = -1;
    }
    """)
    issues = lint_file_portability(c)
    assert any(i.code == "CRW002" for i in issues)


def test_lint_clean_file(tmp_path):
    c = tmp_path / "clean.c"
    c.write_text("""
    #include <stdint.h>
    void test(void* ptr) {
        uintptr_t u = (uintptr_t)ptr;
    }
    """)
    issues = lint_file_portability(c)
    assert len(issues) == 0


def test_cli_lint_json(tmp_path):
    c = tmp_path / "main.c"
    c.write_text("int main(void) { return 0; }")
    res = runner.invoke(app, ["lint", str(c), "--json"])
    assert res.exit_code == 0
    assert '"passed": true' in res.output


def test_cli_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "CROWE" in res.output


def test_ripley_plugin(tmp_path):
    c = tmp_path / "mod.c"
    c.write_text("int foo(void) { return 0; }")
    plugin = CrowePlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "issues" in res


def test_warning_de_estilo_no_tumba_la_compilacion_cruzada(tmp_path):
    """CROWE-D0305: una variable sin usar es un warning, no un fallo de portabilidad."""
    from crowe.core.cross_compiler import check_target_compilation

    warn = tmp_path / "warn.c"
    warn.write_text("int f(void) { int sin_usar; return 0; }\n", encoding="utf-8")
    roto = tmp_path / "roto.c"
    roto.write_text("int f(void) { return ; }\nint g( {\n", encoding="utf-8")

    x86 = [r for r in check_target_compilation([warn]) if r.architecture == "x86_64"][0]
    assert x86.compiler_available and x86.compilation_passed
    assert "sin_usar" in x86.compiler_output  # el warning se informa igual

    x86_roto = [r for r in check_target_compilation([roto]) if r.architecture == "x86_64"][0]
    assert not x86_roto.compilation_passed
