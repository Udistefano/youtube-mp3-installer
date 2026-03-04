document.getElementById('btn-descargar').addEventListener('click', async () => {
  const url    = document.getElementById('url-input').value.trim();
  const estado = document.getElementById('estado');

  if (!url) {
    estado.textContent = 'Ingresá un link de YouTube.';
    return;
  }

  estado.textContent = 'Descargando... no cierres la página.';

  try {
    const res = await fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      estado.textContent = 'Error: ' + err.error;
      return;
    }

    // Convertimos la respuesta en un blob (archivo binario)
    const blob = await res.blob();

    // Creamos una URL temporal apuntando al blob
    const urlBlob = URL.createObjectURL(blob);

    // Creamos un link invisible, lo clickeamos y lo borramos
    const link    = document.createElement('a');
    link.href     = urlBlob;
    const header  = res.headers.get('Content-Disposition');
    const nombre = header ? header.split('filename=')[1].split(';')[0].replace(/"/g, '').trim() : 'audio.mp3';
    link.download = nombre;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    // Limpiamos
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(urlBlob);
    }, 1000);

    estado.textContent = "Descarga completada. Revisá tu carpeta de Descargas.";

  } catch (e) {
    console.error(e);
    estado.textContent = 'Algo salió mal. Revisá la consola (F12).';
  }
});