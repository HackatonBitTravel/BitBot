from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bot.chat import stream_response_generator

app = FastAPI(
    title="BitBot API",
    description="API pour BitTravel Assistant (FR / WO / EN)",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Bienvenue sur l’API BitBot ⚡ (mode streaming activé)"}

@app.get("/ping")
async def ping():
    return {"status": "BitBot actif !"}

@app.post("/chat")
async def chat_stream(req: ChatRequest):
    """
    Endpoint principal qui utilise StreamingResponse pour envoyer la réponse 
    du LLM en temps réel.
    """
    try:
        return StreamingResponse(
            stream_response_generator(req.message),
            media_type="text/event-stream" 
        )
    except Exception as e:
        print(f"Erreur lors de la préparation du stream: {e}")
        return {"error": f"Une erreur interne s'est produite : {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
