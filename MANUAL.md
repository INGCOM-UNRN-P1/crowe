# Manual de Uso y Referencia Técnica: crowe

> **CROWE** — Linter de portabilidad multi-arquitectura (x86_64, ARM, RISC-V, endianness) en C
> **Versión:** `0.1.0` · **CLI principal:** `crowe` · **Plugin Ripley:** `portability`

---

## 1. Arquitectura y Propósito Pedagógico

`crowe` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Auditoría estática de portabilidad multi-arquitectura en código fuente C (reglas `CRW001` a `CRW005`).
- Detección de truncamiento por casteo de puntero a `int` en 64 bits (`CRW001`).
- Detección de asunciones de signo sobre `char` (`CRW002`) y orden de bytes (`CRW003`).
- Detección de suposiciones rígidas sobre el ancho de `long` (`CRW004`).
- Detección de arreglos de longitud variable (VLAs) con riesgo de desbordamiento de pila (`CRW005`).

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Emulación o ejecución de binarios de hardware con QEMU (fuera del alcance).
- Auditoría del alineamiento interno de campos de structs (delegado a `brett`).
- Inspección de endianness en disco (delegado a `kane`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/crowe
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
crowe doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`crowe lint`](#lint) | Analiza archivos C buscando asunciones no portables de hardware y endianness. |
| [`crowe check`](#check) | Gate de portabilidad: lint + verificación multi-arquitectura (lo que invoca ripley). |
| [`crowe report`](#report) | Genera directamente la sección de reporte Markdown de CROWE para Dredd. |
| [`crowe doctor`](#doctor) | Verifica el estado del entorno de auditoría de portabilidad CROWE (Python, GCC nativo y cross-compiladores). |

### `crowe lint`

Analiza archivos C buscando asunciones no portables de hardware y endianness.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `paths` | `List[pathlib._local.Path]` | Archivos o directorios C a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--cross-compile/--no-cross-compile`, `-c` | `<class 'bool'>` | `False` | Intentar compilación contra toolchains x86_64, aarch64 y riscv64 (por defecto desactivada en `lint`). |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
crowe lint <paths>
```

### `crowe check`

Gate de portabilidad: lint + verificación multi-arquitectura (lo que invoca ripley).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `paths` | `List[pathlib._local.Path]` | Archivos o directorios C a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--cross-compile/--no-cross-compile`, `-c` | `<class 'bool'>` | `True` | Verificar compilación contra toolchains x86_64, aarch64 y riscv64 (por defecto activada en `check`, el punto de entrada de ripley). |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
crowe check <paths>
```

### `crowe report`

Genera directamente la sección de reporte Markdown de CROWE para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `paths` | `List[pathlib._local.Path]` | Archivos o directorios C a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[pathlib._local.Path]` | `None` | Ruta de destino del archivo Markdown. |

#### Ejemplo de Invocación
```bash
crowe report <paths>
```

### `crowe doctor`

Verifica el estado del entorno de auditoría de portabilidad CROWE (Python, GCC nativo y cross-compiladores).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
crowe doctor
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
crowe lint --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: crowe, tool=crowe, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`crowe` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
crowe doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.