# Catálogo de reglas de web-audit

Este documento explica **por qué** cada regla es un problema y **cómo corregirlo**.
El agente lo consulta después de ejecutar `scripts/audit.py` para proponer arreglos concretos.
Los identificadores coinciden con el campo `id` de `assets/rules.json`.

| Severidad | Penalización | Significado |
|-----------|--------------|-------------|
| alta      | −10          | Rompe la app, es un riesgo de seguridad o produce datos incorrectos |
| media     | −5           | Puede fallar en ciertos casos o degrada la calidad |
| baja      | −2           | Limpieza, estilo o mantenimiento |

---

## Severidad alta

### `mutacion-estado`
**Problema:** se modifica un valor de `useState` directamente (`cart.push(x)`, `items[0] = y`, `lista.sort()`).
React compara referencias; si el arreglo es el mismo, puede no volver a renderizar.

```jsx
// Mal
cart.push(product)
setCart(cart)

// Bien
setCart([...cart, product])
setCart(prev => prev.map(i => i.id === id ? { ...i, quantity: i.quantity + 1 } : i))
const ordenados = [...lista].sort(comparar)
```

### `debugger`
**Problema:** detiene la ejecución si las DevTools están abiertas. **Arreglo:** borrar la línea.

### `eval`
**Problema:** ejecuta texto como código; si el texto viene del usuario, es inyección de código.
**Arreglo:** usar `JSON.parse` para datos, o una función/objeto de mapeo explícito.

### `secreto-en-codigo`
**Problema:** claves de API o contraseñas escritas en el código terminan en el repositorio y en el navegador.
**Arreglo:** moverlas a variables de entorno (`import.meta.env.VITE_API_URL` en Vite) y agregar `.env` al `.gitignore`.
Recordar que en el frontend **nada es secreto**: las claves privadas deben quedarse en un backend.

---

## Severidad media

### `map-sin-key`
**Problema:** React necesita `key` estable para identificar cada elemento de una lista; sin ella hay advertencias y errores de renderizado al reordenar o eliminar.

```jsx
// Mal
{productos.map(p => <ProductCard product={p} />)}
// Bien (usar un id, no el índice si la lista cambia)
{productos.map(p => <ProductCard key={p.id} product={p} />)}
```

### `effect-sin-deps`
**Problema:** `useEffect(() => { ... })` sin segundo argumento se ejecuta tras **cada** render. Si dentro se hace `setState` o `fetch`, se genera un bucle infinito de peticiones.

```jsx
// Bien: solo al montar
useEffect(() => { cargarProductos() }, [])
// Bien: cuando cambia "busqueda"
useEffect(() => { filtrar(busqueda) }, [busqueda])
```

### `fetch-sin-errores`
**Problema:** `fetch` solo rechaza la promesa ante fallos de red; un 404 o 500 **no** lanza error. Sin manejo, la app queda en "Cargando..." para siempre o falla al leer datos inexistentes.

```jsx
fetch(url)
  .then(res => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  })
  .then(data => setProductos(data.products))
  .catch(err => setError(err.message))
```

### `igualdad-debil`
**Problema:** `==` convierte tipos (`'1' == 1` es `true`, `0 == ''` es `true`). **Arreglo:** usar `===` / `!==`.

### `inner-html`
**Problema:** `dangerouslySetInnerHTML` inserta HTML sin escapar (riesgo XSS).
**Arreglo:** renderizar texto normal con `{texto}`, o sanear el HTML (p. ej. DOMPurify) si es imprescindible.

### `url-http`
**Problema:** peticiones sin cifrar; los navegadores bloquean contenido mixto en sitios `https`.
**Arreglo:** cambiar a `https://`. (Se excluyen `localhost` y `127.0.0.1`.)

---

## Severidad baja

### `console-log`
Registros de depuración olvidados. Borrarlos o usar un logger que se desactive en producción.

### `alert`
`alert()` bloquea la pestaña y no se puede estilizar. Mostrar un mensaje en el propio componente (estado `mensaje`).

### `var`
`var` tiene alcance de función y hoisting confuso. Usar `const` (por defecto) o `let` (si se reasigna).

### `todo`
Comentarios `TODO`/`FIXME`/`HACK` indican trabajo pendiente. Resolverlos o registrarlos como issue.

---

## Limitaciones conocidas (falsos positivos / negativos)

- El análisis es **estático y por patrones**, no ejecuta el código ni construye un AST completo.
- `igualdad-debil` puede marcar `==` dentro de strings o comentarios.
- `map-sin-key` revisa la **primera** etiqueta JSX dentro del `.map(...)`; si se usa `React.Fragment` con key en otra forma puede fallar.
- `fetch-sin-errores` se evalúa por archivo: si hay un `try` para otra cosa, se considera manejado.
- `mutacion-estado` solo detecta variables declaradas como `const [x, setX] = useState(...)`.

Ante un posible falso positivo, el agente debe **leer la línea indicada** y confirmarlo antes de proponer un cambio.
