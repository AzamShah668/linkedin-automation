"""Answer the genuinely per-company free-text question with the LLM. Nothing else.

WHY THIS EXISTS
---------------
After the 2026-08-15 survey the bank answers 102 of 104 distinct questions. The one that
remains and matters is *"Why do you want to join our company?"* - different for every
employer by definition, so a banked generic would be exactly the templated filler this
project exists not to send. [[22-rewrite-architecture]]: same every time -> code, different
every time -> AI. This is the "different every time" half, and it is deliberately tiny.

⚠️ THE DANGER, STATED PLAINLY
An LLM writing onto a real employer's form is the fabrication risk the answer bank was built
to eliminate (D31: the bank proves where a value came from, never that it is right). So this
module is a narrow exception with three hard limits:

1. **Motivation questions only.** `is_llm_answerable()` REFUSES anything that asks for a
   checkable fact - years, salary, certifications, passport, CGPA, dates, notice period,
   yes/no. Those must come from the bank or stay blank. An invented "3 years of Databricks"
   is caught in the first technical screen; an invented reason for wanting a job is not a
   falsifiable claim about his history.
2. **Grounded.** The prompt carries only facts already in the bank and the CV, and forbids
   any claim not present in them.
3. **Loud.** Every generated answer is returned with its prompt so the caller can log it.
   A silent LLM answer on an employer's form is the worst of both worlds.

If the model is unreachable or the answer looks wrong, the field is LEFT BLANK. Blank beats
wrong, unchanged.
"""

from __future__ import annotations

import re

from apps.autopilot import llm

# Anything asking for a verifiable fact. If a label matches ANY of these, the LLM never sees
# it - the bank answers it or it stays blank.
FACTUAL = re.compile(
    r"how (many|much|long)|\byears?\b|\bmonths?\b|salary|ctc|compensation|\bpay\b|stipend"
    r"|certif|passport|\bcgpa\b|percentage|\bgpa\b|aggregate|notice period|last working"
    r"|date of birth|\bdob\b|current (employer|company)|offer in hand|visa|sponsor"
    r"|willing to relocate|do you have|have you (ever|worked|managed|completed)"
    r"|are you (comfortable|available|willing|serving)|rate your",
    re.I,
)

# What we WILL answer: motivation / fit prose, and only when phrased as a real question.
MOTIVATION = re.compile(
    r"why (do|would) you (want|like) to (join|work)|why (are you )?interested"
    r"|why (this|our) (company|role|position)|what (interests|excites) you"
    r"|why should we (hire|consider)|tell us why|motivation for applying",
    re.I,
)

MAX_WORDS = 70


def _budget_line(max_chars: int | None) -> str:
    """Tell the model the character cap the FORM enforces, in characters, not words.

    ⚠️ Never phrase this as a word count. Asking gemini-3.5-flash-lite for "70 words or fewer"
    made it number the words as it wrote - "who (20) runs (21) production (22)" - and burn the
    budget doing it. A character cap it simply respects.
    """
    if not max_chars:
        return ""
    return (f"HARD LIMIT: your entire answer must be under {max_chars} characters. "
            f"Finish the final sentence within that.")

# ⚠️ 4096, not llm.DEFAULT_MAX_TOKENS (1024). Measured 2026-08-15 on the SAME prompt:
#     1024 -> 26 words, ended mid-clause on a comma
#     4096 -> 48 words, complete sentence with a full stop
# Every current Gemini is a reasoning model whose hidden thinking shares this budget (D42).
# The 1024 default was calibrated against SHORT prompts; this one carries a fact list, so the
# thinking pass alone consumes most of 1024 and the answer gets whatever is left. The symptom
# is not an error - it is a fluent half-sentence, which is exactly the failure the truncation
# guard below exists to catch. A budget is not a limit you tune down for tidiness.
FREETEXT_MAX_TOKENS = 4096


def is_llm_answerable(label: str) -> bool:
    """True only for motivation prose. Deliberately a whitelist, not a blacklist."""
    text = (label or "").strip()
    if len(text) < 12:
        return False
    if FACTUAL.search(text):
        return False
    return bool(MOTIVATION.search(text))


