---
name: web-audit
description: Audita un proyecto JavaScript/React (Vite, CRA, Next) buscando errores comunes de React, seguridad, manejo de APIs y código de depuración olvidado, y genera un reporte HTML y JSON con puntaje, severidad, archivo y línea. Úsala cuando el usuario pida "revisar", "auditar", "buscar errores" o "evaluar la calidad" de un proyecto web/React, o antes de entregar o desplegar uno.
---

# web-audit: auditor de proyectos web React/JS

## Cuándo usar esta skill

- El usuario pide revisar, auditar o encontrar errores en un proyecto React o JavaScript.
- Antes de entregar una práctica, abrir un pull request o desplegar.
- Para comparar la calidad antes y después de una corrección (el puntaje debe subir).

**No usarla** para proyectos que no son JavaScript/TypeScript (Python, Java, etc.): el script terminará con el código 3.

## Qué revisa

14 reglas definidas en `assets/rules.json`, agrupadas por severidad:

- **Alta:** mutación directa del estado de `useState`, `debugger`, `eval`, credenciales en el código.
- **Media:** `.map()` sin `key`, `useEffect` sin dependencias, `fetch` sin manejo de errores, `==`, `dangerouslySetInnerHTML`, URLs `http://`.
- **Baja:** `console.log`, `alert`, `var`, comentarios `TODO/FIXME`.

La explicación y el arreglo de cada regla están en `references/reglas.md`.

## Flujo de trabajo

1. **Ubicar el proyecto.** Confirma la carpeta raíz del proyecto (la que contiene `src/` o `package.json`). Si el usuario no la indica, usa el directorio actual.

2. **Ejecutar la auditoría** desde la carpeta de la skill (requiere Python 3.8+, sin dependencias externas):

   ```bash
   python scripts/audit.py <carpeta_del_proyecto> --out <carpeta_del_proyecto>/audit-report
   ```

   En Linux/macOS puede ser `python3`. Opcional: `--fail-on alta` para que el comando devuelva código 1 si hay hallazgos graves (útil en CI).

3. **Revisar el código de salida:**

   | Código | Significado | Qué hacer |
   |--------|-------------|-----------|
   | 0 | Auditoría completa | Continuar al paso 4 |
   | 1 | Hay hallazgos ≥ `--fail-on` | Continuar al paso 4 y marcar el resultado como FALLA |
   | 2 | La ruta no existe o es un archivo | Pedir al usuario la carpeta correcta |
   | 3 | No hay archivos .js/.jsx/.ts/.tsx | Avisar que la skill no aplica a ese proyecto |
   | 4 | `rules.json` o la plantilla son inválidos | Mostrar el mensaje de error; revisar `references/agregar-reglas.md` |

4. **Leer `audit-report/reporte.json`** y, para los hallazgos de severidad alta y media, **abrir el archivo en la línea indicada** para confirmar que no sea un falso positivo (ver "Limitaciones" en `references/reglas.md`).

5. **Responder al usuario** con:
   - Puntaje y calificación (`score`, `grade`).
   - Tabla de hallazgos confirmados, primero los de severidad alta: archivo:línea, problema y arreglo propuesto tomado de `references/reglas.md`.
   - Ruta del reporte HTML (`audit-report/reporte.html`) para abrirlo en el navegador.

6. **Si el usuario pide corregir:** aplica los arreglos uno por uno, vuelve a ejecutar el paso 2 y muestra el puntaje antes/después.

## Recursos de la skill

| Ruta | Para qué se usa |
|------|-----------------|
| `scripts/audit.py` | Motor de la auditoría: lee reglas, analiza archivos, genera HTML y JSON |
| `assets/rules.json` | Catálogo de reglas, extensiones, carpetas ignoradas y penalizaciones |
| `assets/report_template.html` | Plantilla visual del reporte (marcadores `{{...}}`) |
| `references/reglas.md` | Por qué cada regla es un problema y cómo corregirla; limitaciones |
| `references/agregar-reglas.md` | Cómo extender la skill con nuevas reglas |

## Ejemplo

Entrada: `python scripts/audit.py ../examples/tienda-con-errores --out ../examples/tienda-con-errores/audit-report`

Salida en consola (resumen):

```
Proyecto auditado : tienda-con-errores
Archivos revisados: 4
Puntaje           : 22/100 (Crítico)
Hallazgos         : 14 (alta: 4, media: 6, baja: 4)
```

Y se generan `reporte.html` y `reporte.json` en la carpeta `audit-report`.
