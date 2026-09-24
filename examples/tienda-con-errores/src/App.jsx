import { useEffect, useState } from 'react'
import ProductList from './ProductList'
import { API_URL } from './config'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')

  // TODO: mover la carga a un hook propio
  useEffect(() => {
    fetch(`${API_URL}/products`)
      .then((res) => res.json())
      .then((data) => setProducts(data.products))
  })

  function addToCart(product) {
    console.log('agregando', product)
    cart.push({ ...product, quantity: 1 })
    setCart(cart)
  }

  function removeFromCart(id) {
    var index = cart.findIndex((item) => item.id == id)
    cart.splice(index, 1)
    setCart([...cart])
  }

  function checkout() {
    debugger
    alert('Gracias por su compra')
  }

  const visible = products.filter((p) => p.title.includes(search))

  return (
    <main>
      <input value={search} onChange={(e) => setSearch(e.target.value)} />
      <ProductList products={visible} onAdd={addToCart} />
      <ul>
        {cart.map((item) => (
          <li>
            {item.title} x {item.quantity}
            <button onClick={() => removeFromCart(item.id)}>Quitar</button>
          </li>
        ))}
      </ul>
      <button onClick={checkout}>Pagar</button>
    </main>
  )
}

export default App
