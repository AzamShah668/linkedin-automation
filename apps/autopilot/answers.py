"""The answer bank and the FIELD_MAP — the only legal source of form values.

THE ONE HARD RULE (docs/knowledge/17-auto-apply-runbook.md):
    Only values from profile/application-answers.json go into a real employer's form.
    A null means LEAVE IT BLANK. Blank beats wrong. Skip beats invent.

Exactly one derivation is permitted, because it is a fact and not a guess:
    how_did_you_hear_about_us -> "LinkedIn"   (every role on this board came from LinkedIn)

Two answers are country-conditional. That is not inference — the bank itself instructs it
("Decide from the employer's country; if unclear, use the India figure"), and both branches
are stored facts:
    expected CTC       India 840000 INR   /  international 30000 USD
    visa sponsorship   India "No"         /  international "Yes"

first_name / last_name were unmapped until 2026-08-06, on the theory that LinkedIn pre-fills
them. It does not — they came back blank and REQUIRED on a real form. They are now explicit
bank keys (owner-supplied), not a split of full_name in code.

CONSENTS are a separate category from facts, deliberately. See CONSENT_NOTE below.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]
BANK_PATH = REPO / "profile" / "application-answers.json"

# Fields whose correct value depends on the employer's country.
INDIA_DEFAULT = True  # runbook: if the country is genuinely unclear, use the India figure.

TEXT = "text"
NUMERIC = "numeric"
CHOICE = "choice"
DATE = "date"
CONSENT = "consent"

CONSENT_NOTE = """
A consent checkbox is NOT a fact about Azam, so the "never invent a value" rule does not decide
it. That rule exists to stop FALSE STATEMENTS — a guessed salary or notice period is a lie sent
under his name. Ticking "this company may process my data" states nothing false.

It is an act of agreement, so the question is authority, not truth: has the owner authorised it?
He has, twice over — he authorised the application itself, and consenting to process the CV you
are in the act of sending them is instrumental to that. Withholding it while submitting the
application is incoherent: the data is going to them either way.

The risk is also lopsided. Not ticking it blocks a required field and the application silently
dies (recoverable, but that is the failure we are here to fix). Ticking it means a company he
chose to apply to may process the CV he chose to send. That is the transaction.

