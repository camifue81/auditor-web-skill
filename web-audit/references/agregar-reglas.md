# Cómo agregar o ajustar reglas

Las reglas viven en `assets/rules.json`. No hace falta tocar Python para agregar una regla de texto.

## Regla tipo `regex` (una línea)

```json
{
  "id": "localstorage",
  "type": "regex",
  "pattern": "\\blocalStorage\\.setItem\\(",
  "severity": "baja",
  "category": "Datos",
  "message": "Se guarda información en localStorage; revisa que no sea sensible."
}
```

- `pattern` es una expresión regular de Python aplicada **línea por línea**. Recuerda duplicar las barras invertidas (`\\b`) dentro del JSON.
- `severity` debe ser `alta`, `media` o `baja`; si no, el script termina con código 4.
- Documenta la nueva regla en `references/reglas.md` con su explicación y arreglo.

## Regla tipo `check` (lógica en Python)

Para reglas que necesitan mirar varias líneas (como `useEffect` o `.map`):

1. Escribe una función `check_xxx(text)` en `scripts/audit.py` que devuelva una lista de tuplas `(numero_de_linea, detalle)`.
2. Regístrala en el diccionario `CHECKS` con el mismo `id`.
3. Agrega la entrada en `rules.json` con `"type": "check"`.
4. Añade una prueba en `tests/test_audit.py`.

## Otros parámetros de `rules.json`

| Clave | Uso |
|-------|-----|
| `extensions` | Extensiones que se analizan |
| `ignore_dirs` | Carpetas que se saltan (node_modules, dist...) |
| `max_file_kb` | Archivos más grandes se omiten con un aviso (normalmente son código minificado) |
| `penalties` | Puntos que resta cada severidad |

Para usar un archivo de reglas distinto sin modificar el original: `python scripts/audit.py <proyecto> --rules mis_reglas.json`.
