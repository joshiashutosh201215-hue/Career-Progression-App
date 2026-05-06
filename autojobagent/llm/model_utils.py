"""Shared model and text utilities for the AutoJobAgent AI modules.

The project intentionally uses Hugging Face models because they can be loaded
directly from Python, cached locally, and called without a separate inference
server.  This file keeps the model-loading details in one place so the matching,
skill extraction, and cover-letter modules stay small.
"""

import os
import re
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_GENERATION_MODEL = "google/flan-t5-small"


class LocalModelError(RuntimeError):
    """Raised when a local Hugging Face model cannot be loaded or executed."""


def configure_models(model_config: Optional[Dict[str, str]]) -> None:
    """Apply model names from config before any cached model is loaded."""
    if not model_config:
        return

    embedding_model = model_config.get("embedding")
    generation_model = model_config.get("generation")

    if embedding_model:
        os.environ["AUTOJOB_EMBEDDING_MODEL"] = embedding_model
        _load_embedder_result.cache_clear()

    if generation_model:
        os.environ["AUTOJOB_GENERATION_MODEL"] = generation_model
        _load_generation_result.cache_clear()

    if "local_files_only" in model_config:
        os.environ["AUTOJOB_HF_LOCAL_ONLY"] = str(model_config["local_files_only"]).lower()
        _load_embedder_result.cache_clear()
        _load_generation_result.cache_clear()


def get_embedding_model_name() -> str:
    """Return the configured sentence embedding model name."""
    return os.getenv("AUTOJOB_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def get_generation_model_name() -> str:
    """Return the configured instruction-generation model name."""
    return os.getenv("AUTOJOB_GENERATION_MODEL", DEFAULT_GENERATION_MODEL)


@lru_cache(maxsize=1)
def _load_embedder_result():
    """Load the embedder once and cache either success or failure."""
    try:
        from sentence_transformers import SentenceTransformer

        embedder = SentenceTransformer(
            get_embedding_model_name(),
            device="cpu",
            local_files_only=hf_local_files_only(),
        )
        return embedder, None
    except Exception as exc:
        return None, f"Could not load embedding model: {exc}"


def get_embedder():
    """Return the cached sentence-transformers embedder or raise a local error."""
    embedder, error = _load_embedder_result()
    if error:
        raise LocalModelError(error)
    return embedder


@lru_cache(maxsize=1)
def _load_generation_result():
    """Load generation components once and cache either success or failure."""
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from transformers.utils import logging as transformers_logging

        transformers_logging.set_verbosity_error()

        model_name = get_generation_model_name()
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            local_files_only=hf_local_files_only(),
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            local_files_only=hf_local_files_only(),
        )
        model.to("cpu")
        model.eval()
        return (tokenizer, model), None
    except Exception as exc:
        return None, f"Could not load generation model: {exc}"


def get_generation_components():
    """Return cached seq2seq components without using removed pipeline tasks."""
    components, error = _load_generation_result()
    if error:
        raise LocalModelError(error)
    return components


def hf_local_files_only() -> bool:
    """Return True when Hugging Face should avoid network downloads."""
    return os.getenv("AUTOJOB_HF_LOCAL_ONLY", "").lower() in {"1", "true", "yes"}


def generate_text(prompt: str, max_new_tokens: int = 160) -> str:
    """Generate text with the local Hugging Face seq2seq model."""
    try:
        import torch

        tokenizer, model = get_generation_components()
        inputs = tokenizer(
            prompt,
            max_length=1024,
            return_tensors="pt",
            truncation=True,
        )
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=4,
                do_sample=False,
                early_stopping=True,
            )
        return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    except LocalModelError:
        raise
    except Exception as exc:
        raise LocalModelError(f"Text generation failed: {exc}") from exc


def detect_mandatory_german(text: str) -> str:
    """Detect whether German language is explicitly required in a job post."""
    lower_text = text.lower()
    mandatory_phrases = [
        "german mandatory",
        "german required",
        "german language",
        "deutsch zwingend",
        "deutsch erforderlich",
        "deutschkenntnisse erforderlich",
        "fluent german",
        "german fluency",
        "german is required",
        "german speaker",
    ]
    return "German" if any(phrase in lower_text for phrase in mandatory_phrases) else ""


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching and simple overlap heuristics."""
    return re.sub(r"[^a-z0-9+#/.\s-]", " ", text.lower())


def important_tokens(text: str) -> List[str]:
    """Return useful non-stopword tokens for fallback matching."""
    stopwords = {
        "about",
        "after",
        "also",
        "and",
        "are",
        "based",
        "but",
        "can",
        "for",
        "from",
        "have",
        "into",
        "our",
        "the",
        "this",
        "with",
        "will",
        "you",
        "your",
    }
    tokens = re.findall(r"[a-z0-9+#/.]{3,}", normalize_text(text))
    return [token for token in tokens if token not in stopwords]


def extract_keyword_skills(text: str, max_items: int = 5) -> List[str]:
    """Extract skills with deterministic rules when the generation model is absent."""
    raw_lower = text.lower()
    normalized = normalize_text(text)
    skill_patterns = [
        ("AUTOSAR", ["autosar"]),
        ("System Architecture", ["system architecture", "architect"]),
        ("Software Architecture", ["software architecture"]),
        ("Embedded Software", ["embedded software", "firmware"]),
        ("Diagnostics", ["diagnostics", "uds", "doip", "obd"]),
        ("UDS", ["uds"]),
        ("DoIP", ["doip"]),
        ("CAN", [" can ", "can bus", "j1939"]),
        ("Ethernet", ["ethernet"]),
        ("SOME/IP", ["some/ip", "someip"]),
        ("Cybersecurity", ["cybersecurity", "secure boot", "secure flashing"]),
        ("Functional Safety", ["functional safety", "iso 26262"]),
        ("ISO 26262", ["iso 26262"]),
        ("ISO 24089", ["iso 24089"]),
        ("UNECE R155/R156", ["r155", "r156", "unece"]),
        ("OTA Updates", ["ota", "software update", "sums"]),
        ("Python", ["python"]),
        ("C/C++", ["c++", "c/c++", " c "]),
        ("Linux", ["linux"]),
        ("Docker", ["docker", "container"]),
        ("Git", ["git"]),
        ("CI/CD", ["ci/cd", "jenkins"]),
        ("MATLAB/Simulink", ["matlab", "simulink"]),
        ("Computer Vision", ["computer vision", "opencv", "yolo"]),
        ("PyTorch", ["pytorch", "torch"]),
        ("Stakeholder Management", ["stakeholder", "cross-functional"]),
        ("Supplier Management", ["supplier"]),
        ("Agile/Scrum", ["scrum", "agile"]),
    ]

    skills: List[str] = []
    for display_name, triggers in skill_patterns:
        if any(trigger in raw_lower or trigger in normalized for trigger in triggers):
            skills.append(display_name)
            if len(skills) == max_items:
                return skills

    for token in _ordered_unique(important_tokens(text)):
        if token.upper() not in {skill.upper() for skill in skills}:
            skills.append(token.upper() if len(token) <= 4 else token.title())
        if len(skills) == max_items:
            break

    return skills


def _ordered_unique(items: Iterable[str]) -> List[str]:
    """Preserve first-seen order while removing duplicates."""
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items
