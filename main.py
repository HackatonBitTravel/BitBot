from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bot.chat import stream_response_generator, stream_response_generator_plain

app = FastAPI(
    title="BitBot API",
    description="API pour BitTravel Assistant (FR / WO / EN)",
    version="1.0.0"
)

# Configuration CORS (important pour les requêtes depuis le frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API BitBot ⚡ (mode streaming activé)"}


@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    return {"status": "BitBot actif !"}


@app.post("/chat")
async def chat_stream(req: ChatRequest):
    """
    Endpoint principal avec format SSE (Server-Sent Events).
    """
    try:
        return StreamingResponse(
            stream_response_generator(req.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Désactive le buffering nginx
                "Transfer-Encoding": "chunked"
            }
        )
    except Exception as e:
        print(f"❌ Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}


@app.post("/chat/plain")
async def chat_stream_plain(req: ChatRequest):
    """
    Endpoint alternatif sans format SSE (texte brut).
    Plus simple à tester avec curl ou des clients basiques.
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
        print(f"❌ Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,  # Timeout de 5 minutes pour le streaming
        log_level="info"
    )