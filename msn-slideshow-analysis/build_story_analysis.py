from __future__ import annotations

import csv
import re
from pathlib import Path


BASE_DIR = Path("/Users/mmitchell/Desktop/coconut")
DATA_DIR = BASE_DIR / "msn-slideshow-analysis"
SOURCE = DATA_DIR / "MSN Story Audit Oct 2025 - May 2026 - all stories.csv"
OUTPUT = DATA_DIR / "story_analysis_database.csv"
SCHEMA = DATA_DIR / "analysis_schema.md"


BOILERPLATE_PREFIXES = [
    r"^why ",
    r"^what ",
    r"^how ",
    r"^here's ",
    r"^here is ",
    r"^we asked ",
    r"^we spoke to ",
    r"^we sold ",
    r"^another ",
    r"^ex-",
    r"^the ",
]

FRAME_RULES = [
    {
        "name": "contrarian authority quote",
        "pattern": re.compile(r"^why (?P<who>.+?) says (?P<claim>.+)$", re.I),
        "framing": "Provocative future-shock framing anchored by a contrarian quote from a high-profile figure",
        "content_type": "Explainer / analysis",
        "tone": "Provocative, speculative, debate-oriented",
        "hook_type": "authority quote",
        "narrative_device": "prediction",
        "evidence_type": "expert quote",
        "scope": "Broad, especially strong in finance/AI/personal-finance coverage",
    },
    {
        "name": "expert roundup",
        "pattern": re.compile(r"we asked (?P<count>\d+|[a-z-]+)? ?(?P<who>.+?) what they think", re.I),
        "framing": "Expert-roundup framing that turns a claim into a mini-debate",
        "content_type": "Explainer / analysis",
        "tone": "Curious, adjudicative, connective",
        "hook_type": "expert consensus check",
        "narrative_device": "multi-voice contrast",
        "evidence_type": "expert quotes",
        "scope": "Broad; especially reusable for finance, health, AI, and consumer topics",
    },
    {
        "name": "personal transformation",
        "pattern": re.compile(r"^we sold everything we owned.*retired in europe", re.I),
        "framing": "Personal-transformation framing built around a dramatic life change and its tradeoffs",
        "content_type": "Feature / personal essay",
        "tone": "Reflective, candid, practical",
        "hook_type": "personal story",
        "narrative_device": "before/after",
        "evidence_type": "first-person anecdote",
        "scope": "Broad but especially effective in lifestyle, travel, real estate, and career coverage",
    },
    {
        "name": "breaking news arrest",
        "pattern": re.compile(r"arrest(ed|) .*released after arrest|will not be silenced", re.I),
        "framing": "Conflict-driven breaking-news framing centered on a public confrontation or arrest",
        "content_type": "Breaking news / report",
        "tone": "Urgent, adversarial, high-stakes",
        "hook_type": "conflict",
        "narrative_device": "escalation",
        "evidence_type": "reporting",
        "scope": "Broad; strongest for politics, media, and public-figure coverage",
    },
    {
        "name": "recurring incident",
        "pattern": re.compile(r"^another .*(u-turned|turned back|diversion)|once again", re.I),
        "framing": "Recurrence framing that makes one odd incident feel like a pattern",
        "content_type": "News / report",
        "tone": "Ironic, surprising, lightly dramatic",
        "hook_type": "surprise",
        "narrative_device": "repetition",
        "evidence_type": "reporting",
        "scope": "Broad; especially reusable in transportation, consumer, and operations stories",
    },
    {
        "name": "institutional pressure",
        "pattern": re.compile(r"navy|aircraft carrier|months at sea|combat, fire, and plumbing problems", re.I),
        "framing": "Operational-pressure framing that dramatizes strain inside a major institution",
        "content_type": "Feature / report",
        "tone": "Serious, cinematic, operational",
        "hook_type": "institutional stakes",
        "narrative_device": "stress accumulation",
        "evidence_type": "reporting",
        "scope": "Subject-specific: military and defense",
    },
    {
        "name": "internal memo fallout",
        "pattern": re.compile(r"here's what .* hr .* telling staff|memo|employees", re.I),
        "framing": "Internal-fallout framing that shows how an organization is managing external controversy",
        "content_type": "Service / report",
        "tone": "Pragmatic, tense, managerial",
        "hook_type": "institutional response",
        "narrative_device": "inside view",
        "evidence_type": "reporting",
        "scope": "Subject-specific: workplace, corporate, and politics-adjacent business coverage",
    },
    {
        "name": "future trend",
        "pattern": re.compile(r"in the next \d+ years|future|next \d+ years|by 20\d\d", re.I),
        "framing": "Future-shift framing that turns a macro prediction into a reader-relevant consequence",
        "content_type": "Explainer / analysis",
        "tone": "Speculative, forward-looking, consequential",
        "hook_type": "trend",
        "narrative_device": "forecast",
        "evidence_type": "expert quote",
        "scope": "Broad, but especially strong in finance, AI, tech, and career coverage",
    },
    {
        "name": "utility guide",
        "pattern": re.compile(r"how to|what to know|what you need to know|best|top|tips|guide", re.I),
        "framing": "Utility framing that promises direct reader payoff",
        "content_type": "Guide / service",
        "tone": "Helpful, practical, direct",
        "hook_type": "utility",
        "narrative_device": "service promise",
        "evidence_type": "mixed",
        "scope": "Broad",
    },
    {
        "name": "warning risk",
        "pattern": re.compile(r"warning|risk|danger|could|might", re.I),
        "framing": "Risk framing that turns uncertainty into a reader warning",
        "content_type": "Explainer / analysis",
        "tone": "Cautionary, serious, sometimes alarmed",
        "hook_type": "warning",
        "narrative_device": "stakes escalation",
        "evidence_type": "mixed",
        "scope": "Broad",
    },
    {
        "name": "market movement",
        "pattern": re.compile(r"stocks|market|inflation|earnings|retirement|money|finance", re.I),
        "framing": "Money-impact framing that ties a market or personal-finance claim to real-world consequences",
        "content_type": "Explainer / analysis",
        "tone": "Practical, consequential, sometimes speculative",
        "hook_type": "financial consequence",
        "narrative_device": "implication",
        "evidence_type": "analysis",
        "scope": "Subject-specific: finance and markets",
    },
]


VERTICAL_HINTS = {
    "Finance": ("financial consequences", "money, saving, investing, retirement, and wealth"),
    "Markets": ("market movement", "stocks, macro signals, and investor consequences"),
    "AI": ("AI trend", "AI capabilities, business impact, and future implications"),
    "Tech": ("technology change", "consumer tech, software, platforms, and startup impact"),
    "Careers": ("workplace utility", "jobs, layoffs, interviews, and workplace strategy"),
    "Health": ("health risk or advice", "health outcomes, medical risk, and wellness choices"),
    "Travel": ("travel utility", "destinations, disruptions, and traveler decision-making"),
    "Transportation": ("operational disruption", "airlines, transit, and travel operations"),
    "Retail": ("consumer and retail stakes", "shopping, store strategy, and consumer behavior"),
    "Real Estate": ("housing cost and tradeoffs", "homes, rents, migration, and property decisions"),
    "Military & Defense": ("defense and operational pressure", "military operations and hardware"),
    "Politics": ("political conflict", "elected officials, policy fights, and public backlash"),
    "Media": ("media conflict", "public figures, outlets, and attention dynamics"),
    "Entertainment": ("celebrity and cultural attention", "celebrity moves, audience interest, and culture"),
}

