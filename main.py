from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bot.chat import stream_response_generator_plain, stream_response_generator_html_incremental

# ------------------------------------------------------------
# CONFIGURATION GLOBALE DE L'API
# ------------------------------------------------------------
app = FastAPI(
    title="BitBot API",
    description=(
        "API du chatbot **BitBot**, assistant intelligent intégré à la plateforme **BitTravel**. "
        "Elle permet d’interagir avec un modèle d’IA multilingue (Français, Wolof, Anglais) "
        "en mode **streaming** pour une expérience de chat fluide et interactive."
    ),
    version="1.0.0"
)

# ------------------------------------------------------------
# CONFIGURATION CORS
# ------------------------------------------------------------
# Permet les requêtes depuis d’autres origines (notamment le frontend web/mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  À restreindre en production (ex: ["https://bittravel.sn"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# SCHEMAS DE DONNÉES
# ------------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Schéma du message utilisateur envoyé au chatbot.

    Attributes:
        message (str): Le texte saisi par l'utilisateur (question ou instruction).
    """
    message: str


# ------------------------------------------------------------
#ROUTE D'ACCUEIL
# ------------------------------------------------------------
@app.get("/", tags=["Root"])
def home():
    """
   **Page d’accueil de l’API BitBot**

    Retourne un message simple confirmant que l’API est en ligne et prête à l’emploi.

    **Exemple de réponse :**
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

    Cette route sert à vérifier que le serveur est **actif**.
    Utilisée pour les systèmes de surveillance comme **UptimeRobot** ou **Render Health Checks**.

    **Exemple de réponse :**
    ```json
    {
        "status": "BitBot actif !"
    }
    ```
    """
    return {"status": "BitBot actif !"}


# ------------------------------------------------------------
# CHAT STREAM (HTML)
# ------------------------------------------------------------
@app.post("/chat", tags=["Chat"])
async def chat_stream(req: ChatRequest):
    """
    **Discussion avec BitBot — Streaming HTML**

    Cet endpoint renvoie la réponse du chatbot **en continu** sous forme **HTML**.
    Le rendu Markdown est directement converti côté **backend**.

    **Utilisation recommandée :**
    - Lorsque le frontend affiche déjà du contenu HTML (ex : `<div v-html="...">` en Vue.js)
    - Permet une **mise en forme riche** directement côté serveur.

    **Entrée :**
    ```json
    {
        "message": "C’est quoi BitTravel ?"
    }
    ```

    **Sortie (texte HTML progressif) :**
    ```html
    <p><strong>BitTravel</strong> est une plateforme innovante...</p>
    ```

    **Détails techniques :**
    - Méthode : `POST`
    - Type : `text/html; charset=utf-8`
    - Streaming temps réel (connexion persistante)
    - Timeout : 5 minutes

    """
    try:
        return StreamingResponse(
            stream_response_generator_html_incremental(req.message),
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f" Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}


# ------------------------------------------------------------
#  CHAT STREAM (MARKDOWN)
# ------------------------------------------------------------
@app.post("/chat/markdown", tags=["Chat"])
async def chat_stream_markdown(req: ChatRequest):
    """
     **Discussion avec BitBot — Streaming Markdown**

    Cet endpoint renvoie la réponse du chatbot **en texte brut Markdown**,
    sans conversion côté serveur.  
    Le frontend (par ex. Vue.js, React, Flutter) peut ensuite gérer le rendu
    avec une librairie comme **marked.parse()** ou **react-markdown**.

    **Utilisation recommandée :**
    - Pour les applications frontends modernes qui gèrent déjà le Markdown.
    - Permet un **contrôle complet du rendu visuel côté client.**

    **Entrée :**
    ```json
    {
        "message": "Comment payer un billet avec Bitcoin ?"
    }
    ```

    **Sortie (Markdown brut) :**
    ```
    **BitTravel** accepte les paiements en **Bitcoin** via le **Lightning Network** ⚡.
    ```

    **Détails techniques :**
    - Méthode : `POST`
    - Type : `text/plain; charset=utf-8`
    - Streaming temps réel
    - Timeout : 5 minutes
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
#LANCEMENT DU SERVEUR (développement local)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,  # Timeout de 5 minutes pour le streaming
        log_level="info"
    )
