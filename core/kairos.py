"""
QWEN3-CODER ULTIMATE — KAIROS v1.0
Proactive in-session assistance. Detects when user is stuck, confused,
or missing an opportunity — and offers help unprompted.
Based on Claude Code's KAIROS internal system.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KairosSignal:
    type:       str   # stuck | loop | opportunity | confusion | long_silence
    message:    str
    suggestion: str
    confidence: float
    timestamp:  float = field(default_factory=time.time)


class Kairos:
    """
    Proactive assistance engine. Analyzes conversation patterns and detects:
    - User is stuck (same question repeated, no progress)
    - Conversation is looping (going in circles)
    - Missed opportunity (user doesn't know a feature exists)
    - Confusion signals (short frustrated messages)
    - Long silence after complex output (user might be lost)

    Fires a suggestion when confidence exceeds threshold.
    Non-intrusive: suggestions are shown inline, not as interruptions.
    """

    CONFIDENCE_THRESHOLD = 0.72

    STUCK_PATTERNS = [
        r"ainda não|still not|não funciona|not working|mesmo erro|same error",
        r"por que não|why (doesn't|isn't|won't)|não entendo|don't understand",
        r"tentei|tried|já fiz|already did|fiz isso|did that",
    ]

    CONFUSION_PATTERNS = [
        r"^\s*\?\s*$",            # just "?"
        r"^(o que|what|huh|hein|como assim|como funciona)\??$",
        r"não sei|i don't know|lost|perdido|confused",
    ]

    OPPORTUNITY_MAP = [
        ("pytest|unittest|test", "Quer que eu gere os testes automaticamente? Use /test ou `generate_tests`."),
        ("security|segurança|vulnerab", "Posso rodar um scan de segurança OWASP completo. Use /security ou `security_scan`."),
        ("refactor|refatorar|limpar|clean", "Posso fazer a refatoração automaticamente com análise AST. Use /refactor."),
        ("documenta|docstring|readme", "Posso gerar documentação automática para o projeto inteiro."),
        ("deploy|ci|pipeline|github action", "Posso gerar workflows de CI/CD e integrar com GitHub Actions."),
        ("performance|lento|slow|otimiz", "Posso analisar complexidade ciclomática e gerar relatório de performance."),
        ("memori|remember|lembrar|context", "Use /memory para salvar informações que precisam persistir entre sessões."),
        ("parallel|paraleliz|concurrent", "O AgentPool pode rodar 8 agentes especializados em paralelo. Use /agent."),
        ("worktree|branch|isolated", "Posso criar um git worktree isolado para essa feature. Use /wt create."),
        ("web ui|interface|browser", "Tem uma Web UI disponível. Use /webui para abrir no browser."),
    ]

    def __init__(self, client=None, model: str = ""):
        self.client   = client
        self.model    = model
        self._history_window: list[dict] = []
        self._last_signal_ts: float = 0.0
        self._signal_cooldown = 120.0  # min seconds between signals
        self._stats = {"signals": 0, "shown": 0, "acted_on": 0}

    # ── MAIN ENTRY ────────────────────────────────────────────────────────────

    def analyze(self, history: list, last_user_msg: str,
                last_response: str = "") -> Optional[KairosSignal]:
        """
        Analyze conversation after each turn.
        Returns a KairosSignal if something actionable is detected, else None.
        """
        now = time.time()
        if now - self._last_signal_ts < self._signal_cooldown:
            return None  # cooldown

        self._history_window = history[-12:]

        # Check signals in priority order
        signal = (
            self._check_stuck(last_user_msg) or
            self._check_confusion(last_user_msg) or
            self._check_loop() or
            self._check_opportunity(last_user_msg, last_response)
        )

        if signal and signal.confidence >= self.CONFIDENCE_THRESHOLD:
            self._last_signal_ts = now
            self._stats["signals"] += 1
            return signal

        return None

    # ── DETECTORS ─────────────────────────────────────────────────────────────

    def _check_stuck(self, msg: str) -> Optional[KairosSignal]:
        """Detect if user is stuck — repeating the same problem."""
        msg_lower = msg.lower()
        for pattern in self.STUCK_PATTERNS:
            if re.search(pattern, msg_lower):
                # Check if similar messages appeared before
                similar_count = sum(
                    1 for m in self._history_window
                    if m.get("role") == "user" and
                    len(set(msg_lower.split()) & set(str(m.get("content","")).lower().split())) > 4
                )
                if similar_count >= 2:
                    return KairosSignal(
                        type="stuck",
                        message="Parece que você está preso nesse ponto.",
                        suggestion=(
                            "Posso tentar uma abordagem diferente:\n"
                            "• `/plan` — deixa eu criar um plano passo-a-passo\n"
                            "• `/debug` — modo debug com chain-of-thought\n"
                            "• `/reason` — análise profunda do problema"
                        ),
                        confidence=0.80,
                    )
        return None

    def _check_confusion(self, msg: str) -> Optional[KairosSignal]:
        """Detect short confused messages."""
        stripped = msg.strip()
        if len(stripped) < 15:
            for pattern in self.CONFUSION_PATTERNS:
                if re.search(pattern, stripped, re.IGNORECASE):
                    return KairosSignal(
                        type="confusion",
                        message="Parece que a resposta anterior não ficou clara.",
                        suggestion=(
                            "Posso reformular de forma diferente. O que exatamente ficou confuso?\n"
                            "Ou tente: `/explain` para uma explicação mais detalhada."
                        ),
                        confidence=0.75,
                    )
        return None

    def _check_loop(self) -> Optional[KairosSignal]:
        """Detect circular conversation — going back and forth."""
        user_msgs = [
            str(m.get("content", ""))[:100].lower()
            for m in self._history_window
            if m.get("role") == "user"
        ]
        if len(user_msgs) < 4:
            return None

        # Check for near-duplicate user messages
        for i in range(len(user_msgs) - 2):
            words_a = set(user_msgs[i].split())
            words_b = set(user_msgs[i+2].split())
            if len(words_a) > 3 and len(words_b) > 3:
                overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
                if overlap > 0.65:
                    return KairosSignal(
                        type="loop",
                        message="A conversa parece estar em loop.",
                        suggestion=(
                            "Vamos resetar a abordagem:\n"
                            "• `/clear` — limpa histórico, começa fresh\n"
                            "• `/plan` — decompomos o problema em partes menores\n"
                            "• Descreva o objetivo final em uma frase"
                        ),
                        confidence=0.78,
                    )
        return None

    def _check_opportunity(self, msg: str, response: str) -> Optional[KairosSignal]:
        """Detect when user could benefit from a feature they don't know about."""
        combined = (msg + " " + response).lower()
        for keyword_pattern, suggestion in self.OPPORTUNITY_MAP:
            if re.search(keyword_pattern, combined):
                # Don't suggest if they already used the feature
                if any(kw in combined for kw in ["já usei", "already used", "i know", "sei disso"]):
                    continue
                return KairosSignal(
                    type="opportunity",
                    message="Detectei uma oportunidade.",
                    suggestion=suggestion,
                    confidence=0.73,
                )
        return None

    # ── RENDER ────────────────────────────────────────────────────────────────

    def render(self, signal: KairosSignal) -> str:
        icons = {
            "stuck":       "🔄",
            "confusion":   "💡",
            "loop":        "↩",
            "opportunity": "⚡",
            "long_silence": "👋",
        }
        icon = icons.get(signal.type, "💡")
        self._stats["shown"] += 1
        return (
            f"\n{icon} **KAIROS** — {signal.message}\n"
            f"{signal.suggestion}\n"
        )

    def mark_acted_on(self):
        self._stats["acted_on"] += 1
        self._last_signal_ts = time.time() + self._signal_cooldown

    def stats(self) -> str:
        return (
            f"Kairos: {self._stats['signals']} signals | "
            f"{self._stats['shown']} shown | "
            f"{self._stats['acted_on']} acted on"
        )
