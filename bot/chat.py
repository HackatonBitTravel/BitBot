from bot.prompt import chain, template, prompt
from bot.utils import detect_language
from bot.language_model import llm
from bot.embedding import retriever
from langchain_community.tools import DuckDuckGoSearchRun
import re
import asyncio

session_history = []

search_tool = DuckDuckGoSearchRun()

INSTRUCTION_FORMAT = """
Respecte strictement les règles Markdown :
1. Liste les étapes/points en allant systématiquement à la ligne (sauts de ligne).
2. Utilise les numéros (1., 2., 3.) pour les étapes.
3. Utilise toujours les doubles astérisques (**...**) pour le gras.
4. Utilise des listes à puces (-) pour les énumérations.
5. Sépare les paragraphes avec deux sauts de ligne.
"""

def is_bitcoin_related(question: str) -> bool:
    bitcoin_keywords = [
        "bitcoin", "btc", "satoshi", "nakamoto",
        "blockchain", "block", "chain", "mining", "minage", "mineur",
        "hash", "proof of work", "pow", "halving",
        "lightning", "lightning network", "ln", "lnurl", "lnpay",
        "channel", "canal", "onchain", "off-chain", "layer 2", "l2",
        "wallet", "portefeuille", "lnd", "c-lightning", "eclair",
        "node", "noeud", "invoice", "facture",
        "crypto", "cryptomonnaie", "cryptocurrency", "altcoin",
        "xaalis bu numérique", "wareef"
    ]
    question_lower = question.lower()
    return any(re.search(rf"\b{kw}\b", question_lower) for kw in bitcoin_keywords)


def is_bittravel_related(question: str) -> bool:
    bittravel_keywords = [
        "bittravel", "bit travel", "bit-travel",
        "ticket", "billet", "transport", "bus", "taxi", "car rapide",
        "voyage", "déplacement", "trajet",
        "wave", "orange money", "momo", "mobile money", "paiement mobile",
        "dakar", "sénégal", "senegal", "aftos", "dem dikk",
        "réserver", "acheter", "payer", "plateforme", "application", "app",
        "sofer", "tudd", "jënd", "ticket", "bittravel"
    ]
    question_lower = question.lower()
    return any(re.search(rf"\b{kw}\b", question_lower) for kw in bittravel_keywords)


import re

def simple_markdown_to_html_chunk(text: str) -> str:
    """
    Convertit du Markdown partiel ou mal formé en HTML propre pour streaming.
    Gère :
    - **gras**, *italique*
    - listes numérotées (1., 2., 3.)
    - listes à puces (-, *)
    - nettoie les erreurs fréquentes de formatage générées par un LLM
    """

    # --- 🔧 1. Pré-nettoyage du texte brut ---
    text = text.replace("** ", "**").replace(" **", "**")  # espaces inutiles autour du gras
    text = text.replace("* ", "*").replace(" *", "*")
    text = re.sub(r'\*\*\*+', '**', text)  # triples astérisques → doubles
    text = re.sub(r'(\*\*)([A-Za-zÀ-ÿ])', r'** \2', text)  # sépare le gras du mot collé
    text = re.sub(r'([A-Za-zÀ-ÿ])(\*\*)', r'\1 **', text)
    text = re.sub(r'\n+', '\n', text)  # réduit les doubles sauts de ligne inutiles
    text = re.sub(r'(\*\*|__)\s*\n', r'\1 ', text)  # évite les coupures de gras sur plusieurs lignes

    # --- 🔹 2. Fonctions internes ---
    def inline_md_to_html(s):
        """Convertit le Markdown inline en HTML"""
        s = re.sub(r'\*\*([^\*]+)\*\*', r'<strong style="font-weight:600;">\1</strong>', s)
        s = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', s)
        return s

    # --- 🔹 4. Inline Markdown ---
    text = inline_md_to_html(text)

    # --- 🔹 5. Nettoyage HTML final ---

    text = text.replace('\n\n', '<br><br>').replace('\n', '<br>')
    text = re.sub(r'(<br>)+</(ul|ol)>', r'</\2>', text)  # supprime les <br> mal placés

    # --- 🔹 6. Correction de quelques cas de gras/italique brisés ---
    text = text.replace('<strong style="font-weight:600;"></strong>', '')
    text = text.replace('<em></em>', '')

    return text



