async function loadPosts() {
  try {
    const res = await fetch('../docs/blog_posts.json');
    const posts = await res.json();
    const container = document.getElementById('posts');
    container.innerHTML = '';
    posts.forEach(p => {
      const el = document.createElement('div');
      el.className = 'post';
      el.innerHTML = `
        <h3>${p.title}</h3>
        <div class="meta">${p.date} · ${p.category}</div>
        <p>${p.excerpt}</p>
      `;
      container.appendChild(el);
    });
  } catch (e) {
    console.warn('Ni mogoče naložiti blog objav:', e);
  }
}
loadPosts();