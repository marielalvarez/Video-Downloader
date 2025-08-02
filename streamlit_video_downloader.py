# streamlit_video_downloader.py
"""
Streamlit web-app que permite al usuario pegar prácticamente cualquier URL de vídeo soportada por **yt-dlp**
y descargarla como un único archivo MP4.
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


"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Literal, Tuple

import streamlit as st
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


###############################################################################
# Small helpers
###############################################################################

QUALITY_SPEC = {
    "Best available": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
    "1080p HD": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
}


def classify_download_error(err_msg: str) -> Tuple[str, str]:
    """Map yt‑dlp/OS error messages to short user‑friendly explanations."""
    lower = err_msg.lower()

    if "unsupported url" in lower or "no extractor" in lower:
        return (
            "Sitio no soportado",
            "El sitio web no está en la lista de extractores de yt‑dlp. \
            Prueba con otra URL o revisa soporte con `yt-dlp --list-extractors`.",
        )
    if "drm" in lower or "encrypted" in lower:
        return (
            "Contenido protegido por DRM",
            "No es posible descargar/descifrar videos con DRM (Netflix, Disney+, etc.).",
        )
    if "this video is unavailable" in lower and "country" in lower:
        return (
            "Geo‑bloqueo",
            "El video está restringido en tu región. Usa una VPN situada en el país permitido.",
        )
    if "login" in lower or "cookies" in lower or "private" in lower:
        return (
            "Requiere iniciar sesión",
            "Debes pasar tus cookies del navegador (`--cookies-from-browser`) para contenido privado o con edad restringida.",
        )
    if "ffmpeg" in lower and "not found" in lower:
        return (
            "FFmpeg no encontrado",
            "Instala FFmpeg y asegúrate de que esté disponible en tu PATH del sistema.",
        )
    if "file name too long" in lower:
        return (
            "Nombre de archivo demasiado largo",
            "El título del video excede el límite del sistema de archivos. Se recomienda usar un nombre de archivo corto.",
        )
    # Generic fallback
    return ("Error desconocido", err_msg)


###############################################################################
# Streamlit UI
###############################################################################

st.set_page_config(page_title="Video Downloader", page_icon="🔍")
st.title("📥 Descarga videos de redes sociales.")
st.markdown(
    """
    1. **Primero**, pega la liga del video deseado.  
    2. **Después**, se descargará automáticamente.  
    3. **Finalmente**, guárdalo en tu computadora.
    """
)


with st.expander("→ Aviso de uso legal", expanded=False):
    st.markdown(
        "*Descarga únicamente contenido sobre el cual tengas **derechos legales** o permiso explícito.*\n"
        "El uso indebido de la herramienta puede violar derechos de autor, términos de servicio y/o leyes locales."
    )

url = st.text_input("Pega la URL del video o Reel", placeholder="https://www.facebook.com/…")
quality_choice: Literal["Best available", "1080p HD", "720p", "480p"] = st.selectbox(
    "Calidad deseada", list(QUALITY_SPEC.keys()), index=0
)

tmp_dir = Path(tempfile.gettempdir()) / "streamlit_video_dl"
tmp_dir.mkdir(exist_ok=True)

if st.button("Descargar video", disabled=not url):
    if not url:
        st.warning("⚠️ Copia primero una URL válida.")
        st.stop()

    outtmpl = os.path.join(tmp_dir.as_posix(), "% (id)s.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "format": QUALITY_SPEC[quality_choice],
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "noprogress": True,  # Streamlit stdout is messy; we show our own messages
        "restrictfilenames": True,  # avoid spaces/Unicode edge cases
        # Retrys for unstable networks
        "retries": 5,
        "fragment_retries": 10,
        # Limit filename length further if needed
        "trim_file_name": 120,
    }

    with st.spinner("⬇️ Descargando… puede tardar unos minutos según la calidad y tu conexión"):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = Path(ydl.prepare_filename(info))

            if not file_path.exists() or file_path.stat().st_size == 0:
                st.error("No se generó ningún archivo. Verifica la URL y vuelve a intentar.")
                st.stop()

            st.success(f"✅ Descarga completada: **{info.get('title', 'Video')}**")
            with open(file_path, "rb") as f:
                st.download_button(
                    label="💾 Guardar MP4",
                    data=f.read(),
                    file_name=file_path.name,
                    mime="video/mp4",
                )

        except DownloadError as e:
            title, explanation = classify_download_error(str(e))
            st.error(f"**{title}**\n\n{explanation}")
            st.exception(e)
        except Exception as e:  
            st.error("Ocurrió un error inesperado durante la descarga.")
            st.exception(e)
