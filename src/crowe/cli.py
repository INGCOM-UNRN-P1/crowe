"""CLI principal de CROWE."""

import json
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from crowe.core.models import PortabilityReport
from crowe.core.portability_linter import lint_file_portability
from crowe.core.cross_compiler import check_target_compilation

app = typer.Typer(
    name="crowe",
    help="Linter de portabilidad multi-arquitectura y compatibilidad C",
    add_completion=True
)
console = Console()


def generar_seccion_markdown(report: PortabilityReport) -> str:
    """Genera sección de auditoría de portabilidad para Dredd."""
    lines = ["## Portabilidad Multi-Arquitectura y Endianness (Crowe)\n"]
    lines.append(f"- **Archivos analizados:** {len(report.files_analyzed)}")
    lines.append(f"- **Problemas de portabilidad detectados:** {len(report.issues)}\n")
    if report.passed:
        lines.append("> [!TIP]\n> **Código Portable:** No se detectaron asunciones dependientes de arquitectura (endianness, sizeof punteros, tipos dependientes).\n")
    else:
        lines.append("> [!WARNING]\n> **Riesgos de Portabilidad:** Se detectaron construcciones dependientes de hardware o arquitectura.\n")
        lines.append("| Archivo | Línea | Código | Severidad | Descripción | Sugerencia |")
        lines.append("| :--- | :---: | :---: | :---: | :--- | :--- |")
        for iss in report.issues:
            fname = Path(iss.file_path).name
            lines.append(f"| `{fname}` | {iss.line_number} | `{iss.code}` | **{iss.severity}** | {iss.message} | {iss.suggestion} |")
        lines.append("")
    return "\n".join(lines)


@app.command("lint")
@app.command("check")
def lint(
    paths: List[Path] = typer.Argument(..., help="Archivos o directorios C a analizar"),
    check_cross_compile: bool = typer.Option(False, "--cross-compile", "-c", help="Intentar compilación contra toolchains x86_64, aarch64 y riscv64"),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
):
    """Analiza archivos C buscando asunciones no portables de hardware y endianness."""
    files_to_check: List[Path] = []
    for p in paths:
        if p.is_file():
            files_to_check.append(p)
        elif p.is_dir():
            files_to_check.extend(list(p.glob("**/*.c")) + list(p.glob("**/*.h")))

    if not files_to_check:
        console.print("[yellow]No se encontraron archivos C para analizar.[/yellow]")
        raise typer.Exit(code=0)

    all_issues = []
    for f in files_to_check:
        all_issues.extend(lint_file_portability(f))

    arch_statuses = []
    if check_cross_compile:
        arch_statuses = check_target_compilation(files_to_check)

    has_errors = any(i.severity == "ERROR" for i in all_issues) or any(not a.compilation_passed for a in arch_statuses)
    report = PortabilityReport(
        files_analyzed=[str(f) for f in files_to_check],
        issues=all_issues,
        architectures=arch_statuses,
        passed=not has_errors
    )

    if output_md:
        md_text = generar_seccion_markdown(report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Sección Markdown generada en:[/bold green] {output_md}")
        raise typer.Exit(code=0 if report.passed else 1)

    if json_output:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        if not report.passed:
            raise typer.Exit(code=1)
        return

    if not all_issues and (not check_cross_compile or report.passed):
        console.print(Panel(
            f"[bold green]✓ Código 100% Portable[/bold green]\n"
            f"• Archivos analizados: {len(files_to_check)}\n"
            f"• No se detectaron asunciones de endianness, ancho de puntero ni tipos no estándar.",
            title="[bold green]CROWE Portability Check[/bold green]"
        ))
        return

    if all_issues:
        table = Table(title="Problemas de Portabilidad Detectados", show_header=True, header_style="bold magenta")
        table.add_column("Código", style="cyan", width=8)
        table.add_column("Categoría", style="yellow")
        table.add_column("Sev", style="bold", width=8)
        table.add_column("Ubicación", style="blue")
        table.add_column("Mensaje y Sugerencia", style="white")

        for iss in all_issues:
            sev_color = "red" if iss.severity == "ERROR" else "yellow"
            table.add_row(
                iss.code,
                iss.category,
                f"[{sev_color}]{iss.severity}[/{sev_color}]",
                f"{Path(iss.file_path).name}:{iss.line_number}",
                f"{iss.message}\n[dim]↳ Sugerencia: {iss.suggestion}[/dim]"
            )
        console.print(table)

    if arch_statuses:
        arch_table = Table(title="Estado de Compilación Multi-Arquitectura", show_header=True)
        arch_table.add_column("Arquitectura", style="cyan")
        arch_table.add_column("Toolchain", style="blue")
        arch_table.add_column("Resultado", style="bold")

        for arch in arch_statuses:
            status_str = "[green]PASSED ✓[/green]" if arch.compilation_passed else "[red]FAILED ✗[/red]"
            avail_str = "Disponible" if arch.compiler_available else "No disponible"
            arch_table.add_row(arch.architecture, avail_str, status_str)
        console.print(arch_table)

    if not report.passed:
        raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    paths: List[Path] = typer.Argument(..., help="Archivos o directorios C a analizar"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
):
    """Genera directamente la sección de reporte Markdown de CROWE para Dredd."""
    files_to_check: List[Path] = []
    for p in paths:
        if p.is_file():
            files_to_check.append(p)
        elif p.is_dir():
            files_to_check.extend(list(p.glob("**/*.c")) + list(p.glob("**/*.h")))

    all_issues = []
    for f in files_to_check:
        all_issues.extend(lint_file_portability(f))

    has_errors = any(i.severity == "ERROR" for i in all_issues)
    report = PortabilityReport(
        files_analyzed=[str(f) for f in files_to_check],
        issues=all_issues,
        architectures=[],
        passed=not has_errors
    )
    md_content = generar_seccion_markdown(report)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)


@app.command()
def version():
    """Muestra la versión de CROWE."""
    from crowe import __version__
    console.print(f"[bold cyan]CROWE[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
