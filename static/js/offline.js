if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('offline-btn');
  if (!btn) return;

  const CACHE_NAME = 'netzaro-offline-v1';
  const url = btn.dataset.url;

  caches.open(CACHE_NAME).then((cache) => {
    cache.match(url).then((match) => {
      if (match) {
        btn.textContent = '✔ Disponible sin conexión';
        btn.disabled = true;
      }
    });
  });

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'Descargando...';
    try {
      const cache = await caches.open(CACHE_NAME);
      await cache.add(url);
      btn.textContent = '✔ Disponible sin conexión';
    } catch (e) {
      btn.textContent = 'Error al guardar offline';
      btn.disabled = false;
    }
  });
});