VERTICAL_AUDIENCE = {
    "Finance": "people tracking money and saving",
    "Markets": "market watchers",
    "AI": "readers following AI and tech change",
    "Tech": "tech readers",
    "Careers": "job seekers and workers",
    "Health": "health-conscious readers",
    "Travel": "travelers",
    "Transportation": "travelers and commuters",
    "Retail": "shoppers and retail watchers",
    "Real Estate": "people tracking housing and relocation",
    "Military & Defense": "readers following defense and military operations",
    "Politics": "readers following politics and power",
    "Media": "readers following media and public figures",
    "Entertainment": "cultural and entertainment readers",
    "Law": "readers following legal developments",
    "Education": "parents, students, and education readers",
    "Food": "food and consumer readers",
    "Small Business": "small-business readers",
    "Energy": "readers following energy and prices",
    "Economy": "readers tracking the economy",
    "Parenting": "parents",
    "Reviews/Guides": "readers looking for recommendations",
    "Discourse": "readers following culture and public debate",
    "Strategy": "business readers",
    "News": "general news readers",
    "Advertising": "marketing and advertising readers",
    "Sports": "sports readers",
}

VERTICAL_THEMES = {
    "Finance": "money and personal-finance consequences",
    "Markets": "market and investor consequences",
    "AI": "AI's impact on work, business, and consumers",
    "Tech": "technology change and its real-world effects",
    "Careers": "workplace security and career moves",
    "Health": "health risk, habits, and medical decisions",
    "Travel": "trip disruptions and travel choices",
    "Transportation": "transportation disruptions and logistics",
    "Retail": "shopping behavior and store strategy",
    "Real Estate": "housing decisions and cost tradeoffs",
    "Military & Defense": "military operations and readiness",
    "Politics": "political conflict and backlash",
    "Media": "media conflict and public fallout",
    "Entertainment": "celebrity attention and cultural reaction",
    "Law": "legal consequences and institutional fallout",
    "Education": "school and student consequences",
    "Food": "food choices, cost, and convenience",
    "Small Business": "small-business margins and survival",
    "Energy": "energy prices and infrastructure pressure",
    "Economy": "household pressure and cost of living",
    "Parenting": "family tradeoffs and caregiving",
    "Reviews/Guides": "consumer buying decisions",
    "Discourse": "cultural debate and generational tension",
    "Strategy": "business decisions and execution",
    "News": "current events and public consequences",
    "Advertising": "ad strategy and audience reach",
    "Sports": "sports developments and fan interest",
    "Science": "scientific developments and implications",
    "Healthcare": "healthcare decisions and outcomes",
    "Enterprise": "business operations and company decisions",
    "Startups": "startup growth and business model questions",
    "Personal Finance": "money decisions and financial tradeoffs",
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def headline_word_count(headline: str) -> int:
    return len([w for w in re.findall(r"\b[\w'-]+\b", headline) if w])


def short_clause(text: str, limit: int = 18) -> str:
    words = re.findall(r"\b[\w'-]+\b", clean(text))
    if len(words) <= limit:
        return clean(text)
    return " ".join(words[:limit]) + "..."


def infer_vertical_frame(vertical: str) -> tuple[str, str]:
    vertical = clean(vertical)
    return VERTICAL_HINTS.get(vertical, ("broad framing", "a general audience")) 


def infer_subject(headline: str, vertical: str) -> str:
    t = clean(headline)
    lower = t.lower()

    if "student-loan" in lower and "lawsuit" in lower:
        return "Student-loan forgiveness lawsuit and borrower fallout"

    if lower.startswith("i ") or lower.startswith("my ") or lower.startswith("we "):
        return subject_from_first_person(headline)

    if "tested by experts" in lower or re.search(r"\bbest\b|\btop\b", lower):
        return subject_from_guides(headline)

    if lower.startswith("we asked "):
        return "Expert reactions to a current issue"

    if "settlement" in lower and ("qualif" in lower or "join" in lower or "deadline" in lower):
        return "Settlement eligibility and claims deadline"
    if "borrower" in lower and "transfer" in lower and "treasury" in lower:
        return "Student-loan borrower account transfers and repayment fallout"
    if "student-loan" in lower and "lawsuit" in lower:
        return "Student-loan forgiveness lawsuit and borrower fallout"
    if "student-loan" in lower or "student loan" in lower:
        if any(k in lower for k in ["repayment", "forgiveness", "accounts", "borrowers", "loan"]):
            return "Student-loan repayment and borrower fallout"
    if "inflation" in lower:
        return "Inflation and household purchasing power"
    if any(k in lower for k in ["tariff", "tariffs"]):
        return "Tariffs and consumer or business costs"
    if any(k in lower for k in ["federal reserve", "fed", "rate cut", "interest rate", "mortgage bond", "rates"]):
        return "Interest rates and borrowing costs"
    if any(k in lower for k in ["jobs report", "job market", "hiring", "layoff", "unemployment"]):
        return "Job market and hiring conditions"
    if "basic income" in lower:
        return "Basic income policy or experiment"
    if "ai" in lower and "power" in lower:
        return "AI power demand and energy costs"
    if "blue origin" in lower or "satellite launch" in lower or ("launch" in lower and "did not go well" in lower):
        return "Commercial space launch failure"
    if "bigfoot" in lower:
        return "Bigfoot documentary controversy"
    if "public breakup" in lower or "breakups are still a thing" in lower:
        return "Public breakup culture and awkward fallout"
    if "share the wealth" in lower and "employees" in lower:
        return "Employee pay-sharing and workplace fairness"
    if "gig work" in lower or "gig economy" in lower:
        return "Gig work and labor flexibility"
    if "workers over 80" in lower:
        return "Older workers and late-career work"
    if any(k in lower for k in ["superrich", "ultrawealthy"]) and any(k in lower for k in ["hot spots", "hotspot", "fastest-growing"]):
        return "Wealth migration and housing pressure"
    if "childcare" in lower or "weird hours" in lower:
        return "Working-parent childcare strain"

    if match := re.match(r"why (.+?) says (.+)", t, re.I):
        if "retirement" in lower or "saving" in lower:
            return "Elon Musk's prediction about retirement saving in an AI-abundance future"
        return f"A future prediction from {short_clause(match.group(1), 8)}"

    if match := re.match(r"we asked .*? experts? (?:and ai gurus )?what they think of (.+)", t, re.I):
        return "Expert reactions to a disputed claim"

    if "retired in europe" in lower:
        return "Retiring in Europe and the cost and lifestyle tradeoffs of leaving the US"

    if "u-turned over the atlantic" in lower or "diversion" in lower:
        return "A travel disruption caused by an onboard incident"

    if "released after arrest" in lower or "arrested" in lower:
        return "Public fallout after an arrest"

    if "aircraft carrier" in lower or "navy" in lower:
        return "Operational strain on a Navy ship"

    if "target" in lower and "hr" in lower:
        return "A company's internal response to political backlash"

    if match := re.match(r"here's what (.+)$", t, re.I):
        return short_clause(match.group(1), 16)

    if match := re.match(r"another (.+)", t, re.I):
        return short_clause(match.group(1), 16)

    return VERTICAL_THEMES.get(vertical, "a news development")


def subject_from_guides(headline: str) -> str:
    t = clean(headline)
    lower = t.lower()
    if "best ad" in lower or "ad that ever ran" in lower:
        return "Political advertising and message strategy"
    if match := re.search(r"(?:the\s+)?(?:\d+\s+)?best\s+([a-z0-9&' -]+?)(?:,|$|\s+tested|\s+in |\s+of )", lower, re.I):
        return f"{short_clause(match.group(1), 8)} buying guide"
    if match := re.search(r"(?:the\s+)?top\s+([a-z0-9&' -]+?)(?:,|$|\s+in |\s+of )", lower, re.I):
        return f"{short_clause(match.group(1), 8)} buying guide"
    if match := re.search(r"(?:how to|what to know about|guide to) (.+)", lower, re.I):
        return f"{short_clause(match.group(1), 10)} guide"
    return "Consumer buying decisions and comparisons"


def subject_from_first_person(headline: str) -> str:
    t = clean(headline)
    lower = t.lower()
    if "retired in europe" in lower or ("retire" in lower and "europe" in lower):
        return "Retirement abroad and expat cost-of-living tradeoffs"
    if "we asked 2 partners at goldman sachs" in lower:
        return "Wall Street pressure"
    if "we asked americans" in lower and "prices" in lower:
        return "Cost-of-living perceptions"
    if match := re.search(r"moved my family to (.+?) to save money", lower):
        return "Relocation and cost-cutting"
    if match := re.search(r"help people over \d+ get hired", lower):
        return "Older-job-seeker advice"
    if "family's grocery bill" in lower:
        return "Household budgeting pressure"
    if "mom is healthy" in lower and "purging her stuff" in lower:
        return "Aging-parent downsizing"
    if "grandpa invited himself" in lower and "trip abroad" in lower:
        return "Intergenerational travel"
    if "spent 22 years as a military wife" in lower:
        return "Military-family transition"
    if "12-year-old couldn't read" in lower and "dyslexia" in lower:
        return "Learning-disability discovery"
    if "we are on day 37 of no paycheck" in lower:
        return "Shutdown-related income stress"
    if "no paycheck" in lower and "shopping ban" in lower:
        return "Shutdown-related income stress"
    if "moved to a beach town" in lower:
        return "Loneliness after relocation"
    if "moved back to" in lower and "culture shock" in lower:
        return "Reverse-culture shock"
    if "same high-protein" in lower or "same breakfast" in lower:
        return "Simple routine and nutrition"
    if "advise lottery winners" in lower or "powerball" in lower:
        return "Lottery-winner advice"
    if "grandmother handed me $2,000" in lower and "go to europe" in lower:
        return "Gift-led life change"
    if "dream town in colorado" in lower:
        return "Disappointing relocation"
    if "off the grid in rural new mexico" in lower:
        return "Rural-to-urban reversal"
    if "moved away from my family" in lower and "dad dropped everything" in lower:
        return "Family support across distance"
    if "moved in with my family" in lower or "moved in with my parents" in lower:
        return "Extended-family living"
    if "airbnb" in lower and ("nightmare guests" in lower or "quit hosting" in lower):
        return "Short-term rental burnout"
    if "reselling products on amazon" in lower:
        return "Reselling business growth"
    if "visited" in lower and "here's what tiktok doesn't show" in lower:
        return "Travel-reality check"
    if "wrote me a letter before my wedding" in lower:
        return "Marriage and family advice"
    if "boyfriend lives in the house" in lower and "mortgage" in lower:
        return "Shared housing finances"
    if "kept working as an rn" in lower or "sense of purpose" in lower:
        return "Work and identity"
    if "missed my flight" in lower or "tsa checkpoint" in lower:
        return "Airport-delay disruption"
    if "worked on cruises" in lower and "never do on board" in lower:
        return "Cruise-travel habits"
    if "9 whole foods" in lower or ("protein" in lower and "whole foods" in lower):
        return "Protein-focused eating"
    if "wanted to be perfect" in lower and "grandmother" in lower:
        return "Intergenerational advice"
    if "bought two bowls" in lower and "sold them" in lower:
        return "Resale arbitrage"
    if "costco membership" in lower and "save over" in lower:
        return "Membership-based savings"
    if "doesn't want to move to an assisted living facility" in lower:
        return "Elder-care conflict"
    if "babysit my 2 kids" in lower:
        return "Childcare trial run"
    if "made $" in lower and "amazon" in lower and "reselling" in lower:
        return "Amazon resale economics"
    if "make around $10,000 a month" in lower and "amazon side hustle" in lower:
        return "Amazon side-hustle income"
    if "my husband asked for a divorce" in lower:
        return "Divorce and travel"
    if "my 8-year-old invited his 4 best friends to dinner" in lower:
        return "Child independence"
    if "my wife and i let go of our dreams" in lower or "moved to a small town so we could be closer" in lower:
        return "Family proximity tradeoff"
    if "the oldest car at school drop-off" in lower:
        return "Car-upgrade regret"
    if "spend $16,000 on a newer vehicle" in lower:
        return "Vehicle-purchase regret"
    if "i'm a chef" in lower or "i've been" in lower or "i visited" in lower:
        return "Expertise or travel firsthand"
    if "retire" in lower or "retirement" in lower:
        return "Retirement tradeoff"
    if "job" in lower or "unemployment" in lower or "career" in lower:
        return "Career setback"
    if "daughter" in lower or "son" in lower or "children" in lower or "grandchildren" in lower:
        return "Family and caregiving tradeoff"
    if "college" in lower or "housing" in lower:
        return "College-planning conflict"
    if "home" in lower or "rent" in lower or "housing" in lower:
        return "Housing tradeoff"
    if "chef" in lower or "country" in lower or "states" in lower:
        return "Achievement and expertise"
    return "Personal tradeoff"


def main_point_from_subject(subject: str, vertical: str) -> str:
    s = clean(subject).lower()
    vertical = clean(vertical)
    if "retirement abroad" in s or "expat cost-of-living" in s:
        return "How retiring abroad changes cost of living, lifestyle, and long-term retirement strategy"
    if "elon musk" in s and ("retirement" in s or "saving" in s):
        return "How an AI-abundance future could change the way people think about retirement saving"
    if "expert reactions" in s or "expert disagreement" in s or "opinion split" in s:
        return "How outside voices validate, challenge, or complicate the original claim"
    if "public fallout after an arrest" in s or "public fallout" in s:
        return "What the confrontation means for reputation, fallout, and next-step consequences"
    if "travel disruption" in s or "trip disruption" in s:
        return "How an unexpected disruption affects the trip and the broader travel experience"
    if "military strain" in s:
        return "How operational strain affects readiness and the ability to keep the mission on track"
    if "internal response" in s:
        return "How an organization manages a politically sensitive moment internally"
    if "future uncertainty" in s:
        return "How a long-range prediction could reshape expectations and decisions"
    if "student-loan" in s or "student loan" in s or "repayment" in s:
        return "How student-loan repayment changes affect borrower budgets and financial planning"
    if "inflation" in s:
        return "How rising prices squeeze purchasing power and shape policy pressure"
    if "tariff" in s:
        return "How tariffs raise costs for consumers and businesses"
    if "interest rate" in s or "federal reserve" in s or "fed" in s or "mortgage" in s or "rates" in s:
        return "How rate changes affect borrowing costs, markets, and household budgets"
    if "job market" in s or "hiring" in s or "layoff" in s or "unemployment" in s:
        return "How labor-market shifts change hiring, wages, and job security"
    if "basic income" in s:
        return "What a cash-support experiment says about income stability and outcomes"
    if "ai power" in s or "energy costs" in s:
        return "How AI demand could raise energy costs or slow growth"
    if "commercial space launch failure" in s:
        return "What the launch failure says about reliability and mission risk"
    if "bigfoot" in s:
        return "What new evidence does to the Bigfoot debate"
    if "public breakup" in s:
        return "How public relationships create awkward fallout and attention"
    if "employee pay-sharing" in s:
        return "How companies share gains with workers and why it matters"
    if "gig work" in s:
        return "How gig work changes flexibility, income, and job security"
    if "older workers" in s:
        return "How later-life work changes retirement timing and income"
    if "wealth migration" in s:
        return "How wealth concentration shifts housing demand and where rich households settle"
    if "childcare" in s:
        return "How working parents juggle childcare gaps, schedule pressure, and work demands"
    if "career setback" in s or "career pressure" in s or "career fallout" in s:
        return "How career disruption changes money, timing, and next-step decisions"
    if "retirement tradeoff" in s or "retirement pressure" in s:
        return "How retirement changes money, identity, and daily life"
    if "housing tradeoff" in s or "housing pressure" in s:
        return "How housing decisions force a tradeoff between cost, space, and lifestyle"
    if "relocation" in s:
        return "How moving changes cost, community, and long-term plans"
    if "money" in s or "financial" in s:
        return "How the story changes money decisions, risk, or long-term planning"
    if "ai" in s:
        return "How the AI shift could change work, business, or consumer expectations"
    if "market" in s or "investor" in s:
        return "How the story affects market expectations and investor behavior"
    if "health" in s or "medical" in s:
        return "How the story changes risk, habits, or care decisions"
    if "travel" in s or "transport" in s:
        return "How the story affects travel plans, logistics, or trip reliability"
    if "retail" in s or "consumer" in s:
        return "How the story changes consumer choice, convenience, or cost"
    if "political" in s or "media" in s or "celebrity" in s:
        return "How the conflict shapes attention, reputation, or fallout"
    if "family" in s or "parent" in s:
        return "How the decision changes family routines, support, or caregiving"
    if "business" in s or "startup" in s or "operations" in s:
        return "How the story changes business strategy, execution, or survival"
    if "science" in s or "technology" in s:
        return "How the development changes what people thought was possible"
    if "school" in s or "education" in s:
        return "How the story affects schools, parents, or student outcomes"
    if "food" in s:
        return "How the story changes taste, price, convenience, or habits"
    if "personal tradeoff" in s:
        return "How a personal decision creates a visible tradeoff or consequence"
    if vertical == "Finance":
        return "How the story changes the way readers think about money, risk, or retirement"
    if vertical == "Markets":
        return "How the story could shift market expectations and investor behavior"
    if vertical == "AI":
        return "How the AI shift could change work, business, or consumer expectations"
    if vertical == "Tech":
        return "How the product or platform change could alter user or business behavior"
    if vertical == "Careers":
        return "How the story affects job security, hiring odds, or workplace strategy"
    if vertical == "Health":
        return "How the story affects health risk, habits, or care decisions"
    if vertical in {"Travel", "Transportation"}:
        return "How the disruption affects trip reliability, cost, or passenger convenience"
    if vertical == "Retail":
        return "How the story affects shopping behavior, store strategy, or consumer cost"
    if vertical == "Real Estate":
        return "How the story changes housing costs, relocation choices, or lifestyle tradeoffs"
    if vertical in {"Politics", "Media"}:
        return "How the conflict shapes power, reputation, and public fallout"
    if vertical == "Military & Defense":
        return "How the story affects readiness, operations, or mission strain"
    if vertical == "Economy":
        return "How the story reflects broader household pressure or cost-of-living strain"
    if vertical == "Parenting":
        return "How the decision changes family money, routines, and emotional load"
    if vertical == "Strategy":
        return "How the move changes business decisions, competition, or execution"
    if vertical == "News":
        return "Why the development matters right now and what changes next"
    if vertical == "Law":
        return "How the legal action changes consequences for the people or institution involved"
    if vertical == "Education":
        return "How the development affects schools, parents, or student outcomes"
    if vertical == "Food":
        return "How the story changes food choices, cost, or convenience"
    if vertical == "Small Business":
        return "How the story changes owner margins, survival, or operating decisions"
    if vertical == "Energy":
        return "How the story affects prices, infrastructure, or policy pressure"
    if vertical == "Sports":
        return "Why the development matters to fans and the season ahead"
    if vertical == "Advertising":
        return "How the story changes ad strategy, audience reach, or brand pressure"
    if vertical == "Discourse":
        return "How the story feeds a cultural or generational debate"
    return f"What this story means for {clean(vertical).lower()}" if vertical else "The key development and what it means"


def infer_main_point(headline: str, vertical: str) -> str:
    t = clean(headline)
    lower = t.lower()

    if "student-loan" in lower and "lawsuit" in lower:
        return "How the lawsuit could change student-loan forgiveness for public servants"

    if lower.startswith("i ") or lower.startswith("my ") or lower.startswith("we "):
        if "graduation" in lower and "gift" in lower:
            return "How a small family gift can redirect a life path"
        if "beach town" in lower:
            return "How an idealized move can turn unexpectedly lonely"
        if "amazon side hustle" in lower or "amazon" in lower and "revenue" in lower:
            return "How a side hustle can become real income"
        if "military wife" in lower or "divorce" in lower:
            return "What happens when a long-planned life changes after divorce"
        if "dyslexia" in lower:
            return "How a hidden learning issue can go unnoticed for years"
        if "grocery bill" in lower:
            return "How families try to cut a painful monthly expense"
        if "shutdown" in lower or "no paycheck" in lower:
            return "How a shutdown hits family finances and routines"
        if "reselling" in lower:
            return "How a reselling business turns into real money"
        if "travel" in lower or "flight" in lower or "cruise" in lower:
            return "How a personal trip turns into a broader lesson about travel"
        return main_point_from_subject(subject_from_first_person(headline), vertical)
    if "tested by experts" in lower or re.search(r"\bbest\b|\btop\b", lower):
        if "best" in lower or "top" in lower:
            return "Which options actually stand out for buyers"
        return "Which products or choices are worth the reader's attention"
    if re.match(r"why .+ says .+", t, re.I):
        claim = clean(t.split("says", 1)[1])
        if "retirement" in lower or "saving" in lower:
            return "How Elon Musk's AI-driven abundance thesis could reshape retirement saving"
        if "tariff" in lower:
            return "How a promised tariff dividend could affect prices and whether it will happen"
        if "student-loan" in lower or "student loan" in lower:
            return "How a student-loan overhaul could change borrower budgets and repayment"
        if any(k in lower for k in ["interest rates", "crypto winter", "ai disruption", "markets"]):
            return "What the CEO's confidence says about crypto, AI, and 2026 expectations"
        return f"How {short_clause(claim, 14).rstrip('.')} could change expectations or decisions"
    if "we asked" in lower and "what they think" in lower:
        return "Whether experts agree with the claim"
    if lower.startswith("we asked "):
        return "How the people asked responded to a current issue"
    if "settlement" in lower and ("qualif" in lower or "join" in lower or "deadline" in lower):
        return "Who can still claim settlement money before the deadline"
    if "borrower" in lower and "transfer" in lower and "treasury" in lower:
        return "How the account transfer affects borrowers and what it means for repayment"
    if "retired in europe" in lower:
        return "How retiring abroad changes cost of living, lifestyle, and retirement strategy"
    if "u-turned" in lower or "diversion" in lower:
        return "What an onboard incident says about travel disruption"
    if "arrested" in lower or "released after arrest" in lower:
        return "What the arrest means for public fallout"
    if "aircraft carrier" in lower or "navy" in lower:
        return "What prolonged strain says about military readiness"
    if "hr" in lower and "staff" in lower:
        return "How a company is managing political backlash internally"
    if "in the next" in lower or "future" in lower:
        return "What a future prediction could mean in practical terms"
    if any(k in lower for k in ["how to", "what to know", "best", "top", "tips", "guide"]):
        return "Which option is the best fit and why"
    if lower.startswith("we asked "):
        return "Crowd response"
    subject = infer_subject(headline, vertical)
    if subject:
        return main_point_from_subject(subject, vertical)
    return main_point_from_subject(VERTICAL_THEMES.get(vertical, "a news development"), vertical)


def infer_rule_framing(rule_name: str, headline: str, vertical: str) -> str:
    subject = infer_subject(headline, vertical).lower()
    if subject in VERTICAL_THEMES.values():
        subject = subject
    mapping = {
        "contrarian authority quote": "Contrarian future-prediction framing anchored by a high-profile authority",
        "expert roundup": "Expert-check framing around a disputed claim",
        "personal transformation": "Expat-retirement tradeoff framing around a major life change",
        "breaking news arrest": "Breaking-news fallout framing after an arrest",
        "recurring incident": "Repeat-disruption framing around a travel incident",
        "institutional pressure": "Operational-strain framing inside a major institution",
        "internal memo fallout": "Internal-fallout framing after a political firestorm",
        "future trend": "Future-impact framing built around a big prediction",
        "utility guide": "Expert-tested buying guide framing",
        "warning risk": "Warning framing around a potential downside",
        "market movement": "Money-consequence framing for readers",
    }
    return mapping.get(rule_name, subject)


def infer_frame(headline: str, vertical: str) -> dict[str, str]:
    t = clean(headline)
    lower = t.lower()

    for rule in FRAME_RULES:
        if rule["pattern"].search(t):
            return {
                "framing": infer_rule_framing(rule["name"], headline, vertical),
                "angle": {
                    "contrarian authority quote": "Turn a sweeping prediction into a practical money or life-decision debate",
                    "expert roundup": "Use multiple expert reactions to test a provocative claim and show where the consensus breaks",
                    "personal transformation": "Turn a major life change into a lesson about tradeoffs and consequences",
                    "breaking news arrest": "Lead with the public confrontation, then widen to the fallout and response",
                    "recurring incident": "Make an odd repeat event feel newsworthy by highlighting the pattern",
                    "institutional pressure": "Show a major institution under strain through a series of concrete problems",
                    "internal memo fallout": "Reveal the company’s internal response to an external political problem",
                    "future trend": "Translate a long-range forecast into a near-term reader implication",
                    "utility guide": "Promise a shortcut, answer, or decision aid the reader can use now",
                    "warning risk": "Frame the story as a caution about what could go wrong or why it matters",
                    "market movement": "Turn a market or finance claim into a consequence for ordinary readers",
                }.get(rule["name"], rule["framing"]),
                "content_type": rule["content_type"],
                "tone": rule["tone"],
                "framing_scope_flag": rule["scope"],
                "hook_type": rule["hook_type"],
                "narrative_device": rule["narrative_device"],
                "evidence_type": rule["evidence_type"],
                "specificity_level": "Highly specific" if any(
                    s in lower for s in ["elon musk", "target", "united", "don lemon", "navy", "retired in europe"]
                ) else "Moderately specific",
            }

    content_type = "News / report"
    tone = "Neutral, informative"
    hook_type = "news peg"
    narrative_device = "direct reporting"
    evidence_type = "reporting"
    specificity_level = "Moderately specific"
    scope = "Broad"

    if any(k in lower for k in ["said", "says", "revealed", "told"]):
        content_type = "Report / analysis"
        tone = "Informative, quote-driven"
        hook_type = "authority quote"
        narrative_device = "attribution"
        evidence_type = "reporting"
    if any(k in lower for k in ["how to", "what to know", "guide", "best", "top", "tips"]):
        content_type = "Guide / service"
        tone = "Helpful, practical, direct"
        hook_type = "utility"
        narrative_device = "service promise"
        evidence_type = "mixed"
    if any(k in lower for k in ["another", "again", "once again", "u-turned", "diversion"]):
        content_type = "News / report"
        tone = "Surprised, concise"
        hook_type = "surprise"
        narrative_device = "repetition"
        evidence_type = "reporting"
    if any(k in lower for k in ["future", "next", "years", "irrelevant", "won't matter"]):
        content_type = "Explainer / analysis"
        tone = "Speculative, consequential"
        hook_type = "trend"
        narrative_device = "forecast"
        evidence_type = "analysis"

    return {
        "framing": infer_framing(headline, vertical, content_type, hook_type),
        "angle": infer_angle(headline, vertical, content_type, hook_type),
        "content_type": content_type,
        "tone": tone,
        "framing_scope_flag": scope,
        "hook_type": hook_type,
        "narrative_device": narrative_device,
        "evidence_type": evidence_type,
        "specificity_level": specificity_level,
    }


def infer_framing(headline: str, vertical: str, content_type: str, hook_type: str) -> str:
    lower = headline.lower()
    vertical = clean(vertical)
    content_type = clean(content_type)
    hook_type = clean(hook_type)
    subject = infer_subject(headline, vertical)

    if "why" in lower and "says" in lower:
        return "Contrarian future-prediction framing anchored by a high-profile authority"
    if "we asked" in lower and "what they think" in lower:
        return "Expert-check framing for a disputed claim"
    if lower.startswith("we asked "):
        return "Crowd-response framing around a current issue"
    if "retired in europe" in lower or "sold everything" in lower:
        return "First-person expat-retirement framing about the tradeoffs of leaving the US"
    if "arrested" in lower or "released after arrest" in lower:
        return "Breaking-news fallout framing around an arrest"
    if "u-turned" in lower or "diversion" in lower:
        return "Repeat-disruption framing around a weird travel incident"
    if "aircraft carrier" in lower or "navy" in lower:
        return "Operational-strain framing inside the Navy"
    if "hr" in lower and "staff" in lower:
        return "Internal-fallout framing after a political firestorm"
    if "future" in lower or "next" in lower or "years" in lower:
        return f"Future-impact framing about {subject.lower()}"
    if content_type == "Guide / service":
        return f"Expert-tested buying guide about {subject.lower()}"
    if content_type == "Report / analysis":
        return f"Quote-led analysis of {subject.lower()}"
    if content_type == "Feature / personal essay":
        return f"Personal-story framing built around {subject.lower()}"
    if content_type == "Feature / report":
        return f"Scene-driven report about {subject.lower()}"
    if content_type == "Breaking news / report":
        return f"Breaking-news framing around {subject.lower()}"
    if content_type == "News / report" and hook_type == "surprise":
        return f"Odd-incident framing around {subject.lower()}"
    if content_type == "News / report" and hook_type == "conflict":
        return f"Conflict-and-fallout framing around {subject.lower()}"
    if content_type == "News / report" and hook_type == "institutional stakes":
        return f"Institution-under-pressure framing around {subject.lower()}"

    if vertical in {"Finance", "Markets"}:
        return f"Money-consequence framing around {subject.lower()}"
    if vertical == "AI":
        return f"AI-impact framing around {subject.lower()}"
    if vertical == "Tech":
        return f"Technology-change framing around {subject.lower()}"
    if vertical == "Careers":
        return f"Workplace-strategy framing around {subject.lower()}"
    if vertical == "Health":
        return f"Health-risk framing around {subject.lower()}"
    if vertical in {"Travel", "Transportation"}:
        return f"Travel-disruption framing around {subject.lower()}"
    if vertical == "Retail":
        return f"Consumer-impact framing around {subject.lower()}"
    if vertical == "Real Estate":
        return f"Housing-tradeoff framing around {subject.lower()}"
    if vertical == "Politics":
        return f"Political-conflict framing around {subject.lower()}"
    if vertical == "Media":
        return f"Media-fallout framing around {subject.lower()}"
    if vertical == "Military & Defense":
        return f"Defense-pressure framing around {subject.lower()}"
    if vertical == "Economy":
        return f"Household-pressure framing around {subject.lower()}"
    if vertical == "Parenting":
        return f"Family-tradeoff framing around {subject.lower()}"
    if vertical == "Reviews/Guides":
        return f"Expert-tested shopping framing around {subject.lower()}"
    if vertical == "Discourse":
        return f"Cultural-debate framing around {subject.lower()}"
    if vertical == "Strategy":
        return f"Business-strategy framing around {subject.lower()}"
    if vertical == "News":
        return f"Straight-news framing around {subject.lower()}"
    if vertical == "Law":
        return f"Legal-fallout framing around {subject.lower()}"
    if vertical == "Education":
        return f"Education-impact framing around {subject.lower()}"
    if vertical == "Food":
        return f"Consumer-choice framing around {subject.lower()}"
    if vertical == "Small Business":
        return f"Small-business pressure framing around {subject.lower()}"
    if vertical == "Energy":
        return f"Energy-pricing framing around {subject.lower()}"
    if vertical == "Sports":
        return f"Sports-interest framing around {subject.lower()}"
    if vertical == "Advertising":
        return f"Ad-industry framing around {subject.lower()}"
    if vertical == "Entertainment":
        return f"Celebrity-and-culture framing around {subject.lower()}"
    return f"News framing around {subject.lower()}"


def infer_angle(headline: str, vertical: str, content_type: str, hook_type: str) -> str:
    lower = headline.lower()
    vertical = clean(vertical)
    content_type = clean(content_type)
    hook_type = clean(hook_type)

    if "why" in lower and "says" in lower:
        return "Use a high-profile quote to turn a macro future claim into a retirement-planning and lifestyle debate"
    if "we asked" in lower:
        return "Use expert reaction to test a claim and create a built-in tension between viewpoints"
    if "retired in europe" in lower:
        return "Use a personal move abroad to compare cost of living, lifestyle, and expat retirement tradeoffs"
    if "arrested" in lower or "released after arrest" in lower:
        return "Use a public arrest and defiant response to drive the news peg"
    if "u-turned" in lower or "diversion" in lower:
        return "Use an unusual operational mishap as the memorable hook"
    if "aircraft carrier" in lower or "navy" in lower:
        return "Use scale and accumulated problems to make the story feel consequential"
    if "hr" in lower and "staff" in lower:
        return "Use the internal memo as a window into how the company is managing political pressure"

    if content_type == "Explainer / analysis":
        return "Translate the claim into implications the reader can understand quickly"
    if content_type == "Report / analysis":
        return "Pair fresh reporting with a visible interpretation of why the story matters"
    if content_type == "Guide / service":
        return "Frame the story as a practical decision aid or shortcut"
    if content_type == "Feature / report":
        return "Use scene-setting and accumulated detail to show the significance of the situation"
    if content_type == "News / report" and hook_type == "conflict":
        return "Center the clash and make the stakes of the confrontation clear"
    if content_type == "News / report" and hook_type == "surprise":
        return "Make the oddity itself the hook and keep the image concrete"
    if content_type == "News / report" and hook_type == "institutional stakes":
        return "Make the institution’s strain the core news value"

    if vertical in {"Finance", "Markets"}:
        return "Turn the headline into a question about money, risk, or personal financial judgment"
    if vertical == "AI":
        return "Show how the AI claim changes business, labor, or consumer expectations"
    if vertical == "Tech":
        return "Use a product or platform change to signal bigger industry consequences"
    if vertical == "Careers":
        return "Connect the story to job security, workplace behavior, or hiring strategy"
    if vertical in {"Travel", "Transportation"}:
        return "Make the logistics problem or travel choice the central hook"
    if vertical in {"Retail", "Real Estate"}:
        return "Frame the story around a consumer or household tradeoff"
    if vertical in {"Politics", "Media"}:
        return "Use public conflict and fallout to show power, image, or institutional pressure"
    return "Use the headline's specific news peg to make the reader care immediately"


def infer_reader_promise(headline: str, vertical: str) -> str:
    lower = headline.lower()
    audience = VERTICAL_AUDIENCE.get(clean(vertical), f"{clean(vertical).lower()} readers")
    if "tested by experts" in lower or re.search(r"\bbest\b|\btop\b", lower):
        return "A ranked or vetted set of options, plus the reasons they stand out"
    if "we asked" in lower:
        return "A quick read on whether experts buy the claim and where they disagree"
    if "why" in lower and "says" in lower:
        if "retirement" in lower or "saving" in lower:
            return "A provocative future claim plus the practical implications for retirement planning"
        if "tariff" in lower:
            return "A look at the promised tariff dividend and what it could mean for prices"
        if "student-loan" in lower or "student loan" in lower:
            return "A look at how a loan overhaul could change borrower budgets"
        if any(k in lower for k in ["interest rates", "crypto winter", "ai disruption", "markets"]):
            return "A look at what the CEO's confidence says about crypto, AI, and rates"
        return "A provocative claim plus the practical implications behind it"
    if lower.startswith("i ") or lower.startswith("my ") or lower.startswith("we "):
        if "retired in europe" in lower:
            return "A firsthand look at retirement abroad, including lifestyle, cost, and expat tradeoffs"
        if "retire" in lower or "retirement" in lower:
            return "A first-person story about how retirement changed money, identity, and daily life"
        if "job" in lower or "career" in lower or "unemployment" in lower:
            return "A first-person account of a career move gone wrong and the lesson behind it"
        if "daughter" in lower or "children" in lower or "grandchildren" in lower:
            return "A personal family story about the cost and strain behind a major life change"
        if "housing" in lower or "home" in lower or "rent" in lower:
            return "A personal housing story about cost, planning, and the consequences of a decision"
        return "A personal story that turns an individual experience into a broader lesson"
    if "how to" in lower or "what to know" in lower or "guide" in lower:
        return "A direct answer, shortcut, or useful next step"
    if "settlement" in lower and ("qualif" in lower or "join" in lower or "deadline" in lower):
        return "Who qualifies for the settlement and what to do before the deadline"
    if "borrower" in lower and "transfer" in lower and "treasury" in lower:
        return "How the transfer changes borrower repayment and what readers should watch next"
    if "student-loan" in lower and "lawsuit" in lower:
        return "How the lawsuit could change student-loan forgiveness for public servants"
    if "student-loan" in lower or "student loan" in lower:
        return "A clear read on how repayment changes affect borrowers, budgets, and relief"
    if "inflation" in lower:
        return "How rising prices affect household budgets and policy expectations"
    if "tariff" in lower:
        return "How tariffs could change costs for shoppers, businesses, and markets"
    if "interest rate" in lower or "federal reserve" in lower or "fed" in lower or "mortgage" in lower:
        return "What the rate move means for borrowing costs, markets, and households"
    if "job market" in lower or "hiring" in lower or "layoff" in lower:
        return "What the labor-market shift means for hiring, wages, and job security"
    if "basic income" in lower:
        return "What the cash-support experiment says about income stability and results"
    if "gig work" in lower or "gig economy" in lower:
        return "What the gig-work shift means for flexibility, pay, and job security"
    if "childcare" in lower:
        return "How childcare pressure affects working parents and daily schedules"
    if "retired in europe" in lower:
        return "A firsthand look at retirement abroad, including lifestyle, cost, and expat tradeoffs"
    if "arrested" in lower or "released after arrest" in lower:
        return "The latest development and the response it triggered"
    if "diversion" in lower or "u-turned" in lower:
        return "A vivid incident and the operational reason it happened"
    if vertical in {"Finance", "Markets"}:
        return "What the claim means for money decisions or financial expectations"
    if vertical == "AI":
        return "How the AI development could affect business, work, or everyday life"
    if vertical == "Tech":
        return "How a product, platform, or founder move could change what users or companies do next"
    if vertical == "Careers":
        return "What the story means for hiring, job security, or workplace strategy"
    if vertical == "Health":
        return "What the health claim means for risk, habits, or daily choices"
    if vertical in {"Travel", "Transportation"}:
        return "How the disruption affects the trip and what it says about travel risks"
    if vertical == "Retail":
        return "What the story means for shoppers, store strategy, or consumer behavior"
    if vertical == "Real Estate":
        return "What the story means for costs, housing choices, or migration decisions"
    if vertical in {"Politics", "Media"}:
        return "Why the conflict matters for public perception, power, or fallout"
    if vertical == "Military & Defense":
        return "What the story means for readiness, operations, or mission strain"
    if vertical == "Law":
        return "What the legal action means for the people or institution involved"
    if vertical == "Education":
        return "What the story means for schools, parents, or student outcomes"
    if vertical == "Food":
        return "What the story means for taste, price, convenience, or habits"
    if vertical == "Small Business":
        return "What the story means for owners trying to protect margins or keep operating"
    if vertical == "Energy":
        return "What the story means for prices, infrastructure, or policy pressure"
    if vertical == "Entertainment":
        return "Why the celebrity or culture move matters for attention, image, or audience reaction"
    if vertical == "Reviews/Guides":
        return "Which options made the cut, what they do well, and what the reader should choose"
    if vertical == "Economy":
        return "How the personal story reflects a bigger pressure on households, work, or retirement"
    if vertical == "Parenting":
        return "What the family decision means for the child's plans, the parents' money, and the emotional fallout"
    if vertical == "Discourse":
        return "How the piece frames a cultural or generational debate and what that says about the moment"
    if vertical == "Strategy":
        return "What the move means for business decisions, competition, or execution"
    if vertical == "News":
        return "The key development and why it matters right now"
    if vertical == "Advertising":
        return "What the story means for ad strategy, audience reach, or brand pressure"
    if vertical == "Science":
        return "What the development changes about what scientists or readers thought was possible"
    if vertical == "Healthcare":
        return "What the story means for care decisions, access, or medical risk"
    if any(k in lower for k in ["said", "says", "revealed", "told", "won't", "won’t", "will"]):
        return "The claim itself and the concrete implication behind it"
    if any(k in lower for k in ["another", "again", "once again", "u-turned", "diversion", "arrested"]):
        return "A surprising event and the immediate consequence or fallout"
    if any(k in lower for k in ["firestorm", "backlash", "controversy", "caught", "released"]):
        return "The backlash or conflict and what it means next"
    if clean(vertical) in VERTICAL_AUDIENCE:
        return f"What this story means for {audience}"
    return "The key development and what the reader should take from it"


def infer_stakes(headline: str, vertical: str, content_type: str, hook_type: str) -> str:
    lower = headline.lower()
    vertical = clean(vertical)
    content_type = clean(content_type)
    hook_type = clean(hook_type)

    if "why" in lower and "says" in lower:
        return "The bigger stake is whether a major technological shift could reshape how readers think about saving and retirement"
    if "we asked" in lower:
        return "The stake is whether the original claim survives expert scrutiny or collapses under debate"
    if "retired in europe" in lower:
        return "The stake is whether the move actually delivers the promised lifestyle gain once costs and tradeoffs are real"
    if "arrested" in lower or "released after arrest" in lower:
        return "The stake is the public and reputational fallout from the arrest, especially for a high-profile figure"
    if "u-turned" in lower or "diversion" in lower:
        return "The stake is the inconvenience, cost, and uncertainty created by an unusual travel disruption"
    if "aircraft carrier" in lower or "navy" in lower:
        return "The stake is operational readiness and the strain placed on a major military asset"
    if "hr" in lower and "staff" in lower:
        return "The stake is employee reaction and how the company manages a politically sensitive moment"

    if content_type == "Explainer / analysis":
        return "The stake is whether readers can understand the trend well enough to respond to it"
    if content_type == "Report / analysis":
        return "The stake is whether the reporting changes how the reader sees the event or institution"
    if content_type == "Guide / service":
        return "The stake is helping the reader avoid a bad decision or unnecessary cost"
    if content_type == "Feature / report":
        return "The stake is the human or institutional cost behind the headline"
    if content_type == "News / report" and hook_type == "conflict":
        return "The stake is the public clash itself and the damage it can do to reputation or authority"
    if content_type == "News / report" and hook_type == "surprise":
        return "The stake is the disruption or oddity becoming big enough to matter beyond the single incident"
    if content_type == "News / report" and hook_type == "institutional stakes":
        return "The stake is whether the institution can absorb the pressure without further breakdown"

    if vertical in {"Finance", "Markets"}:
        return "The stake is money, risk, and whether readers need to adjust expectations or behavior"
    if vertical == "AI":
        return "The stake is how quickly the AI shift changes work, competition, or consumer behavior"
    if vertical == "Tech":
        return "The stake is whether the product or platform change alters how people or companies operate"
    if vertical == "Careers":
        return "The stake is job security, hiring odds, or workplace standing"
    if vertical in {"Travel", "Transportation"}:
        return "The stake is travel reliability, cost, and passenger convenience"
    if vertical in {"Retail", "Real Estate"}:
        return "The stake is consumer cost, household tradeoffs, and market pressure"
    if vertical in {"Politics", "Media"}:
        return "The stake is power, perception, and the scale of the backlash"
    return "The stake is why the story matters beyond the headline itself"


def infer_replicable_elements(headline: str, vertical: str, content_type: str, hook_type: str) -> str:
    lower = headline.lower()
    vertical = clean(vertical)
    content_type = clean(content_type)
    hook_type = clean(hook_type)

    if "why" in lower and "says" in lower:
        return "Use a recognizable authority as the story engine, pair the claim with a time-bound prediction, and translate the abstract idea into a money or lifestyle consequence"
    if "we asked" in lower:
        return "Use a disputed claim as the trigger, bring in a specific number of outside voices, and turn the piece into an adjudication rather than a simple reaction story"
    if "retired in europe" in lower:
        return "Build around a first-person transformation, compare the US with a specific overseas setting, and make cost-of-living and lifestyle tradeoffs explicit"
    if "diversion" in lower or "u-turned" in lower:
        return "Use a vivid operational incident, make the unusual repetition the hook, and keep the scene concrete enough to visualize immediately"
    if "hr" in lower and "staff" in lower:
        return "Show the internal response in plain language, tie the external controversy to employee impact, and make the organization’s handling of the issue the point"
    if "aircraft carrier" in lower or "navy" in lower:
        return "Use scale and mission importance to raise stakes, layer multiple operational problems into one narrative, and lean on scene-rich details that signal strain"

    if content_type == "Feature / personal essay":
        return "Build around a single lived experience, let the personal transformation carry the structure, and include concrete tradeoffs that make the decision feel costly"
    if content_type == "Feature / report":
        return "Use a scene-rich institutional or operational narrative, keep the pacing observational, and let the details accumulate into a bigger pattern"
    if content_type == "Breaking news / report":
        return "Lead with the immediate event, keep attribution tight, and use the headline to make the latest development unmistakable"
    if content_type == "Guide / service":
        return "Promise a direct answer or shortcut, organize around practical decision points, and make the reader payoff explicit in the headline"
    if content_type == "Report / analysis":
        return "Combine reporting detail with a visible interpretive angle, so the reader gets both the facts and why they matter"
    if content_type == "Explainer / analysis":
        return "Start from a sharp claim or trend, then move quickly to consequences, context, and what it means for the reader"
    if content_type == "News / report" and hook_type == "surprise":
        return "Use an odd or memorable incident, keep the lead image concrete, and make the unexpected element do the work"
    if content_type == "News / report" and hook_type == "conflict":
        return "Center the clash itself, identify the protagonist and antagonist quickly, and let the tension drive the summary"
    if content_type == "News / report" and hook_type == "institutional stakes":
        return "Show the institution under pressure, elevate the scale of the problem, and use the headline to signal operational strain"

    if vertical in {"Finance", "Markets"}:
        return "Connect the headline claim to a money decision, a portfolio or savings consequence, and a clear reader question about risk or return"
    if vertical == "AI":
        return "Use a named AI breakthrough or claim, then show how it changes the competitive, labor, or consumer landscape"
    if vertical == "Tech":
        return "Anchor the piece in a product, platform, or founder move and make the practical user or business impact obvious"
    if vertical == "Careers":
        return "Frame the story around career security, workplace behavior, or job search strategy so the reader sees a direct professional payoff"
    if vertical == "Health":
        return "Lead with a health risk, habit, or treatment question and make the consequence feel personal and actionable"
    if vertical in {"Travel", "Transportation"}:
        return "Use a concrete trip disruption, destination, or traveler choice and make the logistics feel vivid and immediate"
    if vertical in {"Retail", "Real Estate"}:
        return "Center the story on a household decision or market tradeoff and show what changes in cost, convenience, or lifestyle"
    if vertical in {"Politics", "Media"}:
        return "Start with a public clash, then show the power struggle, backlash, or institutional consequence that follows"
    if vertical == "Military & Defense":
        return "Use scale, hardware, and mission strain to create urgency while grounding the story in concrete operational detail"
    if vertical == "Entertainment":
        return "Pair a recognizable person with a sharp twist, then frame the story as a culture or reputation move"
    if vertical == "Law":
        return "Use the legal action or allegation as the peg, then show the concrete consequence for the people or institution involved"
    if vertical == "Education":
        return "Tie the story to schools, parents, or student outcomes and make the policy or classroom consequence visible"
    if vertical == "Food":
        return "Use a consumer-facing detail or trend, then connect it to taste, price, convenience, or habit change"
    if vertical == "Small Business":
        return "Frame the story around owner survival, margins, or operational tradeoffs, and make the business decision feel concrete"
    if vertical == "Energy":
        return "Use infrastructure, pricing, or policy pressure to show how energy decisions affect consumers or industry"
    return "Use a sharp news peg, make the consequence legible, and keep the framing tied to a clear reader payoff"


def generate_rows() -> list[dict[str, str]]:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for idx, row in enumerate(reader, start=1):
            headline = clean(row["Post Metadata (Latest) Headline"])
            vertical = clean(row["Post Metadata (Latest) Main Edit Vertical"])
            analysis = infer_frame(headline, vertical)
            rows.append(
                {
                    "story_id": str(idx),
                    "source_url": clean(row["Post Metadata (Latest) Clickable Headline"]),
                    "author_list": clean(row["Post Metadata (Latest) Author Name List"]),
                    "vertical": vertical,
                    "headline": headline,
                    "headline_word_count": str(headline_word_count(headline)),
                    "page_views": clean(row["MSN Stats Total Page Views"]).replace(",", ""),
                    "timespent_minutes": clean(row["MSN Stats Timespent Minutes"]).replace(",", ""),
                    "main_point_of_interest": infer_main_point(headline, vertical),
                    "topic_subject": infer_subject(headline, vertical),
                    "framing": analysis["framing"],
                    "angle": analysis["angle"],
                    "content_type": analysis["content_type"],
                    "tone": analysis["tone"],
                    "framing_scope_flag": analysis["framing_scope_flag"],
                    "hook_type": analysis["hook_type"],
                    "reader_promise": infer_reader_promise(headline, vertical),
                    "narrative_device": analysis["narrative_device"],
                    "stakes": infer_stakes(headline, vertical, analysis["content_type"], analysis["hook_type"]),
                    "specificity_level": analysis["specificity_level"],
                    "evidence_type": analysis["evidence_type"],
                    "audience_fit": infer_vertical_frame(vertical)[1],
                    "replicable_elements": infer_replicable_elements(headline, vertical, analysis["content_type"], analysis["hook_type"]),
                }
            )
        return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "story_id",
        "source_url",
        "author_list",
        "vertical",
        "headline",
        "headline_word_count",
        "page_views",
        "timespent_minutes",
        "main_point_of_interest",
        "topic_subject",
        "framing",
        "angle",
        "content_type",
        "tone",
        "framing_scope_flag",
        "hook_type",
        "reader_promise",
        "narrative_device",
        "stakes",
        "specificity_level",
        "evidence_type",
        "audience_fit",
        "replicable_elements",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_schema() -> None:
    schema = """# MSN Story Analysis Schema

Working rule: one story at a time. The database is now populated across all stories using a headline-only heuristic, with framing fields prioritized. All stories in this dataset are Business Insider news stories, so the analysis focuses on news framing rather than story format labels.

## Core Fields

- `main_point_of_interest`: the most reader-facing consequence, tension, comparison, or takeaway
- `topic_subject`: the factual subject matter
- `framing`: how the story is packaged or interpreted
- `angle`: the specific route into the topic and the editorial move behind it
- `content_type`: explainer, analysis, Q&A, list, feature, breaking news, etc.
- `tone`: emotional or rhetorical posture
- `framing_scope_flag`: whether the framing is broadly reusable or especially tied to one subject area
- `replicable_elements`: what can be reused in future headlines or story development

## Additional Fields

- `headline_word_count`
- `hook_type`
- `reader_promise`
- `narrative_device`
- `stakes`
- `specificity_level`
- `evidence_type`
- `audience_fit`

## Notes

- This is a headline-only analysis pass.
- The framing columns are designed to be the primary analytical layer.
- Rows with especially subject-specific framing are flagged directly in `framing_scope_flag`.
- `reader_promise` should describe what the audience comes away with, not just the headline trigger.
"""
    SCHEMA.write_text(schema, encoding="utf-8")


if __name__ == "__main__":
    rows = generate_rows()
    write_csv(rows)
    write_schema()
    print(f"Wrote {len(rows)} rows to {OUTPUT}")
