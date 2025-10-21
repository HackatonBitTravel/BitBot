# 🟠 BitBot – Assistant Bitcoin & BitTravel

**BitBot** est un chatbot intelligent conçu pour aider les utilisateurs à comprendre le fonctionnement de la plateforme **BitTravel** 🇸🇳 et du réseau **Bitcoin Lightning** ⚡.  
Il répond en **français**, **wolof**, ou **anglais**, et fournit des instructions claires et contextualisées pour les utilisateurs au Sénégal.

---

## 🔹 Fonctionnalités

- Répond aux questions sur **BitTravel** (achat de tickets, paiements, voyages, etc.)
- Explique le fonctionnement du **Bitcoin Lightning** et son utilisation
- Supporte **français**, **wolof**, et **anglais**
- Génère des réponses étape par étape, contextualisées pour le Sénégal
- Utilise un **vectorstore FAISS** pour la recherche documentaire
- Fonctionne via **modèle LLM Gemini** de Google

---

## 🔹 Prérequis

- Python 3.10+
- [Virtualenv](https://docs.python.org/3/library/venv.html) (recommandé)
- Clé API Gemini valide (Google Generative AI)
- (Optionnel) Token Hugging Face si vous utilisez le vectorstore stocké sur Hugging Face

---

## 🔹 Installation

1. **Cloner le dépôt :**

```bash
git clone https://github.com/HackatonBitTravel/BitBot.git
cd bitbot
```

2. **Créer et activer un environnement virtuel :**

- Windows :

```bash
python -m venv .venv
& .\.venv\Scripts\activate
```

- Linux / macOS :

```bash 
python3 -m venv .venv
source .venv/bin/activate
```

3. **Installer les dépendances depuis requirements.txt**
pip install -r requirements.txt

4. **Configurer la clé API Gemini**
Créez un fichier .env à la racine du projet et ajoute :

```ini
GOOGLE_API_KEY=TA_CLE_API_GEMINI
HF_TOKEN=TON_TOKEN_HUGGINGFACE    # pour accéder au model d'embeddings hébergé
HF_REPO_ID=bitbot/vectorstore     # optionnel, identifiant du repo où se trouvera les fichiers .faiss et .pkl 
```

BitBot utilise cette clé pour se connecter au modèle LLM Gemini.

5. **Préparer le vectorstore FAISS**
- Créez un repo sur [Hugging Face Hub](https://huggingface.co/new)
- Y déposer vos fichiers index.faiss et index.pkl
- Les charger depuis le code via URL directe

## 🔹 Lancer le BitBot
```bash
python main.py
```

## 🔹 Exemples de questions

- “C’est quoi BitTravel ?”

- “Comment acheter un ticket ?”

- “Comment payer avec Bitcoin Lightning ?”

- “Lan la Bitcoin?” (Wolof)

## 🔹 Structure du projet
```bash

bitbot/
│
├─ bot/
│   ├─ __init__.py
│   ├─ chat.py           # Gestion de la conversation
│   ├─ model_bot.py      # Chargement LLM 
│   ├─ prompt.py         # Gestion du prompt et template
│   ├─ utils.py          # Fonctions utilitaires
│   └─ vectorstore.py    # Gestion du vectorstore FAISS
│
├─ .gitignore
├─ .python-version
├─ main.py               # Point d’entrée du bot
├─ pyproject.toml        # Dépendances Python
├─ README.md
└─ requirements.txt      # Liste des packages Python

```

## 🔹 Notes

- BitBot ne fait jamais d’action directe, il guide uniquement.

- Les tickets BitTravel sont signés numériquement et non falsifiables.

- Les réponses sont toujours contextualisées pour le Sénégal.