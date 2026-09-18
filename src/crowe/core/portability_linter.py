"""Linter estático de reglas de portabilidad arquitectónica en C."""

import re
from pathlib import Path
from typing import List, Set
from crowe.core.models import PortabilityIssue
from crowe.core.preprocesador import enmascarar_bloques_inactivos

# CRW002 y CRW005 no se pueden resolver con un regex de una sola línea sin
# falsos positivos masivos: necesitan saber si un identificador es realmente
# `char` o si el corchete de un arreglo es una macro en vez de una variable.
# Se recolectan en una pasada previa sobre el archivo completo.
_DECL_CHAR = re.compile(r'\bchar\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|;|,|\[)')
_DEFINE_MACRO = re.compile(r'^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)', re.MULTILINE)
_IF_LT_ZERO = re.compile(r'\bif\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*<\s*0\s*\)')
_CHAR_LITERAL_NEGATIVO = re.compile(r'\bchar\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*-\d+')
_VLA_CANDIDATA = re.compile(r'\b[a-zA-Z0-9_]+\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\]\s*;')


def _recolectar_chars_y_macros(contenido: str) -> tuple[Set[str], Set[str]]:
    """Recorre el archivo completo para saber qué identificadores son `char` y cuáles macros."""
    chars = set(m.group(1) for m in _DECL_CHAR.finditer(contenido))
    macros = set(m.group(1) for m in _DEFINE_MACRO.finditer(contenido))
    return chars, macros

# Reglas estáticas de portabilidad
PATTERNS = [
    (
        "CRW001",
        "POINTER_SIZE",
        "ERROR",
        re.compile(r'\(\s*(?:int|unsigned\s+int)\s*\)\s*[a-zA-Z_][a-zA-Z0-9_]*->|[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\(\s*(?:int|unsigned\s+int)\s*\)\s*&?[a-zA-Z_]'),
        "Casteo directo de puntero a 'int' (32 bits en x86_64/ARM64). Provoca truncamiento de direcciones de 64 bits.",
        "Utilizá 'uintptr_t' o 'intptr_t' de <stdint.h> para representar punteros como enteros de forma portable."
    ),
    (
        "CRW002",
        "CHAR_SIGN",
        "WARNING",
        re.compile(r'\bchar\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*-\d+|\bif\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*<\s*0\s*\)'),
        "Uso de 'char' asumiendo que tiene signo. En arquitecturas ARM y PowerPC, 'char' es 'unsigned char' por defecto.",
        "Declaralo explícitamente como 'signed char' o 'int8_t' si requiere valores negativos."
    ),
    (
        "CRW003",
        "ENDIANNESS",
        "WARNING",
        re.compile(r'\*\s*\(\s*char\s*\*\s*\)\s*&\s*[a-zA-Z_]|memcpy\s*\([^,]+,\s*&[a-zA-Z_][^,]*,\s*1\s*\)'),
        "Inspección directa del primer byte de un entero. Depende del orden de bytes de la arquitectura (Little vs Big Endian).",
        "Utilizá operadores de desplazamiento de bits (>> / <<) o funciones estándar de conversión de endianness (htons, ntohl)."
    ),
    (
        "CRW004",
        "TYPE_SIZE",
        "WARNING",
        re.compile(r'\b(?:sizeof\s*\(\s*long\s*\)\s*==\s*4|sizeof\s*\(\s*long\s*\)\s*==\s*8)'),
        "Asunción fija sobre el tamaño de 'long'. En Windows x64 'long' tiene 4 bytes (LLP64), mientras que en Linux x86_64 tiene 8 bytes (LP64).",
        "Utilizá tipos de ancho fijo de <stdint.h> como 'int32_t' o 'int64_t'."
    ),
    (
        "CRW005",
        "VLA",
        "INFO",
        re.compile(r'\b[a-zA-Z0-9_]+\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\[\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\]\s*;'),
        "Uso de Variable-Length Array (VLA). Los VLAs son opcionales en C11 y pueden provocar desbordamiento de pila (Stack Overflow) en sistemas embebidos.",
        "Considerá usar asignación dinámica en Heap con 'malloc' o un búfer de tamaño máximo estático."
    ),
]


def lint_file_portability(file_path: Path) -> List[PortabilityIssue]:
    """Analiza un archivo fuente C en busca de violaciones de portabilidad."""
    issues = []
    content = file_path.read_text(encoding="utf-8", errors="replace")
    # El contenido de un `#if 0` no se compila: enmascararlo evita
    # reportar hallazgos sobre código deliberadamente desactivado.
    content = enmascarar_bloques_inactivos(content)
    lines = content.splitlines()
    chars, macros = _recolectar_chars_y_macros(content)

    for idx, line in enumerate(lines, 1):
        # Ignorar comentarios puros
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        for code, category, severity, pattern, msg, suggestion in PATTERNS:
            if code == "CRW002":
                # `if (var < 0)` es un idioma común de C con cualquier entero
                # con signo; solo es sospechoso si `var` es de verdad `char`.
                if _CHAR_LITERAL_NEGATIVO.search(line):
                    coincide = True
                else:
                    m = _IF_LT_ZERO.search(line)
                    coincide = bool(m and m.group(1) in chars)
            elif code == "CRW005":
                # `int buf[MAX]` con `MAX` definida por macro no es un VLA: el
                # tamaño es una constante de compilación, no una variable.
                m = _VLA_CANDIDATA.search(line)
                coincide = bool(m and m.group(1) not in macros)
            else:
                coincide = bool(pattern.search(line))

            if coincide:
                issues.append(PortabilityIssue(
                    code=code,
                    category=category,
                    severity=severity,
                    file_path=str(file_path),
                    line_number=idx,
                    line_content=stripped,
                    message=msg,
                    suggestion=suggestion
                ))

    return issues
