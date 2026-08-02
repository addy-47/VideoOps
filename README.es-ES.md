

# 🎬 VideoOps

**VideoOps** es una pipeline avanzada y completamente automatizada para la generación y orquestación de videos con IA. Genera guiones, recopila activos multimedia coincidentes (imágenes/videos), sintetiza locuciones de texto a voz (TTS), aplica transiciones profesionales y animaciones de texto dinámicas palabra por palabra, y renderiza YouTube Shorts completamente producidos y listos para su publicación.

---

## ✨ Características

- **Selección dinámica de contenido**: Elige formatos óptimos alternando entre creadores **basados en imágenes** (`YTShortsCreator_I`, días pares) y creadores **basados en video** (`YTShortsCreator_V`, días impares).
- **Generación automatizada de contenido**: Utiliza Google Gemini (`gemini-2.5-flash-lite` a través del SDK `google-genai`) para escribir guiones atractivos para formato corto, consultas de búsqueda optimizadas y prompts de imagen personalizados.
- **Cadenas de respaldo robustas**:
  - **Texto a voz (TTS)**: Google Cloud TTS ➔ Azure TTS ↔ gTTS.
  - **Obtención de activos**: Generación de imágenes con IA (Hugging Face Stable Diffusion) ➔ API de Unsplash ➔ APIs de Pexels / Pixabay.
  - **Renderizado paralelo**: Composición de clips multi-proceso/paralela ➔ Renderizado secuencial ➔ Copia plana de emergencia si se superan los umbrales de recursos del sistema.
- **Efectos de video premium**:
  - Diseños de texto dinámico palabra por palabra con desplazamiento automático.
  - Transiciones de disolución (crossfades) personalizadas y atenuaciones de audio suaves.
  - Filtros de desenfoque de bordes y fondo combinados para un aspecto pulido.
- **Flujo de trabajo totalmente automatizado**: Creación automática de miniaturas, limpieza local de archivos y publicación opcional en YouTube mediante integración OAuth.

---

## 📂 Estructura del Proyecto

```
VideoOps/
├── automation/               # Módulos principales de automatización
│   ├── shorts_maker_I.py    # Creador de shorts basado en imágenes (días pares)
│   ├── shorts_maker_V.py    # Creador de shorts basado en video (días impares)
│   ├── parallel_renderer.py # Renderizado de video multi-proceso paralelo
│   ├── parallel_tasks.py    # Gestión concurrente de tareas de renderizado
│   ├── thumbnail.py         # Generación automatizada de miniaturas de YouTube
│   ├── voiceover.py         # Orquestación de TTS e implementación de Google Cloud
│   ├── voiceover_azure.py   # Respaldo de implementación de Azure TTS
│   ├── youtube_auth.py      # Lógica de autenticación OAuth2 para la API de YouTube
│   ├── youtube_upload.py    # Integración de carga con la API de YouTube Data
│   └── content_generator.py # Generación de guiones y prompts con Gemini
├── helper/                  # Utilidades auxiliares modulares
│   ├── image.py            # Transformación de imágenes (zoom, recorte, marcas de agua)
│   ├── fetch.py            # Descargas de medios basadas en API (Pexels, Pixabay, HF, Unsplash)
│   ├── crossfade.py        # Transiciones personalizadas y atenuaciones de múltiples clips
│   ├── text.py             # Animación compleja de clips de texto palabra por palabra
│   ├── audio.py            # Procesamiento, mezcla y sincronización de audio
│   ├── memory.py           # Controles de uso de memoria del sistema y CPU
│   ├── process.py          # Monitoreo de recursos a nivel de proceso
│   ├── minor_helper.py     # Limpieza, verificación de carpetas y análisis de archivos
│   └── blur.py             # Utilidades visuales avanzadas de desenfoque gaussiano/de bordes
├── packages/                # Activos compartidos del paquete
│   └── fonts/
│       └── default_font.ttf # Tipografía consolidada del proyecto
├── main.py                 # Punto de entrada principal de orquestación
├── requirements.txt         # Dependencias de Python personalizadas
├── run.sh                  # Ejecutor cron de automatización con commits automáticos de git
└── _verify_keys.py         # Diagnóstico de claves de entorno
```

---

## 🚀 Configuración e Instalación

### 1. Prerrequisitos
Asegúrate de tener instaladas las siguientes dependencias del sistema:
- **Python 3.10+**
- **FFmpeg**: Requerido para el procesamiento de video con MoviePy (`sudo apt install ffmpeg`)
- **ImageMagick**: Requerido para efectos de texto y renderizado de texto con MoviePy (`sudo apt install imagemagick`)

### 2. Configuración del Entorno
Clona el repositorio y prepara tu entorno virtual:
```sh
git clone https://github.com/yourusername/videoops.git
cd videoops

# Crea y activa el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instala dependencias reducidas y rápidas
pip install -r requirements.txt
```

### 3. Configuración de Credenciales de API
Crea un archivo `.env` en el directorio raíz. Pega y configura las siguientes variables:

```env
# Google Cloud Platform
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/lazycreator-1.json

# Configuración de LLM
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# Medios de Stock y Claves de API
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
NEWS_API_KEY=your_news_api_key
HF_API_TOKEN=your_huggingface_token

# Claves de Voz de Respaldo (Opcional, cae en gTTS)
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_speech_region

# Configuración de la Pipeline de Video
ENABLE_YOUTUBE_UPLOAD=false
YOUTUBE_TOPIC="Artificial Intelligence"
DEBUG_MODE=false
```

---

## 🎮 Guía de Uso

| Comando de Ejecución | Acción |
| :--- | :--- |
| `python main.py` | Ejecuta la pipeline. Selecciona automáticamente el creador de imágenes o video según la paridad del día del año. |
| `python main.py video` | Fuerza la ejecución de la pipeline basada en video (`YTShortsCreator_V`) sin importar el día. |
| `python main.py image` | Fuerza la ejecución de la pipeline basada en imágenes (`YTShortsCreator_I`) sin importar el día. |
| `./run.sh` | Orquesta una ejecución cron (realiza commits automáticos de los archivos del espacio de trabajo y ejecuta la pipeline). |
| `DEBUG_MODE=true python main.py` | Ejecuta con registro detallado completo (nivel `DEBUG`) activado. |
| `python _verify_keys.py` | Script de diagnóstico para comprobar y verificar tus claves de API e integraciones de servicios. |

---

## 📄 Licencia
Este proyecto está licenciado bajo la Licencia MIT.
