from bot.prompt import chain, template, prompt
from bot.utils import detect_language
from bot.language_model import llm
from bot.embedding import retriever
from langchain_community.tools import DuckDuckGoSearchRun
import re
import time

session_history = []
salutation_done = False

# 🔍 Initialisation de l'outil de recherche web
search_tool = DuckDuckGoSearchRun()

# Instruction de formatage stricte (contraint le LLM à un bon Markdown)
INSTRUCTION_FORMAT = """
Respecte strictement les règles Markdown :
1. Liste les étapes/points en allant systématiquement à la ligne (sauts de ligne).
2. Utilise les numéros (1., 2., 3.) pour les étapes.
3. Utilise toujours les doubles astérisques (**...**) pour le gras.
"""

def is_bitcoin_related(question: str) -> bool:
    """
    Détecte si la question concerne Bitcoin/Lightning/Blockchain
    Retourne True si c'est le cas
    """
    bitcoin_keywords = [
        # Bitcoin général
        "bitcoin", "btc", "satoshi", "nakamoto",
        # Blockchain
        "blockchain", "block", "chain", "mining", "minage", "mineur",
        "hash", "proof of work", "pow", "halving",
        # Lightning Network
        "lightning", "lightning network", "ln", "lnurl", "lnpay",
        "channel", "canal", "onchain", "off-chain", "layer 2", "l2",
        # Wallets & Tech
        "wallet", "portefeuille", "lnd", "c-lightning", "eclair",
        "node", "noeud", "invoice", "facture",
        # Crypto général
        "crypto", "cryptomonnaie", "cryptocurrency", "altcoin",
        # Termes wolof
        "xaalis bu numérique", "wareef"
    ]
    
    question_lower = question.lower()
    return any(re.search(rf"\b{kw}\b", question_lower) for kw in bitcoin_keywords)


def is_bittravel_related(question: str) -> bool:
    """
    Détecte si la question concerne BitTravel
    Retourne True si c'est le cas
    """
    bittravel_keywords = [
        # BitTravel direct
        "bittravel", "bit travel", "bit-travel",
        # Transport
        "ticket", "billet", "transport", "bus", "taxi", "car rapide",
        "voyage", "déplacement", "trajet",
        # Mobile Money
        "wave", "orange money", "momo", "mobile money", "paiement mobile",
        # Sénégal spécifique
        "dakar", "sénégal", "senegal", "aftos", "dem dikk",
        # Fonctionnalités
        "réserver", "acheter", "payer", "plateforme", "application", "app",
        # Termes wolof
        "sofer", "tudd", "jënd", "ticket", "bittravel"
    ]
    
    question_lower = question.lower()
    return any(re.search(rf"\b{kw}\b", question_lower) for kw in bittravel_keywords)



def stream_response_generator(input_text, detected_lang=None, max_history=12):
    """Version streaming de la réponse"""
    global session_history

    # Détecter la langue si non précisée
    if detected_lang is None:
        detected_lang = detect_language(input_text)

    # 2. CRÉATION DE L'INSTRUCTION LINGUISTIQUE OBLIGATOIRE
    if detected_lang == 'wo':
        # Le modèle doit répondre en Wolof
        instruction_langue = "Réponds en WOLOF. Ta réponse DOIT ÊTRE intégralement en Wolof. Si l'information manque, explique la limite en Wolof."
    elif detected_lang == 'en':
        # Le modèle doit répondre en Anglais (si la détection est fiable)
        instruction_langue = "Réponds en ANGLAIS. Ta réponse DOIT ÊTRE intégralement en Anglais."
    else:
        # Français ou cas de repli
        instruction_langue = "Réponds en FRANÇAIS. Ta réponse DOIT ÊTRE intégralement en Français."


    # 🔍 LOGIQUE DE RECHERCHE (identique à get_response)
    context_docs = ""
    
    if is_bitcoin_related(input_text):
        print("🌐 [Stream] Question Bitcoin → Recherche WEB")
        try:
            web_results = search_tool.run(input_text)
            context_docs = f"[Web]\n{web_results[:3000]}"
            print("✅ Recherche web OK")
        except Exception as e:
            print(f"⚠️  Erreur web : {e}")
            context_docs = ""
    
    elif is_bittravel_related(input_text):
        print("📚 [Stream] Question BitTravel → Recherche FAISS")
        try:
            docs = retriever.invoke(input_text)
            if docs:
                context_docs = "[FAISS]\n" + "\n\n".join([
                    doc.page_content for doc in docs[:3]
                ])
                print(f"✅ {len(docs)} doc(s) trouvé(s)")
            else:
                context_docs = ""
        except Exception as e:
            print(f"⚠️  Erreur FAISS : {e}")
            context_docs = ""

    # Construire le contexte complet
    conversation_context = "\n".join(session_history[-max_history:])
    full_context = f"{conversation_context}\n\n{context_docs}" if context_docs else conversation_context

    # Formater le prompt
    prompt_text = prompt.format(
        instruction_langue=instruction_langue,
        instruction_format=INSTRUCTION_FORMAT,
        context=full_context,
        input=input_text
    )

    # Streaming
    stream = llm.stream(prompt_text)
    answer_text = ""
    
    for chunk in stream:
        content = chunk.content
        answer_text += content
        yield content

    session_history.append(f"[{detected_lang.upper()}] User: {input_text}")
    session_history.append(f"[{detected_lang.upper()}] BitBot: {answer_text}")

