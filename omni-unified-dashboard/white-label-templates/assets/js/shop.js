let products = [];
const elProducts = document.getElementById('products');
const elSearch = document.getElementById('search');
const elCategory = document.getElementById('category');

function render(list) {
  elProducts.innerHTML = '';
  list.forEach(p => {
    const el = document.createElement('div');
    el.className = 'product';
    el.innerHTML = `
      <img src="../web/assets/img/placeholder.svg" alt="${p.title}" />
      <h3>${p.title}</h3>
      <div class="price">${p.price} €</div>
      <div class="category">${p.category}</div>
      <button class="btn primary">Dodaj v košarico</button>
    `;
    elProducts.appendChild(el);
  });
}

function applyFilters() {
  const q = (elSearch.value || '').toLowerCase();
  const cat = elCategory.value || '';
  const filtered = products.filter(p => {
    const okQ = !q || p.title.toLowerCase().includes(q);
    const okC = !cat || p.category === cat;
    return okQ && okC;
  });
  render(filtered);
}

async function init() {
  try {
    const res = await fetch('../code/javascript/data/products.json');
    products = await res.json();
    render(products);
  } catch (e) {
    console.warn('Ni mogoče naložiti izdelkov:', e);
  }
}

elSearch.addEventListener('input', applyFilters);
elCategory.addEventListener('change', applyFilters);
init();