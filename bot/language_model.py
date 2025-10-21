import os
from langchain_google_genai import ChatGoogleGenerativeAI
# Gestion des variables d'environnement
from dotenv import load_dotenv
import google.generativeai as genai
# Charger la clé API depuis .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(" Clé API Gemini manquante ! Vérifie ton fichier .env.")

# Configurer le client Gemini
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash-exp",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3
)
