#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
import os

load_dotenv()

# Variables d'environnement
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_REPO_ID = os.getenv("HF_REPO_ID")

# Vérifications
if not HUGGINGFACEHUB_API_TOKEN:
    raise ValueError(" Token Hugging Face manquant dans .env")
if not HF_REPO_ID:
    raise ValueError(" HF_REPO_ID manquant dans .env")

print(f"📥 Téléchargement du vectorstore depuis : {HF_REPO_ID}")

# Téléchargement des fichiers FAISS depuis Hugging Face
try:
    faiss_index_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename="index.faiss",
        token=HUGGINGFACEHUB_API_TOKEN
    )

    pkl_index_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename="index.pkl",
        token=HUGGINGFACEHUB_API_TOKEN
    )
    
    print("Fichiers FAISS téléchargés")
except Exception as e:
    print(f"Erreur téléchargement : {e}")
    raise

folder_path = faiss_index_path.replace("index.faiss", "")
print(f"Dossier : {folder_path}")

# ✅ EMBEDDINGS LOCAUX (gratuit, illimité, rapide)
# Le modèle se télécharge une seule fois (~80 MB) et tourne sur ton PC
try:
    # Utilisez le modèle 'text-embedding-004' qui est performant pour le RAG
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        # Votre clé API est lue automatiquement via le SDK
    )
    print("Embeddings Google chargés (légers, API)")
except Exception as e:
    print(f"Erreur initialisation embeddings Google : {e}")
    raise

# Chargement du vectorstore FAISS
try:
    vectorstore = FAISS.load_local(
        folder_path=folder_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"✅ Vectorstore chargé ({vectorstore.index.ntotal} documents)")
except Exception as e:
    print(f"Erreur chargement vectorstore : {e}")
    print("Vérifie que le vectorstore a été créé avec le même modèle d'embeddings")
    raise

# Création du retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

print("✅ Retriever prêt (aucune limite de requêtes !)")