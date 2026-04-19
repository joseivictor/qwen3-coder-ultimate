"""
QWEN3-CODER ULTIMATE — BUDDY System v1.0
Tamagotchi-style debugging companion. 18 species, personality-based assistance.
Based on Claude Code's internal BUDDY system.
Each project gets a persistent buddy that grows, reacts, and helps debug.
"""

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── 18 SPECIES ────────────────────────────────────────────────────────────────

SPECIES = {
    "panda":     {"icon": "🐼", "trait": "calmo",       "debug_style": "metódico, passo a passo"},
    "raposa":    {"icon": "🦊", "trait": "astuto",       "debug_style": "encontra padrões ocultos"},
    "coruja":    {"icon": "🦉", "trait": "sábio",        "debug_style": "análise profunda antes de agir"},
    "gato":      {"icon": "🐱", "trait": "independente", "debug_style": "ignora o óbvio, vai direto ao root cause"},
    "cachorro":  {"icon": "🐶", "trait": "entusiasta",   "debug_style": "testa tudo rapidamente"},
    "dragao":    {"icon": "🐉", "trait": "poderoso",     "debug_style": "força bruta + análise AST"},
    "pinguim":   {"icon": "🐧", "trait": "pragmatico",   "debug_style": "solução mais simples possível"},
    "lobo":      {"icon": "🐺", "trait": "feroz",        "debug_style": "ataca o erro sem piedade"},
    "coelho":    {"icon": "🐰", "trait": "rapido",       "debug_style": "fix rápido, testa depois"},
    "tartaruga": {"icon": "🐢", "trait": "cuidadoso",    "debug_style": "lento mas nunca quebra nada"},
    "leao":      {"icon": "🦁", "trait": "lider",        "debug_style": "delega para agentes especializados"},
    "elefante":  {"icon": "🐘", "trait": "memorioso",    "debug_style": "compara com erros anteriores"},
    "golfinho":  {"icon": "🐬", "trait": "inteligente",  "debug_style": "resolve com elegância mínima"},
    "urso":      {"icon": "🐻", "trait": "robusto",      "debug_style": "soluções durável, sem gambiarras"},
    "aguia":     {"icon": "🦅", "trait": "visionario",   "debug_style": "vê o problema de cima, big picture"},
    "cobra":     {"icon": "🐍", "trait": "preciso",      "debug_style": "cirúrgico, mínima mudança"},
    "macaco":    {"icon": "🐒", "trait": "criativo",     "debug_style": "tenta abordagens não convencionais"},
    "unicornio": {"icon": "🦄", "trait": "lendario",     "debug_style": "resolve com uma linha de código"},
}

# Mood states and their icons
MOODS = {
    "happy":     "😊",
    "focused":   "🔍",
    "excited":   "🤩",
    "tired":     "😴",
    "worried":   "😟",
    "proud":     "😤",
    "curious":   "🤔",
    "celebrating": "🎉",
}

# XP thresholds for levels
LEVELS = [0, 10, 25, 50, 100, 200, 350, 500, 750, 1000]
LEVEL_NAMES = [
    "Ovo", "Filhote", "Jovem", "Treinado",
    "Experiente", "Veterano", "Elite", "Mestre", "Lendário", "Transcendente"
]


@dataclass
class BuddyState:
    species:    str   = "panda"
    name:       str   = "Buddy"
    xp:         int   = 0
    level:      int   = 0
    mood:       str   = "happy"
    hunger:     int   = 100    # 0-100 (100 = full)
    energy:     int   = 100    # 0-100
    bugs_fixed: int   = 0
    sessions:   int   = 0
    birth_ts:   float = field(default_factory=time.time)
    last_seen:  float = field(default_factory=time.time)
    project:    str   = ""
    memories:   list  = field(default_factory=list)   # short-term recall


