from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bot.chat import stream_response_generator, stream_response_generator_plain

app = FastAPI(
    title="BitBot API",
    description=(
        "API de l'assistant conversationnel **BitBot** pour la plateforme **BitTravel**. "
        "Cette API prend en charge les langues **française**, **wolof** et **anglaise**, "
        "et permet d'interagir en temps réel avec un modèle d'IA (LLM) via le streaming."
    ),
    version="1.0.0"
)

# ------------------------------------------------------------
# CORS CONFIGURATION
# ------------------------------------------------------------
# Autorise les requêtes cross-origin (nécessaire pour le frontend web ou mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ À restreindre en production (ex: ["https://bittravel.sn"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# DATA MODELS
# ------------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Représente le format de la requête envoyée au chatbot.

    Attributes:
        message (str): Le message ou la question saisie par l'utilisateur.
    """
    message: str


# ------------------------------------------------------------
# HOME ROUTE
# ------------------------------------------------------------
@app.get("/", tags=["Root"])
def home():
    """
    **Page d’accueil de l’API BitBot**

    Retourne un simple message de bienvenue indiquant que l’API fonctionne correctement.

    **Retourne :**
    ```json
    {
        "message": "Bienvenue sur l'API BitBot ⚡ (mode streaming activé)"
    }
    ```
    """
    return {"message": "Bienvenue sur l'API BitBot ⚡ (mode streaming activé)"}


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------
@app.api_route("/ping", methods=["GET", "HEAD"], tags=["Monitoring"])
async def ping():
    """
    **Vérifie l’état du serveur BitBot**

    Cette route est utilisée pour vérifier que l’API est **en ligne et réactive**.
    Utile pour les outils de monitoring (UptimeRobot, Render, etc.).

    **Retourne :**
    ```json
    {
        "status": "BitBot actif !"
    }
    ```
    """
    return {"status": "BitBot actif !"}


# ------------------------------------------------------------
# CHAT STREAM (SSE)
# ------------------------------------------------------------
@app.post("/chat", tags=["Chat"])
async def chat_stream(req: ChatRequest):
    """
    **Discussion avec BitBot (format SSE)**

    Cette route établit une **connexion en streaming** avec le modèle d'IA, 
    en utilisant le format **Server-Sent Events (SSE)**.

    Le serveur envoie la réponse **progressivement**, 
    permettant une expérience de chat fluide et en temps réel.

    **Entrée :**
    ```json
    {
        "message": "C’est quoi BitTravel ?"
    }
    ```

    **Sortie (flux SSE) :**
    ```
    data: BitTravel est une plateforme de réservation de tickets...
    data: Elle prend en charge les paiements...
    data: ...
    ```

    **Spécificités techniques :**
    - Type : `POST`
    - Format : `text/event-stream`
    - Temps de connexion : 5 minutes max
    - Support : Langues FR / WO / EN

    """
    try:
        return StreamingResponse(
            stream_response_generator(req.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Désactive le buffering (utile sur Render/Nginx)
                "Transfer-Encoding": "chunked"
            }
        )
    except Exception as e:
        print(f"Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}


# ------------------------------------------------------------
# CHAT STREAM (TEXTE BRUT)
# ------------------------------------------------------------
@app.post("/chat/plain", tags=["Chat"])
async def chat_stream_plain(req: ChatRequest):
    """
    **Discussion avec BitBot (texte brut)**

    Variante simplifiée de `/chat` qui renvoie la réponse 
    du modèle en **texte brut (plain text)** au lieu du format SSE.

    Idéale pour les tests avec **cURL**, **Postman** ou des scripts simples.

    **Exemple :**
    ```bash
    curl -X POST http://localhost:8000/chat/plain \
         -H "Content-Type: application/json" \
         -d '{"message": "Qui a créé Bitcoin ?"}'
    ```

    **Sortie :**
    ```
    Bitcoin a été créé en 2009 par une personne (ou un groupe) sous le pseudonyme Satoshi Nakamoto.
    ```

    **Spécificités techniques :**
    - Type : `POST`
    - Format : `text/plain; charset=utf-8`
    - Support : Langues FR / WO / EN
    - Recommandé pour les intégrations simples ou les tests manuels
    """
    try:
        return StreamingResponse(
            stream_response_generator_plain(req.message),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f"Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}


# ------------------------------------------------------------
# RUN SERVER (développement local)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,  # Timeout de 5 min pour le streaming
        log_level="info"
    )
