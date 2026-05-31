import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelo para texto
MODEL_TEXTO = "google/gemini-2.0-flash-exp:free"
# Modelo para visión (imágenes)
MODEL_VISION = "google/gemini-2.0-flash-exp:free"

@app.route("/")
def home():
    return "Servidor funcionando ✓"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    historial = data.get("historial", [])
    imagen_b64 = data.get("imagen", None)
    imagen_tipo = data.get("imagen_tipo", "image/jpeg")

    if not mensaje and not imagen_b64:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        # Construir el mensaje actual
        if imagen_b64:
            contenido = [
                {"type": "text", "text": mensaje if mensaje else "Describe esta imagen en detalle."},
                {"type": "image_url", "image_url": {"url": "data:" + imagen_tipo + ";base64," + imagen_b64}}
            ]
            model = MODEL_VISION
        else:
            contenido = mensaje
            model = MODEL_TEXTO

        # Añadir historial + mensaje actual
        messages = historial + [{"role": "user", "content": contenido}]

        headers = {
            "Authorization": "Bearer " + OPENROUTER_API_KEY,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mi-ia-app.github.io",
            "X-Title": "IA Chat iPad"
        }

        payload = {
            "model": model,
            "max_tokens": 2048,
            "messages": messages
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        respuesta = result["choices"][0]["message"]["content"]
        return jsonify({"respuesta": respuesta})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)