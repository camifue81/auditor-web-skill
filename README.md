# web-audit · Skill auditora de proyectos React/JavaScript

**Autora:** Camila Avril Fuentes Flores
**Materia:** Práctica de Skills para agentes de IA

Skill para agentes de código (Codex, Claude Code u otros compatibles con `SKILL.md`) que **audita un proyecto web React/JavaScript**, detecta errores comunes y genera un **reporte HTML y JSON** con puntaje, severidad, archivo y línea de cada problema. Está inspirada en la skill `review-progress` vista en clase, pero es un motor configurable: las reglas viven en un JSON, el reporte usa una plantilla y el agente consulta un catálogo de arreglos.

![Reporte HTML](docs/capturas/01-reporte-html.png)

---

## 1. ¿Cuándo y para qué se usa?

Cuando se pide "revisa / audita / busca errores en mi proyecto React", antes de entregar una práctica o de hacer un pull request. Detecta 14 tipos de problemas:

| Severidad | Reglas |
|-----------|--------|
| **Alta** (−10) | Mutación directa del estado (`cart.push`), `debugger`, `eval`, credenciales en el código |
| **Media** (−5) | `.map()` sin `key`, `useEffect` sin dependencias, `fetch` sin manejo de errores, `==`, `dangerouslySetInnerHTML`, URLs `http://` |
| **Baja** (−2) | `console.log`, `alert`, `var`, `TODO/FIXME` |

Puntaje = 100 − penalizaciones → **Excelente** (≥90), **Aceptable** (≥70), **Necesita mejoras** (≥50), **Crítico** (<50).

## 2. Estructura

```
auditor-web-skill/
├── web-audit/                     ← LA SKILL (esta carpeta es la que se instala)
│   ├── SKILL.md                   ← cuándo usarla y flujo paso a paso para el agente
│   ├── scripts/
│   │   └── audit.py               ← motor: lee reglas, analiza, genera reportes
│   ├── assets/
│   │   ├── rules.json             ← catálogo de reglas, severidades y penalizaciones
│   │   └── report_template.html   ← plantilla visual del reporte
│   └── references/
│       ├── reglas.md              ← por qué cada regla es un problema y cómo corregirla
│       └── agregar-reglas.md      ← cómo extender la skill
├── examples/
│   ├── tienda-con-errores/        ← proyecto React con errores a propósito
│   ├── proyecto-limpio/           ← mismo proyecto corregido (puntaje 100)
│   ├── proyecto-python/           ← caso inválido: no es JavaScript
│   └── reglas-rotas.json          ← caso inválido: JSON corrupto
├── tests/test_audit.py            ← 16 pruebas automáticas (unittest)
├── docs/capturas/                 ← evidencia de funcionamiento
└── demo.py                        ← ejecuta todos los escenarios de la demostración
```

**Cómo se usa cada parte:**

- `SKILL.md` le dice al agente cuándo activarse y qué pasos seguir (ejecutar, interpretar el código de salida, confirmar hallazgos, proponer arreglos).
- `scripts/audit.py` carga `assets/rules.json`, analiza el código y rellena `assets/report_template.html`.
- `references/reglas.md` es la fuente de los arreglos que el agente propone al usuario.

## 3. Requisitos

- **Python 3.8 o superior.** No necesita librerías externas (solo biblioteca estándar).
- Git (para clonar).
- Opcional: un agente compatible con skills (Codex CLI, Claude Code) para usarla como skill. El script también funciona solo, desde la terminal.

Comprobar Python: `python --version` (Windows) o `python3 --version` (Linux/macOS).

## 4. Instalación

```bash
git clone https://github.com/camifue81/auditor-web-skill.git
cd auditor-web-skill
```

**Como skill de un agente**, copia la carpeta `web-audit/` a la carpeta de skills:

| Agente | Destino (en el proyecto) | Destino (global) |
|--------|--------------------------|------------------|
| Codex (como en clase) | `.codex/skills/web-audit/` | `~/.codex/skills/web-audit/` |
| Claude Code | `.claude/skills/web-audit/` | `~/.claude/skills/web-audit/` |

Ejemplo en Windows (PowerShell), para el proyecto de clase `Practica1`:

```powershell
Copy-Item -Recurse web-audit ..\Practica1\.codex\skills\web-audit
```

Luego, en el agente: *"Audita este proyecto con la skill web-audit"*.

## 5. Ejecución directa

```bash
# Windows
python web-audit/scripts/audit.py examples/tienda-con-errores --out examples/tienda-con-errores/audit-report

# Linux / macOS
python3 web-audit/scripts/audit.py examples/tienda-con-errores --out examples/tienda-con-errores/audit-report
```

Opciones:

| Opción | Descripción |
|--------|-------------|
| `<proyecto>` | Carpeta del proyecto a auditar (obligatorio) |
| `--out CARPETA` | Dónde guardar `reporte.html` y `reporte.json` (por defecto `audit-report`) |
| `--fail-on alta\|media\|baja` | Devuelve código 1 si hay hallazgos de ese nivel o mayor (para CI) |
| `--rules ARCHIVO` | Usa otro archivo de reglas |

