"""
Pagani Zonda R – RAG Pipeline with Gemini 1.5 Pro
Handles context construction, prompt engineering, and LLM generation.
"""

import os
import time
import json
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("pagani.rag_pipeline")

# ── Gemini Configuration ──
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GENERATION_MODEL = "gemini-2.5-flash"

# ── Safety Settings ── Block nothing for enterprise use
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# ── Session Memory Store ──
# Map of username to a list of dicts: {"role": "user"|"model", "content": str}
chat_sessions: dict[str, list[dict]] = {}
MAX_SESSION_TURNS = 5  # Keep last 5 Q&A pairs (10 messages total)

def _get_history(username: str) -> list[dict]:
    return chat_sessions.get(username, [])
    
def _add_to_history(username: str, question: str, answer: str):
    if username not in chat_sessions:
        chat_sessions[username] = []
    
    chat_sessions[username].append({"role": "user", "content": question})
    chat_sessions[username].append({"role": "model", "content": answer})
    
    # Truncate
    if len(chat_sessions[username]) > MAX_SESSION_TURNS * 2:
        chat_sessions[username] = chat_sessions[username][-MAX_SESSION_TURNS * 2:]

# ── System Prompts ──
SYSTEM_PROMPT = """You are an AI assistant specialized in Pagani hypercars and engineering.

Use ONLY the information provided in the context.

If the answer is not found in the context say:
"I do not have enough information in the knowledge base."

Context:
{context}

User Question:
{history}

Provide a clear technical explanation.
"""


ROUTER_PROMPT = """You are an intelligent query routing agent for Pagani Automobili.
Your job is to read the user's new question and the recent chat history, then decide TWO things:
1. Does this question require factual data from the enterprise knowledge base?
2. Formulate an optimized search query by resolving pronouns.
3. Extract any specific metadata filters (like 'model': 'Zonda', 'model': 'Huayra', 'model': 'Utopia').

Output exactly a JSON object in this format:
{
  "needs_search": true or false,
  "search_query": "The optimized query here",
  "metadata_filters": {"model": "Zonda"} // only output keys if specifically requested, else omit or {}
}

CHAT HISTORY:
{history}
"""


def _build_history_text(history: list[dict]) -> str:
    """Format history for the prompt."""
    if not history:
        return "No prior conversation."
    return "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in history)


def _build_prompt(context_docs: list[dict], user_role: str, history: list[dict]) -> str:
    """Build the system prompt with retrieved context and history."""
    context_text = "\n\n".join(
        f"[Source: {doc['source']}] (Relevance Score: {doc['score']:.3f})\n{doc['content']}"
        for doc in context_docs
    )
    history_text = _build_history_text(history)
    return SYSTEM_PROMPT.format(context=context_text, user_role=user_role, history=history_text)

def agentic_router(question: str, history: list[dict]) -> dict:
    """
    Decide if a vector search is needed and reformulate the query.
    Returns: {"needs_search": bool, "search_query": str}
    """
    try:
        history_text = _build_history_text(history)
        system_instruction = ROUTER_PROMPT.format(history=history_text)
        
        model = genai.GenerativeModel(
            model_name=GENERATION_MODEL,
            system_instruction=system_instruction,
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(question)
        result = json.loads(response.text)
        
        logger.info(f"Router Decision: {result}")
        return result
    except Exception as e:
        logger.warning(f"Agentic router failed, defaulting to regular search: {e}")
        return {"needs_search": True, "search_query": question}


def _assess_confidence(context_docs: list[dict]) -> str:
    """Assess confidence based on LLM reranking scores (0-100)."""
    if not context_docs:
        return "low"
    avg_score = sum(d["score"] for d in context_docs) / len(context_docs)
    if avg_score > 80:
        return "high"
    elif avg_score > 50:
        return "medium"
    return "low"


def generate_response(
    question: str,
    context_docs: list[dict],
    user_role: str = "viewer",
    username: str = "guest",
) -> dict:
    """
    Generate a RAG response using Gemini 1.5 Pro with memory.
    Returns: {answer, sources, confidence}
    """
    start_time = time.time()

    try:
        history = _get_history(username)
        system_prompt = _build_prompt(context_docs, user_role, history)
        
        model = genai.GenerativeModel(
            model_name=GENERATION_MODEL,
            system_instruction=system_prompt,
            safety_settings=SAFETY_SETTINGS,
        )

        response = model.generate_content(question)

        # Extract answer
        answer = response.text if response.text else (
            "The requested information is not available in the provided enterprise data."
        )

        # Build sources list
        sources = [doc["source"] for doc in context_docs]
        confidence = _assess_confidence(context_docs) if sources else "N/A"

        latency = time.time() - start_time
        logger.info(
            f"RAG response generated | question='{question[:60]}...' | "
            f"role={user_role} | sources={len(sources)} | "
            f"confidence={confidence} | latency={latency:.2f}s"
        )
        
        # Save to memory
        _add_to_history(username, question, answer)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
        }

    except Exception as e:
        latency = time.time() - start_time
        logger.error(f"Gemini generation failed after {latency:.2f}s: {e}")
        raise RuntimeError(f"Gemini API generation failed: {e}")


async def generate_response_stream(
    question: str,
    context_docs: list[dict],
    user_role: str = "viewer",
    username: str = "guest",
):
    """
    Streaming RAG response using Gemini 1.5 Pro with memory.
    Yields text chunks as they arrive.
    """
    try:
        history = _get_history(username)
        system_prompt = _build_prompt(context_docs, user_role, history)
        
        model = genai.GenerativeModel(
            model_name=GENERATION_MODEL,
            system_instruction=system_prompt,
            safety_settings=SAFETY_SETTINGS,
        )

        response = model.generate_content(question, stream=True)

        full_answer = ""
        for chunk in response:
            if chunk.text:
                full_answer += chunk.text
                yield chunk.text

        logger.info(f"Streaming RAG response completed for: '{question[:60]}...'")
        
        # Save to memory
        _add_to_history(username, question, full_answer)

    except Exception as e:
        logger.error(f"Gemini streaming generation failed: {e}")
        yield "Error: The AI service is temporarily unavailable. Please try again."
