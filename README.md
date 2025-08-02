Streamlit web-app que permite al usuario pegar prácticamente cualquier URL de vídeo soportada por **yt-dlp** y descargarla como un único archivo MP4.

Características principales
-------------
* Funciona con vídeos/Reels de Facebook y miles de sitios más.
* No es necesario iniciar sesión para los vídeos públicos.
* Gestión robusta de errores para las categorías de fallo más comunes
 (sitio no soportado, contenido protegido por DRM, geo-bloqueo, FFmpeg no disponible, etc.).
* Permite al usuario elegir una calidad predefinida; por defecto, la mejor disponible.
* Sanitiza los nombres de archivo para evitar el límite de 255 bytes de macOS/Linux/NTFS.
* Presenta un botón **Download** una vez que el archivo está listo para que el usuario pueda
 guardarlo localmente desde el navegador.