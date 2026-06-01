import os
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_OMNI = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

@app.route("/")
def home():
    return "Servidor funcionando ✓"

def extraer_texto_pdf(b64):
    try:
        import pypdf
        datos = base64.b64decode(b64)
        lector = pypdf.PdfReader(io.BytesIO(datos))
        texto = ""
        for pagina in lector.pages:
            texto += pagina.extract_text() + "\n"
        return texto.strip()
    except Exception as e:
        return None

def extraer_texto_docx(b64):
    try:
        import docx
        datos = base64.b64decode(b64)
        doc = docx.Document(io.BytesIO(datos))
        texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return texto.strip()
    except Exception as e:
        return None

def extraer_texto_txt(b64):
    try:
        datos = base64.b64decode(b64)
        return datos.decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return None

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    historial = data.get("historial", [])
    modelo = data.get("modelo", "openai/gpt-oss-120b:free")
    archivo_b64 = data.get("archivo", None)
    archivo_tipo = data.get("archivo_tipo", "")
    archivo_nombre = data.get("archivo_nombre", "archivo")

    if not mensaje and not archivo_b64:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        modelo_usar = modelo
        contenido = []

        if archivo_b64:
            modelo_usar = MODEL_OMNI
            texto_msg = mensaje if mensaje else ""

            if archivo_tipo.startswith("image/"):
                if texto_msg:
                    contenido.append({"type": "text", "text": texto_msg})
                else:
                    contenido.append({"type": "text", "text": "Describe esta imagen en detalle."})
                contenido.append({
                    "type": "image_url",
                    "image_url": {"url": "data:" + archivo_tipo + ";base64," + archivo_b64}
                })

            elif archivo_tipo.startswith("audio/"):
                fmt = archivo_tipo.replace("audio/", "")
                if texto_msg:
                    contenido.append({"type": "text", "text": texto_msg})
                else:
                    contenido.append({"type": "text", "text": "Transcribe y analiza este audio."})
                contenido.append({
                    "type": "input_audio",
                    "input_audio": {"data": archivo_b64, "format": fmt}
                })

            elif archivo_tipo == "application/pdf":
                texto_extraido = extraer_texto_pdf(archivo_b64)
                if texto_extraido:
                    intro = texto_msg if texto_msg else "Analiza el siguiente documento:"
                    contenido.append({"type": "text", "text": intro + "\n\nArchivo: " + archivo_nombre + "\n\n" + texto_extraido})
                else:
                    contenido.append({"type": "text", "text": "No se pudo extraer el texto del PDF."})

            elif archivo_tipo in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"):
                texto_extraido = extraer_texto_docx(archivo_b64)
                if texto_extraido:
                    intro = texto_msg if texto_msg else "Analiza el siguiente documento:"
                    contenido.append({"type": "text", "text": intro + "\n\nArchivo: " + archivo_nombre + "\n\n" + texto_extraido})
                else:
                    contenido.append({"type": "text", "text": "No se pudo extraer el texto del documento Word."})

            elif archivo_tipo in ("text/plain", "text/markdown", "text/csv"):
                texto_extraido = extraer_texto_txt(archivo_b64)
                if texto_extraido:
                    intro = texto_msg if texto_msg else "Analiza el siguiente archivo:"
                    contenido.append({"type": "text", "text": intro + "\n\nArchivo: " + archivo_nombre + "\n\n" + texto_extraido})
                else:
                    contenido.append({"type": "text", "text": "No se pudo leer el archivo de texto."})

            else:
                contenido.append({"type": "text", "text": "Archivo adjunto: " + archivo_nombre + " (" + archivo_tipo + "). " + (texto_msg or "")})

        else:
            contenido = mensaje

        messages = historial + [{"role": "user", "content": contenido}]

        headers = {
            "Authorization": "Bearer " + OPENROUTER_API_KEY,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ochoenes.github.io",
            "X-Title": "ochoenes"
        }

        payload = {
            "model": modelo_usar,
            "max_tokens": 2048,
            "messages": messages
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=55)
        response.raise_for_status()
        result = response.json()
        respuesta = result["choices"][0]["message"]["content"]
        return jsonify({"respuesta": respuesta})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