SCOPE IS DELIBERATELY NARROW. Only data-processing / privacy-policy consent tied to THIS
application is mapped. Anything that binds him beyond it — marketing opt-ins, background-check
authorisations, agency representation, terms of engagement, "I agree to be contacted by
partners" — is NOT mapped and lands in the unanswered report for a human. If a pattern here
ever starts matching one of those, narrow the pattern; do not widen the value.
"""


class BankMissing(RuntimeError):
    pass


def load_bank(path: Path = BANK_PATH) -> dict:
    if not path.exists():
        raise BankMissing(
            f"answer bank not found at {path}. Copy profile/application-answers.example.json "
            f"to profile/application-answers.json and fill it in."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def lookup(bank: dict, dotted: str) -> str | None:
    """Read a dotted path out of the bank. Returns None for missing OR null — both mean blank."""
    node: object = bank
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if node is None:
        return None
    text = str(node).strip()
    return text or None


@dataclass(frozen=True)
class Spec:
    """One mappable question.

    patterns  regexes matched (case-insensitive) against the field's visible label
    text      bank path used for free-text / dropdown controls
    numeric   bank path used for numeric controls — the word form fails validation there
    kind      hint for how to fill
    note      shown in the FIELD_MAP dump; explains any non-obvious choice
    """

    patterns: tuple[str, ...]
    text: str | Callable[[bool], str | None] | None = None
    numeric: str | Callable[[bool], str | None] | None = None
    kind: str = TEXT
    note: str = ""


def _expected_ctc(india: bool) -> str:
    return (
        "compensation.expected_ctc_india_annual_inr"
        if india
        else "compensation.expected_ctc_international_usd_year"
    )


def _sponsorship(india: bool) -> str:
    # Indian citizen: needs no sponsorship to work in India, does need it elsewhere.
    return "eligibility._answer_no" if india else "eligibility.requires_visa_sponsorship_outside_india"


# ---------------------------------------------------------------------------------------
# FIELD_MAP — insertion order IS match priority. Specific questions must precede generic
# ones: "years with Kubernetes" has to win before the bare "years of experience" catch-all,
# and "expected CTC" before any generic salary pattern.
# ---------------------------------------------------------------------------------------
FIELD_MAP: dict[str, Spec] = {
    # --- contact step -------------------------------------------------------------------
    "email": Spec(
        (r"\bemail\b",), text="identity.email", kind=CHOICE,
        note="usually a select of verified addresses; prefilled value kept if no option matches",
    ),
    "phone_country_code": Spec(
        (r"phone country code", r"country code"), text="identity.phone_country_code", kind=CHOICE,
        note="matched on '+91'",
    ),
    "phone": Spec(
        (r"mobile phone number", r"phone number", r"\bphone\b", r"\bmobile\b"),
        text="identity.phone", numeric="identity.phone",
    ),
    "first_name": Spec((r"first name", r"given name"), text="identity.first_name",
                       note="proven REQUIRED and blank on a real form 2026-08-06; owner-supplied bank key"),
    "last_name": Spec((r"last name", r"surname", r"family name"), text="identity.last_name"),
    "linkedin_url": Spec((r"linkedin (profile|url)", r"linkedin\.com"), text="identity.linkedin"),
    "github_url": Spec((r"\bgithub\b", r"portfolio (url|link)"), text="identity.github"),
    "website": Spec((r"^website", r"personal website", r"\bportfolio\b"), text="identity.github",
                    note="owner: the GitHub URL is the right value for a 'Website' field"),
    "city": Spec((r"^city", r"current (city|location)", r"\blocation\b"), text="identity.location_city"),

    # --- skill-specific experience (MUST precede the generic years catch-all) ------------
    "years_python": Spec((r"python",), numeric="NEEDS_AZAM.years_with_python", text="NEEDS_AZAM.years_with_python", kind=NUMERIC),
    "years_docker": Spec((r"docker",), numeric="NEEDS_AZAM.years_with_docker", text="NEEDS_AZAM.years_with_docker", kind=NUMERIC),
    "years_kubernetes": Spec((r"kubernetes", r"\bk8s\b"), numeric="NEEDS_AZAM.years_with_kubernetes", text="NEEDS_AZAM.years_with_kubernetes", kind=NUMERIC),
    "years_aws": Spec((r"\baws\b", r"amazon web services"), numeric="NEEDS_AZAM.years_with_aws", text="NEEDS_AZAM.years_with_aws", kind=NUMERIC),
    "years_linux": Spec((r"linux",), numeric="NEEDS_AZAM.years_with_linux", text="NEEDS_AZAM.years_with_linux", kind=NUMERIC),
    "years_mlops": Spec((r"mlops", r"machine learning ops"), numeric="NEEDS_AZAM.years_mlops", text="NEEDS_AZAM.years_mlops", kind=NUMERIC),
    "years_speech": Spec((r"speech recognition", r"\basr\b"), numeric="NEEDS_AZAM.years_speech_recognition", text="NEEDS_AZAM.years_speech_recognition", kind=NUMERIC),
    "years_production_dev": Spec((r"production (software )?development",), numeric="NEEDS_AZAM.years_production_development", text="NEEDS_AZAM.years_production_development", kind=NUMERIC),
    "years_total": Spec(
        (r"years of (work )?experience", r"total experience", r"^experience \(years\)"),
        numeric="experience.total_professional_years", text="experience.total_professional_years",
        kind=NUMERIC, note="catch-all — fresher, 0. Must stay AFTER every skill-specific pattern.",
    ),

    # --- money / availability: the two traps paid for on 2026-07-29 ----------------------
    "expected_ctc": Spec(
        (r"expected (ctc|salary|compensation|remuneration)", r"salary expectation", r"desired salary"),
        text=_expected_ctc, numeric=_expected_ctc, kind=NUMERIC,
        note="India 840000 INR / intl 30000 USD. NEVER '8.4' — client-side validation blocks Next.",
    ),
    "current_ctc": Spec(
        (r"current (ctc|salary|compensation)",),
        text="compensation.current_ctc", numeric="compensation.current_ctc", kind=NUMERIC,
        note="0 — fresher, no salaried employment",
    ),
    "notice_period": Spec(
        (r"notice period", r"how soon can you (join|start)", r"earliest (start|joining)", r"when can you (join|start)"),
        text="availability.notice_period", numeric="availability.notice_period_days", kind=NUMERIC,
        note="numeric control -> '0'. NEVER 'Immediate' — proven to fail validation.",
    ),
    "relocate": Spec((r"relocat",), text="availability.willing_to_relocate", kind=CHOICE),
    "onsite_ok": Spec(
        (r"comfortable (commuting|working) (to|from|in)", r"work from (the )?office", r"\bhybrid\b", r"\bon-?site\b"),
        text="availability._answer_yes", kind=CHOICE,
        note="bank: 'Remote, hybrid or on-site - all acceptable' -> Yes",
    ),

    # --- eligibility ---------------------------------------------------------------------
    "sponsorship": Spec(
        (r"sponsor", r"visa status", r"require.*visa"),
        text=_sponsorship, kind=CHOICE,
        note="country-conditional: India -> No, international -> Yes. Wrong answer = auto-reject.",
    ),
    "work_auth": Spec(
        (r"authoriz(ed|ation) to work", r"legally (authorized|entitled) to work", r"right to work"),
        text="eligibility._answer_yes", kind=CHOICE,
        note="bank: Indian citizen, authorised to work in India",
    ),
    "nationality": Spec((r"nationality", r"citizenship"), text="eligibility.nationality"),

    # --- personal / education ------------------------------------------------------------
    "date_of_birth": Spec((r"date of birth", r"\bdob\b"), text="NEEDS_AZAM.date_of_birth", kind=DATE),
    "gender": Spec((r"\bgender\b",), text="NEEDS_AZAM.gender", kind=CHOICE),
    "degree": Spec(
        (r"highest (degree|qualification|education)", r"education level", r"\bdegree\b"),
        text="education.degree", kind=CHOICE,
    ),
    "graduation_year": Spec(
        (r"(year of )?graduation", r"passing (out )?year", r"completion year"),
        text="education.end_year", numeric="education.end_year", kind=NUMERIC,
    ),
    "institution": Spec((r"university", r"college", r"institution", r"school name"), text="education.institution"),

    # --- consent: an act of agreement, not a fact. Read CONSENT_NOTE before touching. -------
    "consent_data_processing": Spec(
        (r"consent to collect", r"consent to (the )?(process|stor)", r"may (collect|process|store) .*(my|your) data",
         r"agree to the processing of", r"agree to (the )?privacy (policy|notice)"),
        text="consents.data_processing", kind=CONSENT,
        note="ONLY data-processing consent for THIS application. Marketing/background-check/"
             "agency-representation consents are deliberately NOT mapped — they go to a human.",
    ),

    # --- the single permitted derivation ---------------------------------------------------
    "how_heard": Spec(
        (r"how did you (hear|find|learn) about", r"source of application", r"referral source"),
        text="_derived.linkedin", kind=CHOICE,
        note="THE ONE PERMITTED DERIVATION -> 'LinkedIn'. Every board row came from LinkedIn.",
    ),

    # --- known-null: mapped so they report by name instead of as 'unrecognised' -------------
    "current_employer": Spec((r"current (employer|company|organi[sz]ation)",), text="NEEDS_AZAM.current_employer",
                             note="null in bank -> leave blank, report"),
    "cgpa": Spec((r"\bcgpa\b", r"percentage", r"\bmarks\b", r"\bgpa\b", r"aggregate"),
                 text="NEEDS_AZAM.highest_qualification_percentage_or_cgpa", kind=NUMERIC,
                 note="null in bank -> leave blank, report"),
    "passport": Spec((r"passport",), text="NEEDS_AZAM.passport_number", note="null in bank -> leave blank, report"),
    "reason_for_change": Spec((r"reason for (change|leaving)", r"why (are you )?looking"),
                              text="NEEDS_AZAM.reason_for_change", note="null in bank -> leave blank, report"),
}

# Synthetic bank paths for values the bank states in prose rather than as a bare token.
SYNTHETIC: dict[str, str] = {
    "_derived.linkedin": "LinkedIn",
    "availability._answer_yes": "Yes",
    "eligibility._answer_yes": "Yes",
    "eligibility._answer_no": "No",
}

_COMPILED: dict[str, tuple[re.Pattern[str], ...]] = {
    key: tuple(re.compile(p, re.IGNORECASE) for p in spec.patterns)
    for key, spec in FIELD_MAP.items()
}


def match_field(label: str) -> tuple[str, Spec] | None:
    """First FIELD_MAP entry whose pattern appears in the label wins. Order = priority."""
    if not label:
        return None
    for key, patterns in _COMPILED.items():
        if any(p.search(label) for p in patterns):
            return key, FIELD_MAP[key]
    return None


def resolve(bank: dict, spec: Spec, *, numeric_control: bool, india: bool = INDIA_DEFAULT) -> str | None:
    """Turn a Spec into the literal string to type, or None meaning LEAVE BLANK.

    A numeric control takes the numeric path when one exists — that is the whole of the
    2026-07-29 lesson ('Immediate' -> '0', '8.4' -> '840000').
    """
    source = spec.numeric if (numeric_control and spec.numeric is not None) else spec.text
    if source is None:
        return None
    path = source(india) if callable(source) else source
    if path is None:
        return None
    if path in SYNTHETIC:
        return SYNTHETIC[path]
    return lookup(bank, path)


def dump_field_map(bank: dict | None = None, india: bool = INDIA_DEFAULT) -> str:
    """Human-readable FIELD_MAP for review before any run touches a real posting."""
    bank = bank if bank is not None else load_bank()
    lines = [
        f"FIELD_MAP — {len(FIELD_MAP)} mapped questions, matched in this order",
        f"country assumption: {'India' if india else 'international'}",
        "",
        f"{'#':>3}  {'key':<22} {'kind':<8} {'text value':<26} {'numeric value':<14} label patterns",
        "-" * 132,
    ]
    for i, (key, spec) in enumerate(FIELD_MAP.items(), 1):
        text_val = resolve(bank, spec, numeric_control=False, india=india)
        num_val = resolve(bank, spec, numeric_control=True, india=india)
        shown_text = "(blank — null in bank)" if text_val is None else text_val
        shown_num = "-" if num_val == text_val or num_val is None else num_val
        lines.append(
            f"{i:>3}  {key:<22} {spec.kind:<8} {shown_text[:26]:<26} {str(shown_num)[:14]:<14} "
            f"{' | '.join(spec.patterns)}"
        )
        if spec.note:
            lines.append(f"{'':>3}  {'':<22} note: {spec.note}")
    return "\n".join(lines)