def build_prompt(label: str, company: str, role: str, max_chars: int | None = None) -> str:
    """Only facts already recorded in this repo. No new claims are introduced here.

    ⚠️ Do NOT put a word COUNT in this prompt. Asking gemini-3.5-flash-lite for "70 words or
    fewer" made it number the words as it wrote - literally emitting "who (20) runs (21)
    production (22)" - and burn its budget doing so, which produced a truncated answer on
    every attempt. Measured 2026-08-15. Constrain by SENTENCES; enforce the word cap in code.
    """
    return f"""Write one short answer on a job application form, in first person, as Azam Shah.

QUESTION: "{label}"
COMPANY: {company or "unknown"}
ROLE: {role or "unknown"}
{_budget_line(max_chars)}

Facts you may use (use nothing else):
- Final-year B.Tech Computer Science student; DevOps Engineer at Verventech, Srinagar, India.
- Built a 7-service private cloud on Proxmox: bare host to running platform in one Ansible run.
- Runs production RAG on a 2-node GPU Kubernetes cluster, with a Jenkins gate that blocks bad
  model deploys.
- Stack: Docker, Kubernetes, Jenkins, Ansible, Python, FastAPI, PostgreSQL, RAG and LLMs.
- Owns the whole stack end to end; wants to do that at a larger scale with a stronger team.

Rules:
- Write two or three complete sentences. End the last one with a full stop.
- Use only the facts above. Do not invent anything about this company's products, customers,
  funding or news. If you know nothing specific about them, write about what he brings.
- No em-dashes. No flattery. Do not write "I am excited about this opportunity".
- Output only the answer text.

Answer:"""


def answer(
    label: str, company: str = "", role: str = "", max_chars: int | None = None
) -> tuple[str | None, str]:
    """Return (answer, why). `answer` is None whenever the field must be left blank.

    `max_chars` is the field's own maxlength. Writing INSIDE the budget beats trimming
    afterwards: a trimmed answer loses its last clause, which is usually the point.
    """
    if not is_llm_answerable(label):
        return None, "not a motivation question - bank or blank"

    prompt = build_prompt(label, company, role, max_chars)
    try:
        text = llm.ask(prompt, max_tokens=FREETEXT_MAX_TOKENS)  # see the constant for why 4096
    except Exception as exc:  # noqa: BLE001 - any failure means blank, never a guess
        return None, f"llm unavailable ({type(exc).__name__}); left blank"

    text = (text or "").strip().strip('"').strip()
    if not text:
        return None, "llm returned nothing; left blank"

    # An over-long answer means the model ignored the brief, which means it probably ignored
    # the grounding rule too. Refuse rather than trim: a rambling answer is where invented
    # claims hide.
    if len(text.split()) > MAX_WORDS + 20:
        return None, f"llm answer was {len(text.split())} words (cap {MAX_WORDS}); left blank"

    # ⚠️ TRUNCATION GUARD. The dangerous direction is SHORT, not long: a budget overrun returns
    # a fluent fragment that ends mid-sentence, and every check above passes it. Measured
    # 2026-08-15 at max_tokens=300. A half-sentence on an employer's form is worse than a blank
    # field, and unlike a blank one nobody notices it. Same shape as the gateway eating the
    # first token (D43): plausible, well-formed, and wrong.
    if not text.rstrip().endswith((".", "!", "?")):
        return None, f"llm answer looks truncated (no end punctuation): {text!r}; left blank"
    if len(text.split()) < 12:
        return None, f"llm answer implausibly short ({len(text.split())} words); left blank"

    if "—" in text:
        text = text.replace("—", ", ")

    # The model is asked to stay inside the budget; this is the backstop when it does not.
    # Refuse rather than hand back a fragment - _fit_to_limit in fill.py would trim it anyway,
    # and a motivation answer that loses its final clause has lost its point.
    if max_chars and len(text) > max_chars:
        window = text[:max_chars]
        cut = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
        if cut < max(40, max_chars // 3):
            return None, f"llm wrote {len(text)} chars against a {max_chars} cap; left blank"
        text = window[: cut + 1].strip()
    return text, "llm-generated, grounded prompt"


__all__ = ["answer", "is_llm_answerable", "build_prompt", "FACTUAL", "MOTIVATION"]
