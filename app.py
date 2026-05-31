import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)

@app.route("/")
def home():
    return "Servidor funcionando ✓"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    imagen_b64 = data.get("imagen", None)
    imagen_tipo = data.get("imagen_tipo", "image/jpeg")

    if not mensaje and not imagen_b64:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        if imagen_b64:
            contenido = [
                {"type": "text", "text": mensaje if mensaje else "Describe esta imagen en detalle."},
                {"type": "image_url", "image_url": {"url": "data:" + imagen_tipo + ";base64," + imagen_b64}}
            ]
            messages = [{"role": "user", "content": contenido}]
            model = "llama-4-scout-17b-16e-instruct"
        else:
            messages = [{"role": "user", "content": mensaje}]
            model = "llama-3.3-70b-versatile"

        response = client.chat.completions.create(
            model=model,
            max_tokens=1024,
            messages=messages
        )
        return jsonify({"respuesta": response.choices[0].message.content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
