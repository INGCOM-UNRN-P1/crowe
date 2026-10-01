# CROWE — Linter de Portabilidad Multi-Arquitectura en C

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

**CROWE** analiza código C para detectar asunciones no portables de hardware (endianness, tamaños fijos de punteros, signo de `char`, VLAs y tamaños de `long`) y opcionalmente valida compilación cruzada para `x86_64`, `aarch64` y `riscv64`.

---

## 🎯 Alcance

### Qué cubre
- Auditoría estática de portabilidad multi-arquitectura en código fuente C (reglas `CRW001` a `CRW005`).
- Detección de truncamiento por casteo de puntero a `int` en 64 bits (`CRW001`).
- Detección de asunciones de signo sobre `char` (`CRW002`) y orden de bytes (`CRW003`).
- Detección de suposiciones rígidas sobre el ancho de `long` (`CRW004`).
- Detección de arreglos de longitud variable (VLAs) con riesgo de desbordamiento de pila (`CRW005`).

### Qué no cubre (Límites y Delegación)
- Emulación o ejecución de binarios de hardware con QEMU (fuera del alcance).
- Auditoría del alineamiento interno de campos de structs (delegado a `brett`).
- Inspección de endianness en disco (delegado a `kane`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio para análisis estático; compiladores GCC cruzados (`aarch64-linux-gnu-gcc`, `riscv64-linux-gnu-gcc`) opcionales para `--cross-compile`.

### Integración en el Ecosistema
- CLI `crowe`. Plugin registrado en `ripley.plugins` (`portability`).

---

## 🚀 Uso Rápido

```bash
# Auditar portabilidad en archivos C
crowe lint src/
crowe check src/

# Generar informe en formato Markdown
crowe report src/

# Probar compilación multi-arquitectura
crowe lint src/ --cross-compile

# Salida estructurada en JSON
crowe lint src/ --json
```

---

## 🔍 Reglas Auditadas

- **`CRW001`**: Casteo de puntero a `int` (provoca truncamiento en arquitecturas de 64 bits).
- **`CRW002`**: Uso de `char` esperando valores negativos (en ARM es `unsigned char` por defecto).
- **`CRW003`**: Asunciones fijas de orden de bytes (Endianness).
- **`CRW004`**: Suposición del tamaño de `long` (`sizeof(long) == 4` vs `8`).
- **`CRW005`**: Uso de Variable-Length Arrays (VLAs) con riesgo de desbordamiento de pila.

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).

### Comandos

| Comando | Descripción |
|:--|:--|
| `crowe lint` | Analiza archivos C buscando asunciones no portables de hardware y endianness. |
| `crowe check` | Gate de portabilidad: lint + verificación multi-arquitectura (lo que invoca ripley). |
| `crowe report` | Genera directamente la sección de reporte Markdown de CROWE para Dredd. |
| `crowe doctor` | Verifica el estado del entorno de auditoría de portabilidad CROWE (Python, GCC nativo y cross-compiladores). |

Ayuda de cada comando: `crowe <comando> -h`.

### Salida JSON

Con `--json`, estos comandos emiten el resultado como JSON por la salida estándar, para usarlo desde scripts, ripley o dredd: `crowe lint`, `crowe check`, `crowe doctor`. El de `doctor --json` lleva `schema_version` y `ok`.

### Códigos de salida

| Código | Significado |
|:--|:--|
| `0` | Terminó bien (en `doctor`: está todo lo requerido). |
| `1` | El comando encontró problemas (hallazgos, pruebas que fallan, un umbral que no se alcanza) o un dato no se pudo usar (un archivo ilegible, un formato inválido). |
| `2` | Error de uso: comando, opción o argumento inválido. |

<!-- p1:referencia:fin -->