**Demostración completa** (los 5 escenarios de una sola vez): `python demo.py`

## 6. Ejemplo de entrada y resultado esperado

**Entrada:** `examples/tienda-con-errores/src/App.jsx` (fragmento)

```jsx
useEffect(() => {
  fetch(`${API_URL}/products`)
    .then((res) => res.json())
    .then((data) => setProducts(data.products))
})                                   // sin dependencias ni manejo de errores

function addToCart(product) {
  console.log('agregando', product)
  cart.push({ ...product, quantity: 1 })   // muta el estado
  setCart(cart)
}
```

**Resultado esperado en consola:**

```
Proyecto auditado : tienda-con-errores
Archivos revisados: 4
Puntaje           : 22/100 (Crítico)
Hallazgos         : 14 (alta: 4, media: 6, baja: 4)

Principales hallazgos:
  [ALTA ] src/App.jsx:19  mutacion-estado
  [ALTA ] src/App.jsx:25  mutacion-estado
  [ALTA ] src/App.jsx:30  debugger
  [ALTA ] src/config.js:2  secreto-en-codigo
  [MEDIA] src/App.jsx:11  effect-sin-deps
  [MEDIA] src/App.jsx:12  fetch-sin-errores
  ...
Reporte HTML: .../audit-report/reporte.html
Reporte JSON: .../audit-report/reporte.json
```

Además se generan `reporte.html` (ver captura arriba) y `reporte.json`:

```json
{
  "project": "tienda-con-errores",
  "score": 22,
  "grade": "Crítico",
  "counts": { "alta": 4, "media": 6, "baja": 4 },
  "findings": [
    { "rule": "mutacion-estado", "severity": "alta", "file": "src/App.jsx", "line": 19,
      "code": "cart.push({ ...product, quantity: 1 })", "message": "Se modifica directamente..." }
  ]
}
```

El proyecto corregido `examples/proyecto-limpio` obtiene **100/100 (Excelente)** con 0 hallazgos.

**Con el proyecto de clase** (`Practica1`, la Tienda Tech) la skill encuentra la mutación `cart.push` (App.jsx:32), el `fetch` sin manejo de errores y un `alert`: **83/100**.

## 7. Pruebas y manejo de errores

```bash
python -m unittest discover -s tests -v
```

16 pruebas: casos exitosos, cada regla especial (estado, `key`, `useEffect`, `fetch`) y los casos de error.

| Situación | Mensaje | Código |
|-----------|---------|--------|
| Auditoría correcta | Resumen + reportes | 0 |
| `--fail-on` y hay hallazgos de ese nivel | `Resultado: FALLA ...` | 1 |
| La carpeta no existe | `ERROR: La ruta no existe: ...` | 2 |
| Se pasó un archivo en vez de carpeta | `ERROR: La ruta debe ser una carpeta de proyecto...` | 2 |
| No hay archivos .js/.jsx/.ts/.tsx | `ERROR: No se encontraron archivos ...` | 3 |
| `rules.json` corrupto o regla inválida | `ERROR: El archivo de reglas no es JSON válido (línea N)...` | 4 |
| Archivo con codificación Latin-1 | Se lee igual (no se rompe) | 0 |
| Archivo enorme (minificado) | Se omite con `AVISO:` | 0 |

Capturas en [`docs/capturas/`](docs/capturas):

| Captura | Muestra |
|---------|---------|
| `01-reporte-html.png` | Reporte HTML del proyecto con errores |
| `02-consola-exito.png` | Ejecución exitosa en la terminal |
| `03-proyecto-limpio.png` | Reporte del proyecto corregido (100/100) |
| `04-errores.png` | Entradas inválidas y sus códigos de salida |
| `05-tests.png` | Las 16 pruebas pasando |

Guion de la demostración: [`docs/presentacion.md`](docs/presentacion.md).

## 8. Decisiones de diseño

1. **Solo biblioteca estándar de Python:** se instala copiando una carpeta, sin `pip install`, y funciona igual en Windows y Linux.
2. **Reglas en `assets/rules.json`, no en el código:** se pueden agregar reglas sin programar (ver `references/agregar-reglas.md`). Lo que no se puede expresar con una regex (mutación de estado, `useEffect`, `.map` sin key) se implementó como `check` en Python.
3. **Detección de estado real:** `mutacion-estado` primero busca qué variables vienen de `useState` y solo marca esas; así `const lista = []; lista.push()` no es un falso positivo.
4. **Dos salidas:** HTML para personas y JSON para que el agente lo lea y proponga arreglos.
5. **Códigos de salida distintos por error:** el agente sabe exactamente qué pasó y qué pedir al usuario (tabla en `SKILL.md`).
6. **El agente confirma antes de corregir:** el análisis es por patrones, así que `SKILL.md` exige leer la línea antes de proponer un cambio. Las limitaciones están documentadas en `references/reglas.md`.
