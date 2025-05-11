# backend/app/main.py
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException # Request n'est plus nécessaire ici
from fastapi.middleware.cors import CORSMiddleware
# StaticFiles et Jinja2Templates ne sont plus nécessaires ici
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("Clé API Gemini configurée.")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de la clé API Gemini: {e}")
        GOOGLE_API_KEY = None
else:
    logger.warning("Clé API Gemini (GOOGLE_API_KEY) non trouvée.")

app = FastAPI(title="Backend Gemini Assistant API") # Donnez un titre à votre API

# Configuration CORS cruciale pour des déploiements séparés
# Soyez plus spécifique avec allow_origins en production si possible
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou l'URL de votre frontend déployé: "https://votre-frontend.fly.dev"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-text")
async def process_text(payload: dict):
    # ... (logique de l'endpoint inchangée) ...
    text = payload.get("text")
    if not text:
        logger.warning("/api/process-text - Champ 'text' manquant.")
        raise HTTPException(status_code=400, detail="Le champ 'text' est manquant.")
    logger.info(f"/api/process-text - Texte reçu : {text[:50]}...")

    if not GOOGLE_API_KEY:
        logger.warning("/api/process-text - Clé API Gemini non configurée. Réponse mock.")
        return {"response": f"Clé API Gemini non configurée. Réponse mock pour : {text}"}
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(text)
        logger.info(f"/api/process-text - Réponse de Gemini obtenue.")
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Gemini (/api/process-text) : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")


@app.post("/api/process-image")
async def process_image(prompt: str = Form(""), image: UploadFile = File(...)):
    # ... (logique de l'endpoint inchangée) ...
    logger.info(f"/api/process-image - Image reçue : {image.filename}, Prompt : {prompt[:50]}...")
    if not image.content_type.startswith("image/"):
        logger.warning(f"/api/process-image - Type de fichier invalide : {image.content_type}")
        raise HTTPException(status_code=400, detail="Type de fichier invalide. Une image est attendue.")

    image_bytes = await image.read()
    logger.info(f"/api/process-image - Image lue en bytes ({len(image_bytes)} bytes).")

    if not GOOGLE_API_KEY:
        logger.warning("/api/process-image - Clé API Gemini non configurée. Réponse mock.")
        return {"response": f"Clé API Gemini non configurée. Réponse mock pour l'image {image.filename}."}
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') 
        image_part = {"mime_type": image.content_type, "data": image_bytes}
        contents = [image_part]
        if prompt:
            contents.insert(0, prompt + " ")

        logger.info(f"/api/process-image - Envoi de la requête à Gemini Vision...")
        response = await model.generate_content_async(contents)
        logger.info(f"/api/process-image - Réponse de Gemini (vision) obtenue.")
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Gemini Vision (/api/process-image) : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur (vision): {e}")

# La partie servant le frontend React est SUPPRIMÉE.

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    logger.info(f"Démarrage du serveur Uvicorn pour l'API sur {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=(port == 8000))