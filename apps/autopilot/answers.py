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
    requires: str | None = None  # extra regex the label MUST also match, or it is not this field


# A skill name in a label does not make it a quantity question. Proven 2026-08-06: "Do you have
# hands-on experience with MLOps and cloud platforms ... Docker/Kubernetes ...?" is a Yes/No
# radio, and it matched `years_docker`, which tried to answer "2". It failed safe only because
# no radio option reads "2" — in a TEXT input it would have typed a nonsense answer into a real
# employer's form. Every years_* spec must also carry a quantity cue.
QUANTITY_CUE = r"how many|how much|how long|\byears?\b|\bmonths?\b|\bduration\b"


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
    "middle_name": Spec((r"middle name",), text="identity.middle_name"),
    "linkedin_url": Spec((r"linkedin (profile|url)", r"linkedin\.com"), text="identity.linkedin"),
    "github_url": Spec((r"\bgithub\b", r"portfolio (url|link)"), text="identity.github"),
    "website": Spec((r"^website", r"personal website", r"\bportfolio\b"), text="identity.github",
                    note="owner: the GitHub URL is the right value for a 'Website' field"),
    # ⚠️ 2026-08-09: this pattern used to include a bare `\blocation\b`, which matched
    # "Have you ever appeared for an Interview at any Exl LOCATION during the last 90 days?"
    # and typed "Srinagar" into it. That is a FALSE STATEMENT on a real employer's form - the
    # precise harm the answer-bank rule exists to prevent, caused by an over-broad pattern
    # rather than by a guess. A pattern that can match a question about something else is as
    # dangerous as inventing a value.
    # Every pattern here must be anchored to the CANDIDATE'S OWN location.
    "city": Spec(
        (r"^city\b", r"^location\b", r"your (current )?location", r"current (city|location)",
         r"city of residence", r"where are you (currently )?(located|based)"),
        text="identity.location_city",
        note="anchored to the candidate's own city; a bare 'location' match caused a wrong answer",
    ),
    # "Are you currently located in <city>?" is answerable from the bank and it is a FACT, not a
    # guess: the bank states the city he lives in. Answered by comparing, never assumed - see
    # located_in_answer() and the resolver in fill.py. Truthful "No" is required even when it
    # may cost the application; willingness to relocate is a separate question the bank answers Yes.
    "located_in_city": Spec(
        (r"currently (located|based|residing) in", r"are you (located|based) in",
         r"do you (currently )?(live|reside) in"),
        text="_dynamic.located_in", kind=CHOICE,
        note="compares the city named in the question against identity.location_city",
    ),

    # --- skill-specific experience (MUST precede the generic years catch-all) ------------
    "years_python": Spec((r"python",), numeric="NEEDS_AZAM.years_with_python", text="NEEDS_AZAM.years_with_python", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_docker": Spec((r"docker",), numeric="NEEDS_AZAM.years_with_docker", text="NEEDS_AZAM.years_with_docker", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_kubernetes": Spec((r"kubernetes", r"\bk8s\b"), numeric="NEEDS_AZAM.years_with_kubernetes", text="NEEDS_AZAM.years_with_kubernetes", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_aws": Spec((r"\baws\b", r"amazon web services"), numeric="NEEDS_AZAM.years_with_aws", text="NEEDS_AZAM.years_with_aws", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_linux": Spec((r"linux",), numeric="NEEDS_AZAM.years_with_linux", text="NEEDS_AZAM.years_with_linux", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_mlops": Spec((r"mlops", r"machine learning ops"), numeric="NEEDS_AZAM.years_mlops", text="NEEDS_AZAM.years_mlops", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_speech": Spec((r"speech recognition", r"\basr\b"), numeric="NEEDS_AZAM.years_speech_recognition", text="NEEDS_AZAM.years_speech_recognition", kind=NUMERIC, requires=QUANTITY_CUE),
    "years_production_dev": Spec((r"production (software )?development",), numeric="NEEDS_AZAM.years_production_development", text="NEEDS_AZAM.years_production_development", kind=NUMERIC, requires=QUANTITY_CUE),
    # Catch-all for "how many years with <ANY technology>". MUST come after the named
    # years_* specs (they carry richer notes) and BEFORE years_total, or the generic
    # "years of experience" answer would be given for a specific technology question -
    # the same digit, a completely different claim.
    "years_technology": Spec(
        (r"years of (work |professional |hands.?on )?experience (do you have )?(with|in|using) ",
         r"years of (work |professional |hands.?on )*[A-Za-z0-9+#./ -]{2,40} experience"),
        text="_dynamic.tech_years", numeric="_dynamic.tech_years", kind=NUMERIC,
        requires=QUANTITY_CUE,
        note="resolved per-technology from experience.technology_years; unknown tech -> 0",
    ),
    "years_total": Spec(
        (r"years of (work|professional)? ?experience", r"total experience",
         r"^experience \(years\)"),
        numeric="experience.total_professional_years", text="experience.total_professional_years",
        kind=NUMERIC, note="catch-all — fresher, 0. Must stay AFTER every skill-specific pattern.",
    ),

    # --- money / availability: the two traps paid for on 2026-07-29 ----------------------
    "expected_ctc": Spec(
        (r"expected (ctc|salary|compensation|remuneration)", r"salary expectation",
         r"desired salary", r"expected .{0,25}(compensation|ctc|package)"),
        text=_expected_ctc, numeric=_expected_ctc, kind=NUMERIC,
        note="India 840000 INR / intl 30000 USD. NEVER '8.4' — client-side validation blocks Next.",
    ),
    "current_ctc": Spec(
        (r"current (ctc|salary|compensation)", r"current .{0,25}(compensation|ctc|package)",
         r"current pay\b", r"current .{0,10}(monthly|annual) (pay|income)"),
        text="compensation.current_ctc", numeric="compensation.current_ctc", kind=NUMERIC,
        note="0 — fresher, no salaried employment. Covers 'current pay in INR per month'.",
    ),
    # MUST precede `notice_period`. "Do you HAVE TO SERVE a notice period?" is a Yes/No
    # question, not a duration - matching it to the duration spec tried to answer "0" and the
    # radio had no such option, so the field stayed blank and the form could not submit
    # (2026-08-10). He is a fresher with no employer, so there is no notice to serve.
    "must_serve_notice": Spec(
        # ⚠️ "are you serving" is NOT enough: a real form asked "Are you CURRENTLY serving
        # notice period?" and the adverb between "you" and "serving" broke the match. Allow
        # a word in between. Also tolerate the "servibg" typo seen on another live form.
        (r"(have|need) to serve.{0,20}notice", r"are you (\w+ )?serv[a-z]{0,3}g.{0,20}notice",
         r"do you have a notice period\b", r"serving .{0,12}notice currently"),
        text="availability._answer_no", kind=CHOICE,
        note="Yes/No form of the notice question: no current employer, so nothing to serve",
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
    # Owner-supplied 2026-08-09. NOTE the ordering: this must precede the `passport` spec below,
    # which covers a request for the passport NUMBER and is still null. "Do you have a passport"
    # and "what is your passport number" are different questions with different answers.
    "has_passport": Spec(
        (r"(have|hold).{0,20}valid.{0,20}passport", r"do you (have|hold) a.{0,15}passport",
         r"passport\s*\?"),
        text="eligibility.has_valid_indian_passport", kind=CHOICE,
        note="the YES/NO question only; the passport NUMBER stays blank",
    ),
    "night_shifts": Spec(
        (r"willing to work in shifts", r"night shift", r"rotational shift", r"shift work"),
        text="availability.willing_to_work_shifts_including_nights", kind=CHOICE,
    ),
    "worked_here_before": Spec(
        # The span is generous because real questions name the legal entity in full:
        # "Have you Worked with exlservice.com (I) Pvt. Ltd. Or any Associate / Subsidiary
        # Company ever before" is ~72 characters between "with" and "before".
        (r"(worked|employed)\s+(with|at|for).{0,120}?\bbefore\b",
         r"ever (worked|been employed)\s+(with|at|for)",
         r"are you a (former|ex).?employee",
         r"previously (worked|employed)"),
        text="eligibility.previously_employed_at_this_company", kind=CHOICE,
        note="No everywhere: total_professional_years is 0, so he has never been employed anywhere",
    ),

    # --- personal / education ------------------------------------------------------------
    "date_of_birth": Spec((r"date of birth", r"\bdob\b"), text="NEEDS_AZAM.date_of_birth", kind=DATE),
    "gender": Spec((r"\bgender\b",), text="NEEDS_AZAM.gender", kind=CHOICE),
    "degree": Spec(
        # ⚠️ NO bare `\bdegree\b`. It matched "Have you completed the following level of
        # education: Master's Degree?" and would have answered "B.Tech" - a text answer to a
        # Yes/No question, about the wrong level. The education_* specs handle completion.
        (r"highest (completed )?(degree|qualification|education)", r"education level",
         r"(what|which) .{0,20}degree", r"your degree\b",
         r"specify your .{0,25}degree", r"degree \(e\.g"),
        text="education.degree", kind=CHOICE,
        note="the degree NAME only; 'have you completed <level>' is education_bachelors et al",
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

    # --- identity gaps the survey exposed 2026-08-15 ---------------------------------------
    "full_name": Spec(
        (r"full name", r"^name$", r"your name\b"), text="identity.full_name",
        note="'Please enter your full name.' was REQUIRED and unmapped; first/last existed, full did not",
    ),
    "country": Spec(
        (r"^country\b", r"country of residence", r"which country"), text="identity.country",
        kind=CHOICE,
        note="India. Anchored with ^ so it cannot eat 'country code' (that spec precedes it anyway)",
    ),

    # --- technology-specific years. MUST stay narrow and MUST precede nothing generic. -----
    # A truthful 0 here loses a role he would fail in the technical round. Do not round up, and
    # do not let years_total answer these: 0 for "professional experience" is a different claim
    # from 0 for "Databricks", even though the digit is the same.

    # --- freelance / contract logistics ----------------------------------------------------
    "remote_support": Spec(
        (r"remote support",), text="logistics.remote_support_ok", kind=CHOICE, note="Yes",
    ),
    "hourly_rate_ok": Spec(
        (r"hourly compensation of", r"comfortable with .{0,15}\$\d+", r"hourly rate of"),
        text="logistics.hourly_rate_8_usd_ok", kind=CHOICE,
        note="Yes at $8/hr, owner-confirmed 2026-08-15. ⚠️ The value is a blanket yes and the "
             "pattern matches ANY figure - revisit if a form offers materially less.",
    ),
    "last_working_day": Spec(
        (r"last working (date|day)", r"official last working"),
        text="logistics.last_working_day",
        note="'N/A - not serving notice'. Non-empty on purpose: these are REQUIRED text inputs "
             "that block submission, and blank would stall the form.",
    ),

    # --- prose reused across employers -----------------------------------------------------
    "small_and_large_scale": Spec(
        (r"small.?scale and large.?scale", r"both small.{0,15}and large"),
        text="narrative.small_and_large_scale",
    ),
    "primary_technologies": Spec(
        (r"primary technologies", r"list the .{0,20}technologies"),
        text="narrative.primary_technologies",
    ),
    "certifications_list": Spec(
        (r"certifications? or training", r"relevant certifications?", r"training programs?"),
        text="narrative.certifications",
        note="Truthful 'no formal certifications, but ...'. NEVER name one he does not hold: it "
             "is checkable and it ends an interview badly.",
    ),

    # --- education completion. LinkedIn phrases this as "Have you completed the following
    # level of education: <DEGREE>?" and it is REQUIRED, so an unmapped degree stalls the
    # wizard. Order matters: doctorate and master must be tested BEFORE bachelor, or a
    # question about a Master's would match a generic degree pattern and answer Yes.
    "education_doctorate": Spec(
        (r"(doctorate|\bphd\b|doctoral)",), text="education.completed_doctorate", kind=CHOICE,
        note="No",
    ),
    "education_masters": Spec(
        (r"master'?s? degree", r"\bmasters\b", r"post.?graduate"),
        text="education.completed_masters", kind=CHOICE, note="No",
    ),
    "education_bachelors": Spec(
        (r"bachelor'?s? degree", r"\bbachelors\b", r"under.?graduate degree",
         r"completed the following level of education"),
        text="education.completed_bachelors", kind=CHOICE,
        note="Yes - B.Tech CSE 2022-2026, complete as of 2026-08. The last pattern is the "
             "catch-all for LinkedIn's phrasing and MUST stay after doctorate/masters.",
    ),

    # --- capability Yes/No, owner-confirmed 2026-08-15 from the 44-form survey -------------
    # These sit AFTER every years_* spec on purpose. A years_* spec also carries QUANTITY_CUE,
    # so a bare "do you have experience with Kubernetes" cannot reach it - but relying on one
    # guard for a value that goes on a real employer's form is how D31 happened. Order is the
    # second guard.
    #
    # Every pattern is anchored to ITS OWN subject. There is deliberately NO generic
    # "do you have experience with (.*)" rule: that would answer Yes about technologies he has
    # never touched, which is the same class of harm as inventing a value outright.
    "cap_mlops_lifecycle": Spec(
        (r"mlops lifecycle", r"(complete|full|end.to.end) mlops", r"owning the .{0,20}mlops"),
        text="capabilities.mlops_lifecycle_production", kind=CHOICE,
        note="Yes - owner-confirmed; distinct from years_mlops, which needs a quantity cue",
    ),
    "cap_k8s_docker_cicd": Spec(
        (r"kubernetes,? (and )?docker", r"docker,? (and )?kubernetes",
         r"(kubernetes|docker).{0,40}ci/?cd", r"ci/?cd.{0,40}(kubernetes|docker)"),
        text="capabilities.kubernetes_docker_cicd", kind=CHOICE,
        note="Yes - the core of his two years; only fires when 2+ of the three are named together",
    ),
    "cap_onprem_gpu_llm": Spec(
        (r"on.?prem(ise)? gpu", r"gpu infrastructure.{0,40}(llm|generative)",
         r"(llm|generative ai) deployment.{0,30}on.?prem"),
        text="capabilities.onprem_gpu_llm_deployment", kind=CHOICE,
        note="Yes - the 2-node K3s + RTX 3090 cluster",
    ),
    "cap_ai_agents": Spec(
        (r"build(ing)? ai.?agents", r"ai.?agents using llm", r"agentic (ai )?systems? (using|with)"),
        text="capabilities.ai_agents_with_llm", kind=CHOICE,
        note="Yes - multi-agent orchestrators, this project included",
    ),
    # The two NOs. Worth as much as the yeses: they stop an overstatement he would have to
    # defend in an interview, and they were explicitly confirmed rather than assumed.
    "cap_k8s_security": Spec(
        (r"hardening kubernetes", r"kubernetes .{0,20}hardening", r"embedding security.{0,30}(k8s|kubernetes)"),
        text="capabilities.kubernetes_hardening_security", kind=CHOICE,
        note="No - owner-confirmed 2026-08-15",
    ),
    "cap_computer_vision": Spec(
        (r"computer vision", r"real.?time ml inference"),
        text="capabilities.computer_vision_realtime_inference", kind=CHOICE,
        note="No - owner-confirmed 2026-08-15",
    ),
    "cap_oci_cert": Spec(
        (r"oracle cloud infrastructure.{0,30}certif", r"\boci\b.{0,30}certif"),
        text="capabilities.oci_certification", kind=CHOICE, note="No - owner-confirmed",
    ),
    "cap_individual_contributor": Spec(
        (r"individual contributor",), text="capabilities.individual_contributor", kind=CHOICE,
        note="Yes - owner-confirmed",
    ),
    "cap_managed_teams": Spec(
        (r"managed teams", r"have you (ever )?(managed|led) a team", r"team size and structure"),
        text="capabilities.managed_teams", kind=CHOICE, note="No - owner-confirmed",
    ),

    # --- logistics, owner-confirmed 2026-08-15 ---------------------------------------------
    "start_immediately": Spec(
        (r"start immediately", r"join immediately", r"immediate joiner", r"can you start immediate"),
        text="logistics.can_start_immediately", kind=CHOICE,
        note="Yes - notice period is Immediate",
    ),
    "f2f_interview": Spec(
        (r"f2f interview", r"face.to.face interview", r"in.?person interview"),
        text="logistics.f2f_interview_available", kind=CHOICE, note="Yes - owner-confirmed",
    ),
    # ⚠️ NOT the same question as an F2F interview. A walk-in drive is a no-appointment hiring
    # event in a named city on a named day; he is in Srinagar and declined both (Chennai ~3000km,
    # Kolkata ~1800km) on 2026-08-15. Answering these Yes commits him to a flight.
    "walkin_drive": Spec(
        (r"walk.?in drive", r"walk.?in\b.{0,30}(on|at)\b", r"available for walk.?in"),
        text="logistics.attend_walkin_drive_other_city", kind=CHOICE,
        note="No - travel from Srinagar; deliberately separate from f2f_interview",
    ),
    "contract_6_month": Spec(
        (r"6.?month .{0,15}contract", r"six.?month .{0,15}contract"),
        text="logistics.six_month_contract_ok", kind=CHOICE, note="Yes - owner-confirmed",
    ),
    "travel_client_site": Spec(
        (r"travel to .{0,25}client site", r"occasional travel"),
        text="logistics.travel_to_client_site", kind=CHOICE, note="Yes - owner-confirmed",
    ),
    "communication_rating": Spec(
        (r"rate your communication", r"communication and stakeholder"),
        text="logistics.communication_rating_1_5", numeric="logistics.communication_rating_1_5",
        kind=NUMERIC, note="4 of 5 - owner-confirmed",
    ),
    "postal_code": Spec(
        (r"postal code", r"\bpin ?code\b", r"\bzip code\b"),
        text="identity.postal_code", numeric="identity.postal_code",
        note="190020 - owner-supplied 2026-08-15",
    ),

    # --- known-null: mapped so they report by name instead of as 'unrecognised' -------------
    "offer_in_hand": Spec(
        (r"offer in hand", r"any offers? (in hand|currently)", r"do you have .{0,15}offer"),
        text="NEEDS_AZAM.offer_in_hand", kind=CHOICE,
        note="NULL ON PURPOSE. He answered '80000' to a Yes/No; the bank says fresher, "
             "current_ctc 0. Recording an offer would be a fabricated fact. Blank until resolved.",
    ),
    "certifications": Spec(
        (r"certification", r"training programs?"),
        text="NEEDS_AZAM.certifications",
        note="NULL ON PURPOSE. Answered 'yes' with no list; none found in profile/ or the CV, "
             "which says explicitly 'not public-cloud certifications - frame honestly'.",
    ),
    "current_employer": Spec((r"current (employer|company|organi[sz]ation)",), text="NEEDS_AZAM.current_employer",
                             note="null in bank -> leave blank, report"),
    "cgpa": Spec((r"\bcgpa\b", r"percentage", r"\bmarks\b", r"\bgpa\b", r"aggregate"),
                 text="NEEDS_AZAM.highest_qualification_percentage_or_cgpa", kind=NUMERIC,
                 note="null in bank -> leave blank, report"),
    "passport": Spec((r"passport",), text="NEEDS_AZAM.passport_number", note="null in bank -> leave blank, report"),
    # No longer null: owner delegated the wording on 2026-08-15 ("find anything inspiring
    # yourself"), so it is written from his real record and stored in narrative.
    # ⚠️ "Why do you want to join OUR company" is NOT routed here. That answer is different for
    # every employer, and a banked generic would be the templated filler this project exists to
    # avoid. It stays unanswered and gets reported.
    "reason_for_change": Spec(
        (r"reason for (change|leaving)", r"why (are you )?looking",
         r"reason for seeking", r"primary reason .{0,20}(new )?opportunity"),
        text="narrative.reason_for_change",
        note="owner-delegated wording, grounded in his own record",
    ),
}

# Synthetic bank paths for values the bank states in prose rather than as a bare token.
SYNTHETIC: dict[str, str] = {
    "_derived.linkedin": "LinkedIn",
    "availability._answer_yes": "Yes",
    "availability._answer_no": "No",
    "eligibility._answer_yes": "Yes",
    "eligibility._answer_no": "No",
}

_COMPILED: dict[str, tuple[re.Pattern[str], ...]] = {
    key: tuple(re.compile(p, re.IGNORECASE) for p in spec.patterns)
    for key, spec in FIELD_MAP.items()
}


def located_in_answer(bank: dict, label: str) -> str | None:
    """Answer 'Are you currently located in <city>?' by COMPARING, never by assuming.

    The bank states where he lives. If the question names that place (or his state, or country
    for a country-level question), the truthful answer is Yes; otherwise No. This is a
    comparison against a recorded fact, not an inference about something unknown.

    Returns None when the question does not name a place we hold, so it goes to a human.
    """
    home = {
        _norm_place(lookup(bank, "identity.location_city")),
        _norm_place(lookup(bank, "identity.location_state")),
        _norm_place(lookup(bank, "identity.location_country")),
    }
    home.discard("")
    if not home:
        return None

    text = _norm_place(label)
    if any(place and place in text for place in home):
        return "Yes"
    # Only answer No when the question actually names somewhere — otherwise we know nothing.
    return "No" if re.search(r"\b(in|at)\s+[A-Z]", label) else None


# "How many years of work experience do you have with <X>?" is LinkedIn's standard screener and
# X is unbounded. The bank knew 8 technologies; everything else came back blank, and these
# fields are REQUIRED, so ONE unmapped technology stalls the whole wizard. Measured 2026-08-15
# on MyRemoteTeam: Python was known, LangChain and Generative AI were not, and the application
# died on page 3 of 4 with "Invalid input".
TECH_QUESTION = re.compile(
    r"years of (?:work |professional |hands.?on )?experience (?:do you have )?"
    r"(?:with|in|using) (?P<tech>.+?)\s*[?*.]*\s*$",
    re.I,
)
# The other word order, seen on a live form: "How many years of hands-on DATABRICKS experience
# do you have in AI/ML or data engineering projects?" - the technology sits BEFORE the word
# "experience", so the pattern above never sees it.
TECH_QUESTION_PREFIX = re.compile(
    r"years of (?:work |professional |hands.?on )*(?P<tech>[A-Za-z0-9+#./ -]{2,40}?) experience",
    re.I,
)
# A technology absent from his record answers 0, never a flattering guess. 0 is TRUE for
# something he has not used, and it loses only roles he would fail in the technical round.
DEFAULT_TECH_YEARS = "0"


def _norm_tech(value: str) -> str:
    """Lower-case, strip LinkedIn's parenthetical suffixes and punctuation."""
    text = re.sub(r"\((?:programming language|software|framework|library|tool)\)", " ", value, flags=re.I)
    text = re.sub(r"[^a-z0-9+#./ -]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def tech_years_answer(bank: dict, label: str) -> str | None:
    """Years for the technology named in the question, or None if it is not that question.

    Returns a STRING because the caller writes it into a text or numeric input either way.
    """
    match = TECH_QUESTION.search(label or "") or TECH_QUESTION_PREFIX.search(label or "")
    if not match:
        return None
    tech = _norm_tech(match.group("tech"))
    if not tech:
        return None

    table = (bank.get("experience") or {}).get("technology_years") or {}
    clean = {k.lower(): str(v) for k, v in table.items() if not k.startswith("_")}

    if tech in clean:
        return clean[tech]
    # Longest known name contained in the phrase: "amazon web services (aws)" -> aws, and
    # "ci/cd pipelines" -> ci/cd. Longest-first so "google cloud" beats a bare "go".
    for name in sorted(clean, key=len, reverse=True):
        if len(name) < 3:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", tech):
            return clean[name]
    return DEFAULT_TECH_YEARS


def _norm_place(value: str | None) -> str:
    return re.sub(r"[^a-z]", "", (value or "").lower())


def match_field(label: str) -> tuple[str, Spec] | None:
    """First FIELD_MAP entry whose pattern appears in the label wins. Order = priority.

    A spec carrying `requires` must ALSO match that regex — a skill name alone is not enough
    to make a question a quantity question.
    """
    if not label:
        return None
    for key, patterns in _COMPILED.items():
        spec = FIELD_MAP[key]
        if not any(p.search(label) for p in patterns):
            continue
        if spec.requires and not re.search(spec.requires, label, re.IGNORECASE):
            continue
        return key, spec
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


def all_values(bank: dict) -> set[str]:
    """Every scalar in the bank, plus the synthetic answers, as comparable strings.

    Used by the pre-submit check to prove that nothing on the review screen came from anywhere
    but this file. Keys starting with '_' are prose notes, not answers, and are excluded.
    """
    found: set[str] = set(SYNTHETIC.values())

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if not str(key).startswith("_"):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif node is not None:
            text = str(node).strip()
            if text:
                found.add(text)

    walk(bank)
    return found


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
