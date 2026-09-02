# CROWE — Linter de Portabilidad Multi-Arquitectura en C

**CROWE** analiza código C para detectar asunciones no portables de hardware (endianness, tamaños fijos de punteros, signo de `char`, VLAs y tamaños de `long`) y opcionalmente valida compilación cruzada para `x86_64`, `aarch64` y `riscv64`.

---

## 🎯 Alcance

### Qué cubre
- Auditoría estática de portabilidad multi-arquitectura en código fuente C.
- Detección de uso de tipos con tamaño dependiente de la arquitectura (`long`, `unsigned long`, `size_t`, punteros) sin utilizar `<stdint.h>`.
- Detección de asunciones rígidas sobre el ancho de palabra (32 bits vs 64 bits).
- Detección de pasaje de estructuras voluminosas por valor a través de la pila en lugar de punteros constantes.

### Qué no cubre (Límites y Delegación)
- Compilación cruzada real ni emulación de hardware con QEMU (delegado al toolchain de cátedra).
- Auditoría del alineamiento interno de campos de structs (delegado a `brett`).
- Inspección de endianness en disco (delegado a `kane`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio (análisis estático con Tree-Sitter).

### Integración en el Ecosistema
- CLI `crowe`. Plugin registrado en `ripley.plugins` (`portability`).

---

## 🚀 Uso Rápido

```bash
# Auditar portabilidad en archivos C
crowe lint src/

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