async def stream_response_generator_html_incremental(input_text, detected_lang=None, max_history=12):
    """
    VERSION CORRECTE : Streaming HTML incrémental
    Envoie seulement les NOUVEAUX morceaux convertis en HTML
    """
    global session_history

    if detected_lang is None:
        detected_lang = detect_language(input_text)

    if detected_lang == 'wo':
        instruction_langue = "Réponds en WOLOF. Ta réponse DOIT ÊTRE intégralement en Wolof."
    elif detected_lang == 'en':
        instruction_langue = "Réponds en ANGLAIS. Ta réponse DOIT ÊTRE intégralement en Anglais."
    else:
        instruction_langue = "Réponds en FRANÇAIS. Ta réponse DOIT ÊTRE intégralement en Français."

    # Recherche
    context_docs = ""
    
    if is_bitcoin_related(input_text):
        print("🌐 [Stream] Question Bitcoin → Recherche WEB")
        try:
            loop = asyncio.get_event_loop()
            web_results = await loop.run_in_executor(None, search_tool.run, input_text)
            context_docs = f"[Web]\n{web_results[:3000]}"
            print("✅ Recherche web OK")
        except Exception as e:
            print(f"⚠️  Erreur web : {e}")
            context_docs = ""
    
    elif is_bittravel_related(input_text):
        print("📚 [Stream] Question BitTravel → Recherche FAISS")
        try:
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, retriever.invoke, input_text)
            if docs:
                context_docs = "[FAISS]\n" + "\n\n".join([
                    doc.page_content for doc in docs[:3]
                ])
                print(f"✅ {len(docs)} doc(s) trouvé(s)")
        except Exception as e:
            print(f"⚠️  Erreur FAISS : {e}")
            context_docs = ""

    conversation_context = "\n".join(session_history[-max_history:])
    full_context = f"{conversation_context}\n\n{context_docs}" if context_docs else conversation_context

    prompt_text = prompt.format(
        instruction_langue=instruction_langue,
        instruction_format=INSTRUCTION_FORMAT,
        context=full_context,
        input=input_text
    )

    # 🔥 STRATÉGIE : Garder le Markdown original ET envoyer du HTML
    markdown_buffer = ""  # Pour l'historique
    
    try:
        stream = llm.stream(prompt_text)
        
        for chunk in stream:
            content = chunk.content
            if content:
                # Sauvegarder le Markdown original
                markdown_buffer += content
                
                # 🔥 Convertir SEULEMENT le nouveau chunk en HTML
                html_chunk = simple_markdown_to_html_chunk(content)
                
                # Envoyer seulement le nouveau morceau HTML
                yield html_chunk
                
                await asyncio.sleep(0.01)
        
        # Sauvegarder en Markdown dans l'historique
        session_history.append(f"[{detected_lang.upper()}] User: {input_text}")
        session_history.append(f"[{detected_lang.upper()}] BitBot: {markdown_buffer}")
        
    except Exception as e:
        print(f"❌ Erreur lors du streaming : {e}")
        yield f'<span style="color: red;">Erreur: {str(e)}</span>'


# Version Markdown plain (pour compatibilité)
async def stream_response_generator_plain(input_text, detected_lang=None, max_history=12):
    """
    Version streaming Markdown brut
    """
    global session_history

    if detected_lang is None:
        detected_lang = detect_language(input_text)

    if detected_lang == 'wo':
        instruction_langue = "Réponds en WOLOF. Ta réponse DOIT ÊTRE intégralement en Wolof."
    elif detected_lang == 'en':
        instruction_langue = "Réponds en ANGLAIS. Ta réponse DOIT ÊTRE intégralement en Anglais."
    else:
        instruction_langue = "Réponds en FRANÇAIS. Ta réponse DOIT ÊTRE intégralement en Français."

    context_docs = ""
    
    if is_bitcoin_related(input_text):
        try:
            loop = asyncio.get_event_loop()
            web_results = await loop.run_in_executor(None, search_tool.run, input_text)
            context_docs = f"[Web]\n{web_results[:3000]}"
        except Exception as e:
            print(f"⚠️  Erreur web : {e}")
    
    elif is_bittravel_related(input_text):
        try:
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, retriever.invoke, input_text)
            if docs:
                context_docs = "[FAISS]\n" + "\n\n".join([
                    doc.page_content for doc in docs[:3]
                ])
        except Exception as e:
            print(f"⚠️  Erreur FAISS : {e}")

    conversation_context = "\n".join(session_history[-max_history:])
    full_context = f"{conversation_context}\n\n{context_docs}" if context_docs else conversation_context

    prompt_text = prompt.format(
        instruction_langue=instruction_langue,
        instruction_format=INSTRUCTION_FORMAT,
        context=full_context,
        input=input_text
    )

    answer_text = ""
    
    try:
        stream = llm.stream(prompt_text)
        
        for chunk in stream:
            content = chunk.content
            if content:
                answer_text += content
                yield content
                await asyncio.sleep(0.01)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        yield f"\n\nErreur: {str(e)}"

    session_history.append(f"[{detected_lang.upper()}] User: {input_text}")
    session_history.append(f"[{detected_lang.upper()}] BitBot: {answer_text}")