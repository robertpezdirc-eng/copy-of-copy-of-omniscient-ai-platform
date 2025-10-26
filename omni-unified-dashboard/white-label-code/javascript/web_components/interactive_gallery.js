export function initInteractiveGallery(selector) {
  const root = document.querySelector(selector);
  if (!root) return;
  root.querySelectorAll('img').forEach(img => {
    img.addEventListener('click', () => {
      alert('Galerija – klik na sliko');
    });
  });
}