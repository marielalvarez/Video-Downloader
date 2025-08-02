# streamlit_video_downloader.py
"""
Streamlit web‑app que permite al usuario pegar casi cualquier URL compatible con **yt‑dlp** y
bajarla como MP4. Corregido:
* Plantilla `outtmpl` sin espacio malicioso → evita que todos los videos usen el mismo nombre.
* Botón de descarga con `key` dinámico → Streamlit no cachea los bytes del primer video.
* Limpieza opcional del archivo tras la descarga para no llenar el disco.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Literal, Tuple

import streamlit as st
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

###############################################################################
# Helpers
###############################################################################
QUALITY_SPEC = {
    "Best available": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
    "1080p HD": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
}

def classify_download_error(err_msg: str) -> Tuple[str, str]:
    lower = err_msg.lower()
    if "unsupported url" in lower or "no extractor" in lower:
        return (
            "Sitio no soportado",
            "El sitio no está en la lista de extractores de yt‑dlp.",
        )
    if "drm" in lower or "encrypted" in lower:
        return ("Contenido protegido por DRM", "yt‑dlp no puede descargar medios con DRM.")
    if "country" in lower and "unavailable" in lower:
        return ("Geo‑bloqueo", "El video está restringido en tu región, usa VPN.")
    if any(w in lower for w in ("login", "cookies", "private")):
        return ("Requiere iniciar sesión", "Pasa tus cookies con --cookies-from-browser.")
    if "ffmpeg" in lower and "not found" in lower:
        return ("FFmpeg no encontrado", "Instala FFmpeg o añádelo a PATH.")
    if "file name too long" in lower:
        return ("Nombre de archivo muy largo", "Usa --trim-filenames o un template corto.")
    return ("Error desconocido", err_msg)

###############################################################################
# UI
###############################################################################
st.set_page_config(page_title="Video Downloader", page_icon="📥")
st.title("📥 Descarga videos de redes sociales")

with st.expander("Aviso legal"):
    st.markdown(
        "Descarga solo contenido sobre el que tengas **derechos** o permiso explícito. El mal uso puede violar leyes y TOS."
    )

url = st.text_input("Pega la URL del video", placeholder="https://…")
quality: Literal["Best available", "1080p HD", "720p", "480p"] = st.selectbox(
    "Calidad", list(QUALITY_SPEC.keys()), index=0
)

TMP_DIR = Path(tempfile.gettempdir()) / "streamlit_video_dl"
TMP_DIR.mkdir(exist_ok=True)

if st.button("Descargar", disabled=not url):
    if not url:
        st.warning("⚠️ Ingresa una URL válida.")
        st.stop()

    outtmpl = TMP_DIR / "%(id)s.%(ext)s"

    ydl_opts = {
        "format": QUALITY_SPEC[quality],
        "merge_output_format": "mp4",
        "outtmpl": str(outtmpl),
        "restrictfilenames": True,
        "trim_file_name": 120,
        "quiet": True,
    }

    with st.spinner("⬇️ Descargando…"):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = Path(ydl.prepare_filename(info))

            if not file_path.exists():
                st.error("Descarga fallida: archivo no creado.")
                st.stop()

            st.success(f"✅ {info.get('title') or 'Video'} listo")
            with open(file_path, "rb") as f:
                st.download_button(
                    "💾 Guardar MP4",
                    data=f.read(),
                    mime="video/mp4",
                    file_name=file_path.name,
                    key=f"download_{info['id']}",  
                )

            total_size = sum(p.stat().st_size for p in TMP_DIR.glob("*"))
            if total_size > 300 * 1024 * 1024:  
                shutil.rmtree(TMP_DIR)
                TMP_DIR.mkdir()

        except DownloadError as e:
            title, msg = classify_download_error(str(e))
            st.error(f"**{title}**\n{msg}")
        except Exception as e:
            st.error("Error inesperado.")
            st.exception(e)