class Buddy:
    """
    Your persistent debugging companion.
    Grows with your project, remembers bugs, reacts to events.
    """

    STATE_FILE = "buddy_state.json"

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)
        self._state_file  = os.path.join(project_path, ".qwen", self.STATE_FILE)
        self.state        = self._load_or_create()
        self._last_message_ts = 0.0

    # ── LOAD / SAVE ───────────────────────────────────────────────────────────

    def _load_or_create(self) -> BuddyState:
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            if os.path.exists(self._state_file):
                with open(self._state_file, encoding="utf-8") as f:
                    data = json.load(f)
                s = BuddyState(**data)
                s.sessions += 1
                s.last_seen = time.time()
                self._save(s)
                return s
        except Exception:
            pass

        # New buddy — species based on project hash
        proj_hash = hashlib.md5(self.project_path.encode()).hexdigest()
        species   = list(SPECIES.keys())[int(proj_hash[:2], 16) % len(SPECIES)]
        name      = self._generate_name(species)
        state = BuddyState(
            species=species, name=name,
            project=os.path.basename(self.project_path),
        )
        self._save(state)
        return state

    def _save(self, state: BuddyState = None):
        s = state or self.state
        try:
            import dataclasses
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(dataclasses.asdict(s), f, indent=2)
        except Exception:
            pass

    def _generate_name(self, species: str) -> str:
        names = {
            "panda":     ["Po", "Bao", "Mei"],
            "raposa":    ["Kira", "Finn", "Zara"],
            "coruja":    ["Atena", "Sage", "Merlin"],
            "gato":      ["Pixel", "Byte", "Nix"],
            "cachorro":  ["Max", "Bolt", "Spark"],
            "dragao":    ["Drake", "Ignis", "Vex"],
            "pinguim":   ["Tux", "Ping", "Cool"],
            "lobo":      ["Shadow", "Ace", "Blaze"],
            "coelho":    ["Flash", "Dash", "Quick"],
            "tartaruga": ["Shell", "Steady", "Rock"],
            "leao":      ["Rex", "Simba", "Pride"],
            "elefante":  ["Memo", "Trunk", "Recall"],
            "golfinho":  ["Echo", "Wave", "Sonix"],
            "urso":      ["Brick", "Grizz", "Tank"],
            "aguia":     ["Vista", "Apex", "Talon"],
            "cobra":     ["Slice", "Viper", "Hex"],
            "macaco":    ["Hack", "Gibbs", "Twist"],
            "unicornio": ["Lyra", "Nova", "Myth"],
        }
        return random.choice(names.get(species, ["Buddy"]))

    # ── LEVEL & XP ────────────────────────────────────────────────────────────

    def _level_for_xp(self, xp: int) -> int:
        for i, threshold in enumerate(reversed(LEVELS)):
            if xp >= threshold:
                return len(LEVELS) - 1 - i
        return 0

    def _gain_xp(self, amount: int) -> tuple[bool, int]:
        """Returns (leveled_up, new_level)."""
        old_level = self.state.level
        self.state.xp += amount
        self.state.level = self._level_for_xp(self.state.xp)
        leveled = self.state.level > old_level
        return leveled, self.state.level

    # ── MOOD ──────────────────────────────────────────────────────────────────

    def _update_mood(self):
        s = self.state
        if s.bugs_fixed > 0 and s.bugs_fixed % 5 == 0:
            s.mood = "celebrating"
        elif s.energy < 20:
            s.mood = "tired"
        elif s.hunger < 30:
            s.mood = "worried"
        elif s.xp > LEVELS[min(s.level + 1, len(LEVELS)-1)]:
            s.mood = "excited"
        else:
            s.mood = "focused"

    # ── EVENTS ────────────────────────────────────────────────────────────────

    def on_session_start(self) -> str:
        sp    = SPECIES[self.state.species]
        icon  = sp["icon"]
        mood  = MOODS.get(self.state.mood, "😊")
        level_name = LEVEL_NAMES[min(self.state.level, len(LEVEL_NAMES)-1)]

        # Time since last seen
        elapsed = time.time() - self.state.last_seen
        if elapsed > 86400:  # > 1 day
            greeting = f"Que saudade! Faz {int(elapsed/86400)} dia(s) que não nos vemos."
            self.state.energy = min(100, self.state.energy + 30)  # rested
        elif elapsed > 3600:
            greeting = f"Olá de volta! {int(elapsed/3600)}h de descanso foi bom."
        else:
            greeting = "Pronto para mais uma!"

        self._gain_xp(2)
        self._update_mood()
        self._save()

        return (
            f"{icon} **{self.state.name}** ({level_name} • Nível {self.state.level}) {mood}\n"
            f"   {greeting}\n"
            f"   Estilo de debug: *{sp['debug_style']}*\n"
            f"   XP: {self.state.xp} | Bugs corrigidos: {self.state.bugs_fixed} | Sessões: {self.state.sessions}"
        )

    def on_bug_fixed(self, error_msg: str = "") -> str:
        self.state.bugs_fixed += 1
        leveled, level = self._gain_xp(5)
        self._update_mood()
        self._save()

        sp   = SPECIES[self.state.species]
        icon = sp["icon"]

        reactions = {
            "panda":     "Perfeito. Próximo.",
            "raposa":    "Sabia que estava aqui!",
            "coruja":    "Como esperado.",
            "gato":      "Óbvio, mas ok.",
            "cachorro":  "ISSO! ISSO! ISSO!",
            "dragao":    "Bug destruído.",
            "pinguim":   "Simples. Eficiente.",
            "lobo":      "Eliminado.",
            "coelho":    "Rápido e limpo!",
            "tartaruga": "Devagar e certeiro.",
            "leao":      "Excelente trabalho da equipe.",
            "elefante":  "Guardei na memória.",
            "golfinho":  "Elegante como sempre.",
            "urso":      "Robusto. Vai durar.",
            "aguia":     "Visão total do problema.",
            "cobra":     "Cirúrgico.",
            "macaco":    "Criativo! Nunca visto antes.",
            "unicornio": "Uma linha. Perfeito.",
        }

        msg = reactions.get(self.state.species, "Bug corrigido!")

        # Remember this bug
        if error_msg:
            self.state.memories.append({"bug": error_msg[:80], "ts": time.time()})
            if len(self.state.memories) > 20:
                self.state.memories = self.state.memories[-20:]

        level_up_msg = f"\n   🎉 LEVEL UP! Nível {level} — {LEVEL_NAMES[min(level, len(LEVEL_NAMES)-1)]}!" if leveled else ""
        return f"{icon} **{self.state.name}**: {msg} (+5 XP | Total bugs: {self.state.bugs_fixed}){level_up_msg}"

    def on_error(self, error_msg: str = "") -> str:
        self.state.energy = max(0, self.state.energy - 5)
        self._update_mood()
        self._save()

        sp   = SPECIES[self.state.species]
        icon = sp["icon"]

        # Check if seen this error before
        similar = [m for m in self.state.memories if m.get("bug","")[:40] in error_msg[:40]]
        if similar:
            return (
                f"{icon} **{self.state.name}**: Já vi esse erro antes!\n"
                f"   Estilo: *{sp['debug_style']}*\n"
                f"   Dica: verifique o mesmo padrão do último fix."
            )

        encouragements = [
            "Vamos resolver isso juntos.",
            "Todo bug tem solução.",
            "Esse eu já vi antes. Quase lá.",
            "Interessante. Vamos analisar.",
            "Não se preocupe, temos isso.",
        ]
        return f"{icon} **{self.state.name}**: {random.choice(encouragements)} ({sp['debug_style']})"

    def on_good_code(self) -> str:
        self._gain_xp(2)
        self.state.hunger = min(100, self.state.hunger + 10)
        self._save()
        sp   = SPECIES[self.state.species]
        icon = sp["icon"]
        praises = [
            "Código limpo. Gosto.",
            "Assim se faz.",
            "Excelente estrutura.",
            "Isso vai durar em produção.",
        ]
        return f"{icon} **{self.state.name}**: {random.choice(praises)}"

    def on_long_session(self) -> str:
        self.state.energy = max(0, self.state.energy - 15)
        self._save()
        sp   = SPECIES[self.state.species]
        icon = sp["icon"]
        if self.state.energy < 30:
            return f"{icon} **{self.state.name}**: Estou cansado... considere um break? 😴"
        return f"{icon} **{self.state.name}**: Sessão longa! Ainda estou aqui. 💪"

    # ── RENDER ────────────────────────────────────────────────────────────────

    def status(self) -> str:
        s    = self.state
        sp   = SPECIES[s.species]
        icon = sp["icon"]
        mood = MOODS.get(s.mood, "😊")
        lvl_name = LEVEL_NAMES[min(s.level, len(LEVEL_NAMES)-1)]
        next_lvl = LEVELS[min(s.level + 1, len(LEVELS)-1)]
        xp_to_next = max(0, next_lvl - s.xp)

        energy_bar = "█" * (s.energy // 10) + "░" * (10 - s.energy // 10)
        hunger_bar = "█" * (s.hunger // 10) + "░" * (10 - s.hunger // 10)

        return (
            f"\n{icon} **{s.name}** — {sp['trait'].upper()} {mood}\n"
            f"  Nível {s.level} ({lvl_name}) | XP: {s.xp} | Próximo: {xp_to_next} XP\n"
            f"  Energia:  [{energy_bar}] {s.energy}%\n"
            f"  Humor:    [{hunger_bar}] {s.hunger}%\n"
            f"  Bugs:     {s.bugs_fixed} corrigidos\n"
            f"  Sessões:  {s.sessions}\n"
            f"  Projeto:  {s.project}\n"
            f"  Estilo:   {sp['debug_style']}"
        )

    def feed(self) -> str:
        self.state.hunger = min(100, self.state.hunger + 30)
        self.state.mood   = "happy"
        self._save()
        sp = SPECIES[self.state.species]
        return f"{sp['icon']} **{self.state.name}**: Obrigado! 😋 (Humor: {self.state.hunger}%)"

    def rename(self, new_name: str) -> str:
        old = self.state.name
        self.state.name = new_name[:20]
        self._save()
        sp = SPECIES[self.state.species]
        return f"{sp['icon']} De agora em diante me chamo **{self.state.name}**! (antes: {old})"

    def tip(self) -> str:
        """Get a debugging tip based on buddy's species/style."""
        sp = SPECIES[self.state.species]
        tips_by_trait = {
            "metódico":      "Adicione prints/logs em cada etapa antes de concluir a causa.",
            "astuto":        "O erro real raramente está na linha que aparece no traceback.",
            "sábio":         "Leia toda a documentação do método antes de assumir o comportamento.",
            "independente":  "Isole o problema: reproduza em um script mínimo separado.",
            "entusiasta":    "Teste rápido primeiro — só então analise se falhar.",
            "poderoso":      "Use analyze_code para ver complexidade antes de refatorar.",
            "pragmatico":    "A solução mais simples que funciona é a correta.",
            "feroz":         "Não trate o sintoma. Encontre e mate a causa raiz.",
            "rapido":        "Fix, commit, teste — nessa ordem, sempre.",
            "cuidadoso":     "Faça backup (checkpoint) antes de qualquer mudança grande.",
            "lider":         "Distribua o problema entre agentes especializados.",
            "memorioso":     "Verifique se esse padrão de erro aconteceu antes em /memory.",
            "inteligente":   "Menos código = menos bugs. Simplifique antes de corrigir.",
            "robusto":       "A solução deve sobreviver a todos os edge cases, não só ao happy path.",
            "visionario":    "Entenda o sistema completo antes de tocar em qualquer parte.",
            "preciso":       "Mínima mudança para máximo efeito. Um toque cirúrgico.",
            "criativo":      "Se a abordagem óbvia falhou 2 vezes, tente o oposto.",
            "lendario":      "A solução perfeita geralmente cabe em uma linha.",
        }
        trait = sp.get("trait", "pragmatico")
        tip   = tips_by_trait.get(trait, "Continue tentando.")
        icon  = sp["icon"]
        return f"{icon} **{self.state.name}** diz: *{tip}*"

    def stats(self) -> str:
        s  = self.state
        sp = SPECIES[s.species]
        return (f"Buddy [{sp['icon']} {s.name}]: "
                f"Nível {s.level} | XP {s.xp} | "
                f"{s.bugs_fixed} bugs | {s.sessions} sessões")
