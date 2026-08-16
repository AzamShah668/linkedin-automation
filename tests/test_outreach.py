"""The rules that decide who the owner is asked to connect with.

Every case below is a real card harvested from a live LinkedIn people search on 2026-08-15, and
three of them are bugs this module shipped before it had tests:

  * an EX-employee recommended as the contact, because "Past: X at Lotus Interworks" contains the
    company name and a substring test cannot tell an alumnus from an employee
  * a genuine current Team Lead DROPPED, because his headline named a different employer and only
    the "Current:" line named this one
  * mutual-connection facepile links harvested as if they were people, producing "candidates"
    named "Parvaiz Ahmad - Srinagar, SAYAR UL HASSAN & 4 other mutual connections"

None of the three errored. Each wrote a confident contact.md and posted a Slack card asking a real
person to connect with the wrong human.
"""

from __future__ import annotations

from apps.autopilot.outreach import (
    CURRENT,
    PAST,
    UNKNOWN,
    Candidate,
    approval_card,
    classify,
    company_tokens,
    contact_md,
    employment,
    evidence_line,
    mentions_company,
    parse_card,
    rank,
)

# The literal card text LinkedIn rendered for the search '"Lotus Interworks" (recruiter OR ...)'.
EX_EMPLOYEE_CARD = [
    "Er. Faiqa Bilal Rah • 2nd",
    "Senior AI Engineer | Network Operations Engineer | IMSS Engineer",
    "Srinagar, Jammu & Kashmir, India",
    "Connect",
    "Past: Network Operations Engineer at Lotus Interworks",
]
CURRENT_LEAD_CARD = [
    "SHALE FRANCIS",
    "• 3rd+",
    "Team Lead Simplia",
    "Ernakulam, Kerala, India",
    "Message",
    "Current: Team Lead at Lotus Interworks",
]
FACEPILE_CARD = ["Parvaiz Ahmad - Srinagar, SAYAR UL HASSAN & 4 other mutual connections"]
RECRUITER_CARD = [
    "Deepajothi Ramasamy",
    "HR IT RECRUITER @ ThreatXIntel | IT Sectors",
    "Chennai, Tamil Nadu, India",
]


# --- parsing -----------------------------------------------------------------------------------
def test_the_connection_degree_is_not_part_of_the_name():
    """It was sent to Slack as though it were a surname: "Er. Faiqa Bilal Rah • 2nd"."""
    assert parse_card("u", EX_EMPLOYEE_CARD).name == "Er. Faiqa Bilal Rah"


def test_current_and_past_employers_are_read_separately():
    card = parse_card("u", EX_EMPLOYEE_CARD)
    assert card.past_company == "Lotus Interworks"
    assert card.current_company == ""


def test_the_current_line_supplies_the_role_when_the_headline_names_another_employer():
    card = parse_card("u", CURRENT_LEAD_CARD)
    assert card.current_company == "Lotus Interworks"
    assert card.current_role == "Team Lead"
    assert card.headline == "Team Lead Simplia"      # a DIFFERENT company
    assert "Team Lead" in card.role_text


def test_the_degree_line_is_not_mistaken_for_a_headline():
    assert parse_card("u", CURRENT_LEAD_CARD).headline != "• 3rd+"


def test_a_facepile_link_is_junk_not_a_person():
    assert parse_card("u", FACEPILE_CARD).junk is True


# --- employment: the lead / stranger / alumnus distinction --------------------------------------
def test_a_past_employee_is_past_not_current():
    assert employment(parse_card("u", EX_EMPLOYEE_CARD), "Lotus Interworks") == PAST


def test_a_current_employee_is_current():
    assert employment(parse_card("u", CURRENT_LEAD_CARD), "Lotus Interworks") == CURRENT


def test_an_employer_named_in_the_headline_counts_as_current():
    assert employment(parse_card("u", RECRUITER_CARD), "ThreatXIntel") == CURRENT


def test_an_unrelated_person_is_unknown_not_current():
    """The first live bug: a keyword match with no stated link to the company."""
    card = parse_card("u", ["Jane Doe", "Senior AI Engineer at Somewhere Else", "Bengaluru"])
    assert employment(card, "Lotus Interworks") == UNKNOWN


