"""Tests unitarios y de integración para CROWE."""

from pathlib import Path
from typer.testing import CliRunner
from crowe.cli import app
from crowe.core.portability_linter import lint_file_portability
from crowe.plugins.ripley_plugin import CrowePlugin

runner = CliRunner()


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
