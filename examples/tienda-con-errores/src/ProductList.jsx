function ProductList({ products, onAdd }) {
  return (
    <section className="grid">
      {products.map((p) => (
        <article key={p.id} className="card">
          <h3>{p.title}</h3>
          <p dangerouslySetInnerHTML={{ __html: p.description }} />
          <button onClick={() => onAdd(p)}>Agregar</button>
        </article>
      ))}
    </section>
  )
}

export default ProductList