def test_company_tokens_ignore_corporate_filler():
    assert company_tokens("InterGlobe Aviation Ltd") == ["interglobe", "aviation"]
    assert company_tokens("Hyper Lychee Labs") == ["hyper", "lychee"]


def test_a_company_of_only_generic_words_still_matches_on_something():
    assert company_tokens("The Tech Company")


def test_spacing_differences_still_match():
    """A slug is not a comparison key: skillscapital vs Skills Capital."""
    assert mentions_company("Recruiter at SkillsCapital", "Skills Capital")
    assert mentions_company("Recruiter at Skills Capital", "SkillsCapital")


# --- ranking -----------------------------------------------------------------------------------
def test_a_recruiter_outranks_an_engineer():
    recruiter = classify("A", "Technical Recruiter")
    engineer = classify("B", "DevOps Engineer")
    assert recruiter is not None and engineer is not None
    assert rank([engineer, recruiter])[0].name == "A"


def test_warm_beats_a_better_title_because_that_is_the_only_thing_that_ever_replied():
    """D8 as arithmetic. The single reply this project has had came from a shared-roots contact."""
    cold_recruiter = classify("Cold", "Technical Recruiter")
    warm_engineer = classify("Warm", "DevOps Engineer", warm_text="Srinagar, Jammu & Kashmir")
    assert warm_engineer is not None and cold_recruiter is not None
    assert warm_engineer.warm == "Kashmir"
    assert rank([cold_recruiter, warm_engineer])[0].name == "Warm"


def test_warmth_is_found_on_the_location_line_not_only_the_headline():
    scored = classify("X", "Talent Acquisition", warm_text="Srinagar, Jammu & Kashmir, India")
    assert scored is not None and scored.warm


def test_a_team_lead_is_worth_contacting():
    """Dropped on the live run: nothing in ROLE_KINDS matched "Team Lead"."""
    assert classify("X", "Team Lead") is not None


def test_a_jobseeker_at_the_company_is_not_a_route_in():
    assert classify("X", "DevOps Engineer | Open to work") is None


def test_an_out_of_network_profile_is_not_contactable():
    assert classify("LinkedIn Member", "Technical Recruiter") is None


def test_someone_with_no_relevant_role_is_skipped():
    assert classify("X", "Dentist") is None


# --- what reaches the owner ----------------------------------------------------------------------
def _person(**kw):
    base = dict(name="Asha R", headline="Technical Recruiter", username="asha-r",
                kind="recruiter", warm="", score=40)
    base.update(kw)
    return Candidate(**base)


def test_the_slack_card_carries_the_ref_the_approval_gate_greps_for():
    """check_approvals.py finds cards with `ref:<slug>`. No ref means the tick can never work."""
    _title, text = approval_card("Skills Capital", "SRE", _person())
    assert "ref:skills-capital" in text


def test_the_card_says_what_the_tick_will_do():
    _title, text = approval_card("Acme", "SRE", _person())
    assert "connection request" in text.lower()


def test_a_warm_contact_is_flagged_on_the_card_and_in_the_file():
    warm = _person(warm="Kashmir", score=100)
    _title, text = approval_card("Acme", "SRE", warm)
    assert "WARM" in text
    assert "WARM" in contact_md("Acme", "SRE", [warm])


def test_contact_md_records_that_nothing_was_sent():
    body = contact_md("Acme", "SRE", [_person()])
    assert "has been sent" in body
    assert "https://www.linkedin.com/in/asha-r/" in body


def test_backups_are_listed_so_a_dead_end_does_not_stall_the_company():
    body = contact_md("Acme", "SRE", [_person(), _person(name="Bo", username="bo")])
    assert "Backups" in body and "Bo" in body


# =================================================================================================
# 2026-08-16 — the fourth wrong-person send, and the one that actually reached someone.
#
# A real connection request went to Aditya Sharma for "Berribot · M365 Infrastructure SME". He is
# an IIT Delhi AI/full-stack engineer, banner-flagged Open to work, and the word "Berribot" appears
# ZERO times on his profile (verified by hand afterwards). The invite could not be recalled.
#
# Two independent defects had to line up:
#   1. CARD BLEED - `a.closest('li')` swept a neighbouring result's text into his card, so a
#      "Berribot" line belonging to somebody else satisfied employment().
#   2. NO PERSISTED EVIDENCE - contact.md recorded only "Why them: engineer", so the mistake was
#      invisible in the exact file a human would review.
#
# A three-state check is worthless if its verdict is never written down.
# =================================================================================================

