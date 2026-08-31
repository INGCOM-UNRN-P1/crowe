---
title: "Manual de Referencia: crowe"
subtitle: "Crowe — Linter de Portabilidad Multi-Arquitectura, Endianness y Tipos de Ancho Fijo"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-crowe)=
# Crowe — Linter de Portabilidad Multi-Arquitectura, Endianness y Tipos de Ancho Fijo

````{abstract}
**Rol en el ecosistema:** Detección de asunciones no portables en C: tamaño de punteros, orden de bytes (Little vs Big Endian), alineación y uso de tipos primitivos no estándar.
````

---

(manual-crowe-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`crowe`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-crowe-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `crowe`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
crowe doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-crowe-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `crowe`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `crowe audit src/` | Audita el código fuente buscando incompatibilidades entre x86_64, ARM64 y 32-bit. |
| `crowe endianness src/serializador.c` | Detecta casteo directo de punteros o desplazamientos dependientes de Little Endian. |
| `crowe fix-types src/` | Sustituye tipos dependientes de plataforma por <stdint.h> (int32_t, uint64_t, size_t). |
| `crowe doctor` | Verifica toolchains cruzadas disponibles (GCC multiarch, QEMU user). |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-crowe-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
#include <stdio.h>
#include <stdint.h>

// Código no portable: asume que sizeof(long) == sizeof(void*) y Little Endian
void serializar_mal(unsigned long valor, char *buf) {
    *(unsigned long*)buf = valor; // Peligro de alineación y endianness
}

// Código portable auditado por Crowe
void serializar_bien(uint32_t valor, uint8_t *buf) {
    buf[0] = (uint8_t)(valor >> 24);
    buf[1] = (uint8_t)(valor >> 16);
    buf[2] = (uint8_t)(valor >> 8);
    buf[3] = (uint8_t)(valor);
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
crowe audit src/
````

### Salida Obtenida en Consola

````{code-block} text
[!] src/serializador.c:5:5: ALERTA DE PORTABILIDAD [CROWE-001]
    Casteo de puntero a tipo 'unsigned long*' asume tamaño de 8 bytes (falla en arquitecturas de 32 bits y Windows x64 donde sizeof(long)==4).
    Sugerencia: Utilizá uint32_t o uint64_t de <stdint.h> con serialización explícita byte a byte.
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-crowe-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`crowe`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Auditoría de Serializador Binario
Detectar problemas de orden de bytes en `src/protocolo.c`.

**Instrucción de ejecución:**
```bash
crowe endianness src/protocolo.c
```
````

````{solution} Desafío 1
```bash
crowe endianness src/protocolo.c
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Migración a Tipos de Ancho Fijo
Reemplazar `unsigned int` y `long` por `uint32_t` y `int64_t`.

**Instrucción de ejecución:**
```bash
crowe fix-types src/ -i
```
````

````{solution} Desafío 2
```bash
crowe fix-types src/ -i
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Simulación en Arquitectura Big Endian
Verificar el comportamiento bajo emulación MIPS/PowerPC con QEMU.

**Instrucción de ejecución:**
```bash
crowe audit src/ --target mips
```
````

````{solution} Desafío 3
```bash
crowe audit src/ --target mips
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-crowe-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `crowe` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-crowe:
	@echo "=== Ejecutando verificación con crowe ==="
	crowe check src/ include/

.PHONY: check-crowe
````

Ejecutá `make check-crowe` antes de cada commit para asegurar que tu código conserve el estado de aprobación.

---

(manual-crowe-arquitectura)=
## 7. Arquitectura Interna y Mecanismo Técnico

La herramienta **`crowe`** implementa un motor de alta precisión basado en:

- **Tecnología Núcleo:** `GCC Cross-Toolchains + QEMU User Emulation + Clang Target AST Matcher`.
- **Aislamiento y Determinismo:** Diseñada para operar sin efectos colaterales en entornos de integración continua (CI), terminales de estudiantes y servidores docentes headless.
- **Manejo de Errores Pedagógico:** Todo fallo de sintaxis, memoria o lógica se traduce en una acción prescriptiva concreta con su respectiva justificación técnica.

---

(manual-crowe-ecosistema)=
## 8. Integración y Conexión con el Ecosistema

````{note}
Ninguna herramienta opera de forma aislada. **`crowe`** forma parte del pipeline integral de evaluación, verificación y enseñanza de la cátedra.
````

### Diagrama de Flujo e Interoperabilidad

````{mermaid}
graph TD
    SRC[Código C] --> CRW[Crowe: Linter Multi-Arquitectura]
    CRW -->|Chequeo Endianness/Tipos| ABI[Modelos x86_64, ARM, 32-bit]
    CRW -->|Tipos Seguros stdint.h| DAE[Daedalus: Compilador Defensivo]
    CRW -->|Binario Portable| NOS[Nostromo: Sandbox Linux]
````

### Matriz de Intercambio de Datos

| Canal | Herramientas Conectadas | Tipo de Datos Transferidos |
| :--- | :--- | :--- |
| **Entradas (Inputs)** | - `Código fuente C (.c y .h)` | Código fuente, AST, binarios, testcases, contratos |
| **Salidas (Outputs)** | - `daedalus (compilación cruzada)`
- `nostromo (ejecución multiarch)` | Informes Markdown, diagnósticos Rich, JSON, actas |
| **Sincronización** | `brett`, `kane`, `ferro` | Validación cruzada, flags compartidos y autofix |

### Pipeline de Integración Recomendado

Podés encadenar `crowe` con otras herramientas del ecosistema en una única línea de comando:

````{code-block} bash
# Pipeline de integración típico
crowe audit src/ && daedalus compile src/*.c -o bin/app
````

