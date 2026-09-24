import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'https://dummyjson.com'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/products`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => setProducts(data.products))
      .catch((err) => setError(err.message))
  }, [])

  function addToCart(product) {
    setCart((prev) => [...prev, { ...product, quantity: 1 }])
  }

  function removeFromCart(id) {
    setCart((prev) => prev.filter((item) => item.id !== id))
  }

  if (error) return <p role="alert">No se pudieron cargar los productos: {error}</p>

  return (
    <main>
      <section className="grid">
        {products.map((p) => (
          <article key={p.id}>
            <h3>{p.title}</h3>
            <button onClick={() => addToCart(p)}>Agregar</button>
          </article>
        ))}
      </section>
      <ul>
        {cart.map((item) => (
          <li key={item.id}>
            {item.title}
            <button onClick={() => removeFromCart(item.id)}>Quitar</button>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App
