"""
QWEN3-CODER ULTIMATE — Reasoning Engine v1.0
Chain-of-Thought, Tree-of-Thought, Self-Reflection, Confidence Scoring.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReasoningStep:
    step_num: int
    thought: str
    action: Optional[str] = None
    result: Optional[str] = None
    confidence: float = 0.0
    valid: bool = True


@dataclass
class ThoughtNode:
    content: str
    score: float = 0.0
    children: list = field(default_factory=list)
    parent: Optional["ThoughtNode"] = None
    depth: int = 0


class ReasoningEngine:
    """
    Advanced reasoning engine with CoT scaffolding, ToT branching,
    self-reflection loops and confidence scoring per response.
    """

    REFLECTION_PROMPT = """Review your previous response critically:
1. Is the solution correct and complete?
2. Are there edge cases not handled?
3. Is there a simpler or more efficient approach?
4. Any bugs or logical errors?

If improvements are needed, provide the corrected version.
If the solution is solid, respond with: [APPROVED]"""

    CONFIDENCE_PROMPT = """Rate your confidence in this response on a scale 0-100.
Consider: correctness, completeness, edge cases, potential issues.
Respond ONLY with a JSON: {"score": <number>, "reason": "<brief reason>"}"""

    def __init__(self, client, model: str, max_tokens: int = 4096):
        self.client     = client
        self.model      = model
        self.max_tokens = max_tokens
        self._stats     = {"total_calls": 0, "reflections": 0, "avg_confidence": 0.0}

    def _call(self, messages: list, max_tokens: int = None, temperature: float = 0.1) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature,
                stream=False,
            )
            self._stats["total_calls"] += 1
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[ReasoningEngine error: {e}]"

    # ── CHAIN-OF-THOUGHT ──────────────────────────────────────────────────────
    def chain_of_thought(self, problem: str, context: str = "", steps: int = 4) -> list[ReasoningStep]:
        """Scaffold step-by-step reasoning with validation at each step."""
        system = (
            "You are an expert problem-solver. Think step by step. "
            "For each step output JSON: {\"step\": N, \"thought\": \"...\", \"action\": \"...\", \"confidence\": 0-100}\n"
            "Be concise and precise."
        )
        messages = [{"role": "system", "content": system}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nProblem: {problem}\n\nStep 1:"})
        else:
            messages.append({"role": "user", "content": f"Problem: {problem}\n\nStep 1:"})

        reasoning_steps = []
        prev_thoughts = ""

        for i in range(1, steps + 1):
            raw = self._call(messages, max_tokens=512, temperature=0.15)

            step = self._parse_step(raw, i)
            step = self._validate_step(step, prev_thoughts)
            reasoning_steps.append(step)

            prev_thoughts += f"\nStep {i}: {step.thought}"
            messages.append({"role": "assistant", "content": raw})
            if i < steps:
                messages.append({"role": "user", "content": f"Continue. Step {i+1}:"})

        return reasoning_steps

    def _parse_step(self, raw: str, step_num: int) -> ReasoningStep:
        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(raw[start:end])
                return ReasoningStep(
                    step_num   = step_num,
                    thought    = data.get("thought", raw[:200]),
                    action     = data.get("action"),
                    confidence = float(data.get("confidence", 70)) / 100,
                )
        except Exception:
            pass
        return ReasoningStep(step_num=step_num, thought=raw[:300], confidence=0.5)

    def _validate_step(self, step: ReasoningStep, prev_context: str) -> ReasoningStep:
        if len(step.thought.strip()) < 5:
            step.valid = False
            return step
        if step.confidence < 0.3:
            system = "You are a critical reviewer. Is this reasoning step sound? Reply with JSON {\"valid\": true/false, \"reason\": \"...\"}."
            msg = [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Previous steps: {prev_context}\nThis step: {step.thought}"},
            ]
            raw = self._call(msg, max_tokens=150, temperature=0.1)
            try:
                data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
                step.valid = data.get("valid", True)
            except Exception:
                step.valid = True
        return step

    # ── TREE-OF-THOUGHT ───────────────────────────────────────────────────────
    def tree_of_thought(self, problem: str, branches: int = 3, depth: int = 2) -> ThoughtNode:
        """Explore multiple reasoning paths and score them, returning the best."""
        root = ThoughtNode(content=problem, depth=0)
        self._expand_node(root, branches=branches, max_depth=depth)
        best = self._find_best_leaf(root)
        return best

    def _expand_node(self, node: ThoughtNode, branches: int, max_depth: int):
        if node.depth >= max_depth:
            node.score = self._score_thought(node)
            return

        system = (
            f"Generate {branches} distinct approaches to this problem/thought. "
            f"Output JSON array: [{{\"approach\": \"...\"}}, ...]"
        )
        messages = [
            {"role": "system",  "content": system},
            {"role": "user",    "content": f"Problem: {node.content}"},
        ]
        raw = self._call(messages, max_tokens=600, temperature=0.7)

        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            items = json.loads(raw[start:end])
            for item in items[:branches]:
                child = ThoughtNode(
                    content = item.get("approach", str(item)),
                    parent  = node,
                    depth   = node.depth + 1,
                )
                node.children.append(child)
                self._expand_node(child, branches, max_depth)
        except Exception:
            leaf = ThoughtNode(content=raw[:200], parent=node, depth=node.depth+1)
            node.children.append(leaf)
            leaf.score = self._score_thought(leaf)

    def _score_thought(self, node: ThoughtNode) -> float:
        system = (
            "Rate this solution/approach on a scale 0-100 considering: "
            "correctness, elegance, completeness, efficiency. "
            "Reply ONLY with JSON: {\"score\": <number>}"
        )
        chain = []
        cur = node
        while cur.parent:
            chain.insert(0, cur.content)
            cur = cur.parent
        path = " → ".join(chain) or node.content

        raw = self._call(
            [{"role": "system", "content": system},
             {"role": "user",   "content": f"Approach chain: {path[:800]}"}],
            max_tokens=60, temperature=0.1
        )
        try:
            data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
            return float(data.get("score", 50)) / 100
        except Exception:
            return 0.5

    def _find_best_leaf(self, node: ThoughtNode) -> ThoughtNode:
        if not node.children:
            return node
        best = None
        for child in node.children:
            candidate = self._find_best_leaf(child)
            if best is None or candidate.score > best.score:
                best = candidate
        return best or node

    # ── SELF-REFLECTION ───────────────────────────────────────────────────────
    def reflect_and_refine(self, original_response: str, task: str,
                            max_iterations: int = 2) -> tuple[str, int]:
        """
        Critique and refine a response up to max_iterations times.
        Returns (refined_response, iterations_taken).
        """
        current = original_response
        self._stats["reflections"] += 1

        for i in range(max_iterations):
            messages = [
                {"role": "system",    "content": self.REFLECTION_PROMPT},
                {"role": "user",      "content": f"Task: {task}\n\nYour response:\n{current}"},
            ]
            feedback = self._call(messages, max_tokens=1024, temperature=0.1)

            if "[APPROVED]" in feedback.upper():
                return current, i

            refinement_prompt = (
                f"Task: {task}\n\n"
                f"Original response:\n{current}\n\n"
                f"Critique:\n{feedback}\n\n"
                "Provide the improved, complete response:"
            )
            current = self._call(
                [{"role": "system", "content": "You are an expert. Produce the best possible response."},
                 {"role": "user",   "content": refinement_prompt}],
                max_tokens=self.max_tokens, temperature=0.1
            )

        return current, max_iterations

    # ── CONFIDENCE SCORING ────────────────────────────────────────────────────
    def score_confidence(self, response: str, task: str) -> dict:
        """Rate confidence in a response and return score + reasoning."""
        messages = [
            {"role": "system", "content": self.CONFIDENCE_PROMPT},
            {"role": "user",   "content": f"Task: {task}\n\nResponse: {response[:1500]}"},
        ]
        raw = self._call(messages, max_tokens=120, temperature=0.1)
        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            data  = json.loads(raw[start:end])
            score = max(0, min(100, int(data.get("score", 70))))
            self._stats["avg_confidence"] = (
                (self._stats["avg_confidence"] * (self._stats["total_calls"] - 1) + score)
                / self._stats["total_calls"]
                if self._stats["total_calls"] > 0 else score
            )
            return {"score": score, "reason": data.get("reason", ""), "level": self._level(score)}
        except Exception:
            return {"score": 70, "reason": "Could not parse confidence", "level": "medium"}

    def _level(self, score: int) -> str:
        if score >= 85: return "high"
        if score >= 60: return "medium"
        return "low"

    # ── FULL PIPELINE ─────────────────────────────────────────────────────────
    def reason(self, problem: str, context: str = "", use_tot: bool = False,
               reflect: bool = True, cot_steps: int = 3) -> dict:
        """
        Full reasoning pipeline: CoT → (optional ToT) → generate answer →
        (optional reflection) → confidence score.
        Returns a structured result dict.
        """
        start_time = time.time()
        result = {"problem": problem, "steps": [], "answer": "", "confidence": {}, "elapsed": 0}

        # Step 1: Chain-of-Thought
        steps = self.chain_of_thought(problem, context, steps=cot_steps)
        result["steps"] = [
            {"step": s.step_num, "thought": s.thought, "confidence": round(s.confidence, 2), "valid": s.valid}
            for s in steps
        ]

        # Step 2: Optionally Tree-of-Thought for branching
        tot_insight = ""
        if use_tot:
            best_node = self.tree_of_thought(problem, branches=3, depth=2)
            tot_insight = f"\nBest approach found (score {best_node.score:.0%}): {best_node.content}"

        # Step 3: Generate final answer from reasoning
        reasoning_summary = "\n".join(
            f"Step {s['step']}: {s['thought']}" for s in result["steps"] if s["valid"]
        )
        final_prompt = (
            f"Problem: {problem}\n"
            f"Reasoning:\n{reasoning_summary}{tot_insight}\n\n"
            "Now provide the complete, final solution:"
        )
        answer = self._call(
            [{"role": "system", "content": "You are an expert. Using the provided reasoning, give the best final answer."},
             {"role": "user",   "content": final_prompt}],
            temperature=0.15
        )

        # Step 4: Self-reflection
        if reflect:
            answer, iters = self.reflect_and_refine(answer, problem, max_iterations=1)
            result["reflections"] = iters

        result["answer"]     = answer
        result["confidence"] = self.score_confidence(answer, problem)
        result["elapsed"]    = round(time.time() - start_time, 2)
        return result

    def stats(self) -> str:
        return (
            f"ReasoningEngine stats:\n"
            f"  Total LLM calls: {self._stats['total_calls']}\n"
            f"  Reflections run: {self._stats['reflections']}\n"
            f"  Avg confidence:  {self._stats['avg_confidence']:.1f}/100"
        )