ADITYA_CARD = [
    "Aditya Sharma",
    "· 3rd",
    "AI / Full-Stack Engineer | IIT Delhi'25 | Open Source Contributor (NetBox, Aden) | "
    "Building & Scaling SaaS Products | GATE CS AIR 156",
    "New Delhi, Delhi, India",
    "Connect",
]
BAYONE_CARD = [
    "Abhishek Negi",
    "Tech Recruiter | Hiring for UX, Product & Engineering Roles",
    "Bengaluru, Karnataka, India",
    "Current: Tech Recruiter at BayOne Solutions",
]
ANSR_CARD = [
    "Abarna Devi",
    "Associate Director - Talent Acquisition @ ANSR",
    "Bengaluru, Karnataka, India",
]


def test_the_berribot_card_is_not_a_berribot_employee():
    """The exact failure. Nothing on this card ties him to the company."""
    card = parse_card("adityasharmalin", ADITYA_CARD)
    assert employment(card, "Berribot") == UNKNOWN


def test_the_berribot_candidate_is_not_reviewable_so_cannot_be_contacted():
    card = parse_card("adityasharmalin", ADITYA_CARD)
    person = Candidate(name=card.name, headline=card.headline, username=card.username,
                       kind="engineer", employment=employment(card, "Berribot"),
                       evidence=evidence_line(card, "Berribot"))
    assert person.evidence == ""
    assert person.reviewable is False


def test_a_current_employee_named_only_on_the_current_line_is_reviewable():
    """BayOne: the headline never names the company, the Current: line does."""
    card = parse_card("abhisheknegiiii", BAYONE_CARD)
    assert employment(card, "BayOne Solutions") == CURRENT
    assert "BayOne Solutions" in evidence_line(card, "BayOne Solutions")


def test_a_current_employee_named_in_the_headline_is_reviewable():
    card = parse_card("abarna", ANSR_CARD)
    assert employment(card, "ANSR") == CURRENT
    assert evidence_line(card, "ANSR").startswith("headline:")


def test_evidence_is_empty_when_there_is_none():
    card = parse_card("x", ["Jane Doe", "Engineer at Somewhere Else", "Pune"])
    assert evidence_line(card, "Berribot") == ""


def test_a_former_employee_evidence_says_so_out_loud():
    card = parse_card("u", EX_EMPLOYEE_CARD)
    assert "FORMER" in evidence_line(card, "Lotus Interworks")


def test_reviewable_requires_both_current_and_evidence():
    """Either half missing must block the send. The verdict alone is not enough."""
    base = dict(name="A", headline="h", username="u", kind="recruiter")
    assert Candidate(**base, employment="current", evidence="card line: ...").reviewable is True
    assert Candidate(**base, employment="current", evidence="").reviewable is False
    assert Candidate(**base, employment="past", evidence="card line: ...").reviewable is False
    assert Candidate(**base).reviewable is False


def test_contact_md_shows_the_evidence_a_human_would_check():
    """The file recorded only "Why them: engineer" when the bad invite went out."""
    person = Candidate(name="Abarna Devi", headline="Talent Acquisition @ ANSR",
                       username="abarna", kind="recruiter",
                       employment="current", evidence='headline: "Talent Acquisition @ ANSR"')
    body = contact_md("ANSR", "Data & AI Platform", [person])
    assert "Works there:** CURRENT" in body
    assert "Evidence:**" in body and "Talent Acquisition @ ANSR" in body


def test_contact_md_shouts_when_there_is_no_evidence():
    person = Candidate(name="Aditya Sharma", headline="AI / Full-Stack Engineer",
                       username="adityasharmalin", kind="engineer")
    body = contact_md("Berribot", "M365 Infrastructure SME", [person])
    assert "UNVERIFIED" in body
    assert "do not contact" in body
