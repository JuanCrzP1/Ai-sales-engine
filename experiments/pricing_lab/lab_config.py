from __future__ import annotations

import os
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parent
REPO_ROOT = LAB_DIR.parents[1]
PROJECT_DIR = REPO_ROOT / "project"
RESULTS_DIR = LAB_DIR / "results"

DEFAULT_CHANNEL = os.getenv("PRICING_LAB_CHANNEL", "whatsapp").strip() or "whatsapp"
DEFAULT_USER_ID = os.getenv("PRICING_LAB_USER_ID", "pricing-lab-user").strip() or "pricing-lab-user"
DEFAULT_TENANT = os.getenv("PRICING_LAB_TENANT", "").strip()

GOLDEN_TURNS = [
    "Hola amigo",
    "Dame más información de lo que venden",
    "Yo recibo muchos mensajes y no alcanzo a responder",
    "¿Cómo funciona eso?",
    "¿De verdad eso me puede ayudar a vender más?",
    "¿Por dónde funciona?",
    "¿Y qué precio tiene?",
    "¿Qué incluye?",
    "¿Qué no incluye?",
    "Está caro, pero si me sirve quiero empezar",
]

CANONICAL_RESULT_FILES = {
    "baseline_prompt": RESULTS_DIR / "baseline_prompt.txt",
    "baseline_metrics": RESULTS_DIR / "baseline_metrics.json",
    "candidate_prompt": RESULTS_DIR / "candidate_prompt.txt",
    "candidate_metrics": RESULTS_DIR / "candidate_metrics.json",
    "comparison": RESULTS_DIR / "conversation_comparison.md",
    "evolution": RESULTS_DIR / "evolution_log.md",
}
