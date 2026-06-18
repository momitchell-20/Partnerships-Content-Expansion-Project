from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path("/Users/mmitchell/Desktop/coconut")
DATA_DIR = BASE_DIR / "msn-slideshow-analysis"
SOURCE = DATA_DIR / "MSN Story Audit Oct 2025 - May 2026 - all stories.csv"
OUTPUT = DATA_DIR / "story_framing_database.csv"
SCHEMA = DATA_DIR / "story_framing_schema.md"
SUMMARY = DATA_DIR / "story_framing_summary.md"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def lower(text: str) -> str:
    return clean(text).lower()


def short(text: str, limit: int = 12) -> str:
    words = re.findall(r"\b[\w'-]+\b", clean(text))
    if len(words) <= limit:
        return clean(text)
    return " ".join(words[:limit]) + "..."


def headline_word_count(headline: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", clean(headline)))


def topic_from_vertical(vertical: str, headline: str) -> str:
    v = clean(vertical)
    h = lower(headline)
    if any(k in h for k in ["settlement", "lawsuit", "court", "legal", "claims deadline", "qualifies"]):
        return "law and legal fallout"
    if any(k in h for k in ["trump", "political firestorm", "political", "davos", "president", "election", "campaign"]):
        return "politics and public conflict"
    if any(k in h for k in ["flight", "plane", "airline", "airport", "tsa", "travel", "cruise", "trip"]):
        return "travel and transportation"
    if "moved back" in h or "culture shock" in h or "repatriation" in h:
        return "real estate and housing"
    if "breakfast" in h and any(k in h for k in ["protein", "fiber", "healthy", "nutrition"]):
        return "health and wellness"
    if any(k in h for k in ["retirement", "retire", "saving for retirement", "retirement savings", "401k", "401(k)"]):
        if "europe" in h or any(k in h for k in ["relocation", "moved", "moving", "home", "housing", "rent"]):
            return "real estate and housing"
        return "personal finance and affordability"
    if any(k in h for k in ["europe", "relocation", "moved", "moving", "home", "housing", "rent"]):
        return "real estate and housing"
    if any(k in h for k in ["job", "jobs", "career", "hiring", "layoff", "unemployment", "workers", "employee", "staff"]):
        return "careers and labor"
    if any(k in h for k in ["inflation", "tariff", "rates", "federal reserve", "fed", "mortgage", "borrow", "credit card interest"]):
        return "economy and cost of living"
    if any(k in h for k in ["stock", "stocks", "market", "investor", "wall street", "earnings", "crypto"]):
        return "markets and investing"
    if re.search(r"\bai\b", h) or any(k in h for k in ["technology", "tech", "app", "platform", "product", "website", "service"]):
        return "technology and platforms"
    if any(k in h for k in ["health", "medical", "doctor", "hospital", "cancer", "disease"]):
        return "health and wellness"
    if any(k in h for k in ["bigfoot", "movie", "show", "celebrity", "entertainment", "dating", "breakup"]):
        return "entertainment and celebrity culture"
    if any(k in h for k in ["navy", "military", "fighter", "combat", "weapon", "missile", "aircraft carrier"]):
        return "military and defense"
    if any(k in h for k in ["food", "restaurant", "meal", "eat", "grocer", "supermarket"]):
        return "food and consumer habits"
    if v == "Finance":
        if "retirement" in h or "student-loan" in h or "student loan" in h or "inflation" in h or "tariff" in h:
            return "personal finance and affordability"
        return "finance"
    if v == "Markets":
        return "markets and investing"
    if v == "AI":
        return "AI and technology"
    if v == "Tech":
        return "technology and platforms"
    if v == "Careers":
        return "careers and labor"
    if v == "Health":
        return "health and wellness"
    if v in {"Travel", "Transportation"}:
        return "travel and transportation"
    if v == "Retail":
        return "retail and consumer behavior"
    if v == "Real Estate":
        return "real estate and housing"
    if v == "Military & Defense":
        return "military and defense"
    if v in {"Politics", "Media"}:
        return "politics and public conflict" if v == "Politics" else "media and public reaction"
    if v == "Economy":
        return "economy and cost of living"
    if v == "Parenting":
        return "parenting and family tradeoffs"
    if v == "Strategy":
        return "business strategy"
    if v == "News":
        return "news"
    if v == "Law":
        return "law and legal fallout"
    if v == "Education":
        return "education and schools"
    if v == "Food":
        return "food and consumer habits"
    if v == "Small Business":
        return "small business"
    if v == "Energy":
        return "energy and infrastructure"
    if v == "Entertainment":
        return "entertainment and celebrity culture"
    if v == "Sports":
        return "sports"
    if v == "Discourse":
        return "culture and discourse"
    return v.lower() or "news"


def content_type_for_frame(frame: str, headline: str, vertical: str) -> str:
    h = lower(headline)
    if frame == "authority_prediction":
        return "Explainer / analysis"
    if frame == "expert_roundup":
        return "Explainer / analysis"
    if frame == "personal_transformation":
        return "Feature / personal essay"
    if frame == "human_story_lesson":
        return "Feature / report"
    if frame == "breaking_news_fallout":
        return "Breaking news / report"
    if frame == "repeat_incident":
        return "News / report"
    if frame in {"utility_guide", "eligibility_deadline"}:
        return "Guide / service"
    if frame in {"policy_wallet_impact", "market_move", "career_security", "travel_disruption", "housing_tradeoff", "science_tech_implication", "product_platform_impact", "winners_losers", "comparison_tradeoff", "risk_warning", "trend_projection", "straight_news"}:
        return "Explainer / analysis"
    if frame in {"cultural_debate", "institutional_pressure", "insider_view", "hidden_system"}:
        return "Report / analysis"
    return "News / report"


def tone_for_frame(frame: str, headline: str) -> str:
    if frame == "authority_prediction":
        return "Provocative, speculative, debate-oriented"
    if frame == "expert_roundup":
        return "Curious, adjudicative, connective"
    if frame == "personal_transformation":
        return "Reflective, candid, practical"
    if frame == "human_story_lesson":
        return "Personal, revealing, lightly narrative"
    if frame == "breaking_news_fallout":
        return "Urgent, adversarial, high-stakes"
    if frame == "repeat_incident":
        return "Ironic, surprising, lightly dramatic"
    if frame in {"utility_guide", "eligibility_deadline"}:
        return "Helpful, practical, direct"
    if frame == "policy_wallet_impact":
        return "Practical, consequential, consumer-facing"
    if frame == "market_move":
        return "Practical, consequential, investor-facing"
    if frame == "career_security":
        return "Cautionary, practical, workforce-oriented"
    if frame == "travel_disruption":
        return "Surprised, concrete, traveler-focused"
    if frame == "housing_tradeoff":
        return "Reflective, comparative, tradeoff-oriented"
    if frame == "cultural_debate":
        return "Curious, interpretive, conversation-driven"
    if frame == "institutional_pressure":
        return "Serious, operational, strained"
    if frame == "science_tech_implication":
        return "Speculative, explanatory, consequential"
    if frame == "product_platform_impact":
        return "Explanatory, user-facing, practical"
    if frame == "winners_losers":
        return "Comparative, distributional, outcome-focused"
    if frame == "comparison_tradeoff":
        return "Comparative, evaluative, choice-oriented"
    if frame == "insider_view":
        return "Inside, revealing, managerially tense"
    if frame == "hidden_system":
        return "Explanatory, clarifying, mechanism-focused"
    if frame == "risk_warning":
        return "Cautionary, serious, alerting"
    if frame == "trend_projection":
        return "Forward-looking, interpretive, consequential"
    return "Neutral, informative"


def main_point_for_frame(frame: str, headline: str) -> str:
    h = lower(headline)
    if "blue origin" in h or "satellite launch" in h or ("launch" in h and "did not go well" in h):
        return "Launch failure"
    if "krugman" in h and "affordability" in h:
        return "Affordability policy prescription"
    if "stiglitz" in h and any(k in h for k in ["weakening", "we're just going to get worse", "we just going to get worse"]):
        return "Economic warning"
    if "dating" in h or "age-gap" in h or "65-year-olds" in h or "older men" in h:
        return "Age-gap dating"
    if "breakfast" in h and any(k in h for k in ["protein", "fiber", "healthy", "nutrition"]):
        return "Health routine"
    if frame == "authority_prediction":
        if "retirement" in h or "saving" in h:
            return "Retirement prediction"
        if "tariff" in h:
            return "Policy prediction"
        if "crypto" in h or "interest" in h or "ai disruption" in h:
            return "Claim-led future outlook"
        return "Future prediction"
    if frame == "expert_roundup":
        return "Expert reaction"
    if frame == "personal_transformation":
        return "Life-change tradeoff"
    if frame == "human_story_lesson":
        if "plane" in h and "celebrity" in h:
            return "Unexpected encounter"
        return "Personal lesson"
    if frame == "breaking_news_fallout":
        return "Breaking-news fallout"
    if frame == "repeat_incident":
        return "Repeat disruption"
    if frame == "utility_guide":
        return "Practical answer"
    if frame == "eligibility_deadline":
        return "Eligibility / deadline"
    if frame == "policy_wallet_impact":
        return "Cost-of-living impact"
    if frame == "market_move":
        return "Market consequence"
    if frame == "career_security":
        return "Career impact"
    if frame == "travel_disruption":
        return "Travel disruption"
    if frame == "housing_tradeoff":
        if "moved back" in h or "culture shock" in h or "repatriation" in h:
            return "Repatriation shock"
        return "Relocation tradeoff"
    if frame == "cultural_debate":
        return "Cultural debate"
    if frame == "institutional_pressure":
        return "Institutional strain"
    if frame == "science_tech_implication":
        return "Future implications"
    if frame == "product_platform_impact":
        return "Platform impact"
    if frame == "hidden_system":
        return "System explainer"
    if frame == "insider_view":
        return "Insider perspective"
    if frame == "winners_losers":
        return "Winners and losers"
    if frame == "comparison_tradeoff":
        return "Comparison / tradeoff"
    if frame == "trend_projection":
        return "Trend projection"
    if frame == "risk_warning":
        return "Risk warning"
    return "Current development"


def evidence_type_for_frame(frame: str, headline: str, vertical: str) -> str:
    h = lower(headline)
    if frame == "authority_prediction":
        return "expert quote"
    if frame == "expert_roundup":
        return "expert quotes"
    if frame == "personal_transformation":
        return "first-person anecdote"
    if frame == "human_story_lesson":
        return "first-person anecdote"
    if frame == "breaking_news_fallout":
        return "reporting"
    if frame == "repeat_incident":
        return "reporting"
    if frame in {"utility_guide", "eligibility_deadline"}:
        return "service reporting"
    if frame == "policy_wallet_impact":
        if any(k in h for k in ["inflation", "jobs report", "job market", "rates", "federal reserve", "mortgage bond"]):
            return "data and reporting"
        if any(k in h for k in ["student-loan", "student loan", "tariff"]):
            return "policy reporting"
        return "policy reporting"
    if frame == "market_move":
        return "market analysis"
    if frame == "career_security":
        return "reporting"
    if frame == "travel_disruption":
        return "reporting"
    if frame == "housing_tradeoff":
        return "first-person anecdote"
    if frame == "cultural_debate":
        return "reporting"
    if frame == "institutional_pressure":
        return "reporting"
    if frame == "science_tech_implication":
        return "analysis and reporting"
    if frame == "product_platform_impact":
        return "product reporting"
    if frame == "hidden_system":
        return "explainer reporting"
    if frame == "insider_view":
        return "internal documents or insider reporting"
    if frame == "winners_losers":
        return "analysis"
    if frame == "comparison_tradeoff":
        return "comparative reporting"
    if frame == "trend_projection":
        return "analysis"
    if frame == "risk_warning":
        return "analysis"
    return "reporting"


def emotional_register_for_frame(frame: str, headline: str) -> str:
    h = lower(headline)
    if frame == "authority_prediction":
        return "provocative"
    if frame == "expert_roundup":
        return "curious"
    if frame == "personal_transformation":
        return "reflective"
    if frame == "human_story_lesson":
        if "celebrity" in h or "plane" in h:
            return "surprised"
        return "personal"
    if frame == "breaking_news_fallout":
        return "urgent"
    if frame == "repeat_incident":
        return "surprised"
    if frame in {"utility_guide", "eligibility_deadline"}:
        return "practical"
    if frame == "policy_wallet_impact":
        return "concerned"
    if frame == "market_move":
        return "anxious"
    if frame == "career_security":
        return "cautious"
    if frame == "travel_disruption":
        return "surprised"
    if frame == "housing_tradeoff":
        return "reflective"
    if frame == "cultural_debate":
        return "curious"
    if frame == "institutional_pressure":
        return "serious"
    if frame == "science_tech_implication":
        return "speculative"
    if frame == "product_platform_impact":
        return "practical"
    if frame == "hidden_system":
        return "instructive"
    if frame == "insider_view":
        return "tense"
    if frame == "winners_losers":
        return "comparative"
    if frame == "comparison_tradeoff":
        return "evaluative"
    if frame == "trend_projection":
        return "forward-looking"
    if frame == "risk_warning":
        return "cautionary"
    return "neutral"


def after_says(headline: str) -> str:
    if " says " in headline.lower():
        return clean(re.split(r"\bsays\b", headline, maxsplit=1, flags=re.I)[1])
    return ""


def subject_from_headline(headline: str, vertical: str) -> str:
    h = lower(headline)
    v = clean(vertical)

    if "retired in europe" in h or ("retire" in h and "europe" in h):
        return "retirement abroad and expat cost-of-living tradeoffs"
    if "business seats on a plane" in h or ("plane" in h and "celebrity" in h):
        return "chance celebrity encounter during air travel"
    if "moved back" in h or "culture shock" in h or "repatriation" in h:
        return "repatriation and relocation shock"
    if "breakfast" in h and any(k in h for k in ["protein", "fiber", "healthy", "nutrition"]):
        return "healthy breakfast routine"
    if "gofundme" in h and "trump" in h:
        return "Ford employee fundraiser after Trump heckling"
    if "political firestorm" in h and "hr" in h and "staff" in h:
        return "Target political firestorm and HR response"
    if "settlement" in h and any(k in h for k in ["qualif", "deadline", "join"]):
        return "settlement eligibility and claims deadline"
    if "student-loan" in h and "lawsuit" in h:
        return "student-loan forgiveness lawsuit"
    if "student-loan" in h or "student loan" in h:
        return "student-loan repayment changes"
    if "tariff" in h:
        return "tariffs and consumer costs"
    if "inflation" in h:
        return "inflation and purchasing power"
    if any(k in h for k in ["federal reserve", "fed", "rate cut", "interest rate", "mortgage bond", "rates"]):
        return "interest-rate and borrowing-cost changes"
    if any(k in h for k in ["job market", "hiring", "layoff", "unemployment"]):
        return "job market and hiring conditions"
    if "basic income" in h:
        return "basic income experiment"
    if "gig work" in h or "gig economy" in h:
        return "gig work and labor flexibility"
    if "childcare" in h:
        return "working-parent childcare strain"
    if any(k in h for k in ["superrich", "wealthiest", "ultrawealthy"]):
        return "wealth migration and housing pressure"
    if "bigfoot" in h:
        return "Bigfoot documentary controversy"
    if "public breakup" in h or "breakups are still a thing" in h:
        return "public breakup culture"
    if "blue origin" in h or "satellite launch" in h or ("launch" in h and "did not go well" in h):
        return "commercial space launch failure"
    if "arrested" in h or "released after arrest" in h:
        return "public fallout after an arrest"
    if "diversion" in h or "u-turned" in h:
        return "travel disruption caused by an onboard incident"
    if "aircraft carrier" in h or "navy" in h:
        return "operational strain on a Navy ship"
    if "best ad" in h or "ad that ever ran" in h:
        return "political advertising and message strategy"
    if "we asked" in h and "what they think" in h:
        return "expert reactions to a disputed claim"
    if "why" in h and "says" in h:
        claim = after_says(headline)
        return claim or "a future claim from a high-profile figure"
    if v == "Finance":
        return "money and personal-finance consequences"
    if v == "Markets":
        return "market and investor consequences"
    if v == "AI":
        return "AI's impact on work, business, and consumers"
    if v == "Tech":
        return "technology change and its real-world effects"
    if v == "Careers":
        return "workplace security and career moves"
    if v == "Health":
        return "health risk, habits, and medical decisions"
    if v in {"Travel", "Transportation"}:
        return "trip disruptions and travel choices"
    if v in {"Retail", "Real Estate"}:
        return "consumer and housing tradeoffs"
    if v in {"Politics", "Media"}:
        return "public conflict and fallout"
    if v == "Military & Defense":
        return "military operations and readiness"
    if v == "Economy":
        return "household pressure and cost of living"
    if v == "Strategy":
        return "business strategy and execution"
    if v == "Discourse":
        return "cultural debate and generational tension"
    if v == "News":
        return "a current news development"
    if v == "Law":
        return "legal consequences and institutional fallout"
    if v == "Education":
        return "school and student consequences"
    if v == "Food":
        return "food choices, cost, and convenience"
    if v == "Small Business":
        return "small-business margins and survival"
    if v == "Energy":
        return "energy prices and infrastructure pressure"
    if v == "Entertainment":
        return "celebrity attention and cultural reaction"
    if v == "Sports":
        return "sports developments and fan interest"
    return short(headline, 10)


def classify_frame(headline: str, vertical: str) -> str:
    h = lower(headline)
    if "why" in h and "says" in h:
        return "authority_prediction"
    if "we asked" in h or ("expert" in h and "what they think" in h):
        return "expert_roundup"
    if h.startswith(("i ", "my ", "we ")):
        if "sold everything" in h or "retired in europe" in h:
            return "personal_transformation"
        if "moved back" in h or "culture shock" in h or "repatriation" in h:
            return "housing_tradeoff"
        if "plane" in h and "celebrity" in h:
            return "human_story_lesson"
        if "breakfast" in h and any(k in h for k in ["protein", "fiber", "healthy", "nutrition"]):
            return "utility_guide"
        if "advise" in h or "advice" in h:
            return "utility_guide"
        if any(k in h for k in ["moved", "relocated", "retired", "quit", "divorce", "traveled", "travel", "flight", "cruise"]):
            return "human_story_lesson"
    if "arrested" in h or "released after arrest" in h:
        return "breaking_news_fallout"
    if "diversion" in h or "u-turned" in h or "another" in h and "again" in h:
        return "repeat_incident"
    if "best ad" in h or "ad that ever ran" in h:
        return "cultural_debate"
    if any(k in h for k in ["how to", "what to know", "what you need to know", "guide", "tips", "best ", "top "]):
        return "utility_guide"
    if "settlement" in h and any(k in h for k in ["qualif", "deadline", "join"]):
        return "eligibility_deadline"
    if any(k in h for k in ["tariff", "inflation", "student-loan", "student loan", "rate cut", "federal reserve", "interest rate", "mortgage bond", "job market", "hiring", "layoff", "basic income", "gig work", "childcare"]):
        return "policy_wallet_impact"
    if any(k in h for k in ["affordability", "economic", "economy", "cost of living"]):
        return "policy_wallet_impact"
    if any(k in h for k in ["stocks", "market", "investor", "crypto", "wall street", "earnings"]):
        return "market_move"
    if any(k in h for k in ["job", "career", "unemployment", "older workers", "workers over 80", "hiring"]):
        return "career_security"
    if any(k in h for k in ["flight", "cruise", "travel", "airline", "trip", "u-turned", "diversion", "plane"]):
        return "travel_disruption"
    if any(k in h for k in ["retired in europe", "europe", "real estate", "rent", "home", "housing", "moving", "relocation"]):
        return "housing_tradeoff"
    if any(k in h for k in ["bigfoot", "public breakup", "breakup", "ad that ever ran", "documentary", "culture", "celebrity"]):
        return "cultural_debate"
    if any(k in h for k in ["navy", "aircraft carrier", "military", "weapons", "memo", "employees", "hr", "staff"]):
        return "institutional_pressure"
    if re.search(r"\bai\b", h) or any(k in h for k in ["tech", "blue origin", "launch", "science", "research", "power demands"]):
        return "science_tech_implication"
    if re.search(r"\b(platform|app|product|website|service)\b", h) or "personal assistant" in h:
        return "product_platform_impact"
    if "who wins" in h or "who loses" in h or "winner" in h or "loser" in h:
        return "winners_losers"
    if any(k in h for k in ["vs ", "versus", "pros and cons", "compare", "comparison", "better", "tradeoff"]):
        return "comparison_tradeoff"
    if any(k in h for k in ["memo", "internal", "behind the scenes", "inside", "staff", "hr"]):
        return "insider_view"
    if any(k in h for k in ["how ", "what happened when", "what happens when", "explained", "here's what happened", "here is what happened"]):
        return "hidden_system"
    if any(k in h for k in ["could", "risk", "warning", "danger", "ugly", "worse", "immediate"]):
        return "risk_warning"
    if "future" in h or "next " in h or "by 20" in h:
        return "trend_projection"
    if h.startswith(("why ", "how ", "what ", "here's ", "here is ")):
        return "straight_news"
    return "straight_news"


FRAME_LIBRARY = {
    "authority_prediction": {
        "framing": "Authority-backed future prediction",
        "angle": "Use a recognizable authority to turn a forecast into a debate about practical consequences.",
        "reader_motivation": "To judge whether the prediction is credible and what it means.",
        "replicable_element": "Pair a recognizable authority with a time-bound prediction and translate it into concrete consequences.",
        "notes": "Broad; strongest in finance, AI, tech, and personal-finance coverage.",
    },
    "expert_roundup": {
        "framing": "Expert claim check",
        "angle": "Use outside voices to validate, challenge, or complicate a provocative claim.",
        "reader_motivation": "To see whether experts agree or disagree.",
        "replicable_element": "Use a disputed claim as the hook, then adjudicate it with multiple voices.",
        "notes": "Broad; works whenever the newsroom can quickly assemble outside expertise.",
    },
    "personal_transformation": {
        "framing": "First-person transformation tradeoff story",
        "angle": "Use a lived experience to make a major life change feel concrete.",
        "reader_motivation": "To see the tradeoffs behind a major life decision.",
        "replicable_element": "Follow one person's experience to illuminate a bigger tradeoff.",
        "notes": "Broad; especially strong in lifestyle, travel, housing, and retirement coverage.",
    },
    "human_story_lesson": {
        "framing": "Human-interest lesson framing",
        "angle": "Let one person's story stand in for a broader lesson or trend.",
        "reader_motivation": "To see how a personal experience maps onto a larger reality.",
        "replicable_element": "Use a personal anecdote to make a macro trend legible.",
        "notes": "Broad; useful when the human angle is the real hook.",
    },
    "breaking_news_fallout": {
        "framing": "Breaking-news fallout framing",
        "angle": "Lead with the latest event, then widen to the consequences and response.",
        "reader_motivation": "To get the immediate update and understand the fallout.",
        "replicable_element": "Start with a public confrontation or arrest and quickly move to response and consequences.",
        "notes": "Broad; strongest in politics, media, and public-figure coverage.",
    },
    "repeat_incident": {
        "framing": "Repeat-disruption framing",
        "angle": "Make a weird incident feel newsworthy by showing it happened again.",
        "reader_motivation": "To understand why the strange event happened again and whether it signals a pattern.",
        "replicable_element": "Use recurrence as the hook so oddity becomes pattern.",
        "notes": "Subject-specific; strongest in transportation, aviation, and operations coverage.",
    },
    "utility_guide": {
        "framing": "Utility / decision-aid framing",
        "angle": "Promise a direct answer, shortcut, or eligibility check.",
        "reader_motivation": "To get practical next steps quickly.",
        "replicable_element": "Make the payoff explicit and deliver it fast.",
        "notes": "Broad.",
    },
    "eligibility_deadline": {
        "framing": "Eligibility-and-deadline framing",
        "angle": "Turn a policy or legal change into a simple who-qualifies / what-to-do question.",
        "reader_motivation": "To see whether they qualify and what action to take.",
        "replicable_element": "Use a cutoff or eligibility test to give readers a practical reason to click.",
        "notes": "Broad; especially effective in consumer, policy, and finance stories with a hard cutoff.",
    },
    "policy_wallet_impact": {
        "framing": "Policy-to-wallet framing",
        "angle": "Translate policy or market change into household cost or affordability impact.",
        "reader_motivation": "To know how the change hits their money.",
        "replicable_element": "Turn an abstract policy or market shift into a household consequence.",
        "notes": "Broad; strongest in finance, economy, policy, and consumer coverage.",
    },
    "market_move": {
        "framing": "Market consequence framing",
        "angle": "Connect the development to price action and investor positioning.",
        "reader_motivation": "To understand what it means for markets or a portfolio.",
        "replicable_element": "Frame the event through winners, losers, and investor expectations.",
        "notes": "Subject-specific: finance and markets.",
    },
    "career_security": {
        "framing": "Career-security framing",
        "angle": "Center the labor-market or workplace consequences.",
        "reader_motivation": "To judge job or hiring risk.",
        "replicable_element": "Tie the story to hiring, layoffs, or job-search odds.",
        "notes": "Broad; especially strong in careers and labor coverage.",
    },
    "travel_disruption": {
        "framing": "Travel-disruption framing",
        "angle": "Keep the logistics problem concrete and immediate.",
        "reader_motivation": "To understand delays, costs, and trip consequences.",
        "replicable_element": "Use a vivid operational hiccup that readers can picture.",
        "notes": "Subject-specific: travel and transportation.",
    },
    "housing_tradeoff": {
        "framing": "Housing / relocation tradeoff framing",
        "angle": "Compare places or living situations through the lens of cost and quality of life.",
        "reader_motivation": "To weigh whether the move or housing choice is worth it.",
        "replicable_element": "Use the move or home decision to illuminate a cost-of-living tradeoff.",
        "notes": "Broad; especially strong in real estate, relocation, and retirement stories.",
    },
    "cultural_debate": {
        "framing": "Cultural-debate framing",
        "angle": "Use one story to surface a larger social or generational argument.",
        "reader_motivation": "To understand what the story says about the culture moment.",
        "replicable_element": "Use a concrete anecdote to surface a broader debate.",
        "notes": "Broad; especially strong in media, entertainment, and discourse coverage.",
    },
    "institutional_pressure": {
        "framing": "Institution-under-pressure framing",
        "angle": "Layer concrete operational problems to show strain at scale.",
        "reader_motivation": "To see how a major institution is handling pressure.",
        "replicable_element": "Use scale, strain, and concrete problems to raise stakes.",
        "notes": "Subject-specific: strongest in military, corporate, and public-institution coverage.",
    },
    "science_tech_implication": {
        "framing": "Science/tech implication framing",
        "angle": "Translate technical change into practical consequences.",
        "reader_motivation": "To understand what the development changes about the future.",
        "replicable_element": "Turn a technical advance or failure into an implications story.",
        "notes": "Broad; strongest in AI, tech, science, and space coverage.",
    },
    "product_platform_impact": {
        "framing": "Product/platform impact framing",
        "angle": "Translate a product move into user or business consequences.",
        "reader_motivation": "To know what changes for users or businesses.",
        "replicable_element": "Connect a product change to real-world usage or business impact.",
        "notes": "Broad; strongest in tech and platform coverage.",
    },
    "hidden_system": {
        "framing": "Hidden-system framing",
        "angle": "Pull back the curtain on a process, pipeline, or rule.",
        "reader_motivation": "To understand how a complicated system actually works.",
        "replicable_element": "Explain the mechanism, not just the event.",
        "notes": "Broad; strongest when the process is opaque to readers.",
    },
    "insider_view": {
        "framing": "Insider / behind-the-scenes framing",
        "angle": "Reveal internal thinking, strategy, or backstage reaction.",
        "reader_motivation": "To see what people inside the system know that outsiders do not.",
        "replicable_element": "Use internal voices or documents to expose the logic behind the move.",
        "notes": "Broad; strongest in business, politics, and workplace stories with access.",
    },
    "winners_losers": {
        "framing": "Winners-and-losers framing",
        "angle": "Show how one change creates uneven outcomes.",
        "reader_motivation": "To find out who gains and who loses.",
        "replicable_element": "Show the distributional effect of a policy or market move.",
        "notes": "Broad; especially useful in policy, business, housing, and labor coverage.",
    },
    "comparison_tradeoff": {
        "framing": "Comparison / tradeoff framing",
        "angle": "Use contrast to make the choice legible.",
        "reader_motivation": "To compare paths, places, or options.",
        "replicable_element": "Set up a sharp comparison, then make the tradeoffs concrete.",
        "notes": "Broad; works well in housing, travel, consumer, and career coverage.",
    },
    "trend_projection": {
        "framing": "Trend projection framing",
        "angle": "Use a long-range shift to shape expectations about what comes next.",
        "reader_motivation": "To understand where a trend is headed.",
        "replicable_element": "Forecast the likely consequence of a change before it lands fully.",
        "notes": "Broad; strongest in finance, AI, tech, and labor coverage.",
    },
    "risk_warning": {
        "framing": "Risk-warning framing",
        "angle": "Surface the downside or hidden risk before it hits.",
        "reader_motivation": "To avoid a bad outcome or understand the downside.",
        "replicable_element": "Quantify the common concern and make the consequence concrete.",
        "notes": "Broad.",
    },
    "straight_news": {
        "framing": "Straight-news framing",
        "angle": "Use a clean news peg and explain the immediate consequence.",
        "reader_motivation": "To understand the latest development and why it matters.",
        "replicable_element": "Lead with the concrete event, then spell out the consequence.",
        "notes": "Broad fallback.",
    },
}


def render_row(headline: str, vertical: str) -> dict[str, str]:
    frame = classify_frame(headline, vertical)
    subject = subject_from_headline(headline, vertical)
    topic = topic_from_vertical(vertical, headline)
    spec = FRAME_LIBRARY[frame]
    content_type = content_type_for_frame(frame, headline, vertical)
    tone = tone_for_frame(frame, headline)
    evidence_type = evidence_type_for_frame(frame, headline, vertical)
    emotional_register = emotional_register_for_frame(frame, headline)
    length = headline_word_count(headline)

    main_point = main_point_for_frame(frame, headline)

    return {
        "Headline": clean(headline),
        "Main Point of Interest": main_point,
        "Subject": subject,
        "Topic": topic,
        "Framing": spec["framing"],
        "Angle": spec["angle"],
        "Content Type": content_type,
        "Tone": tone,
        "Evidence Type": evidence_type,
        "Emotional Register": emotional_register,
        "Headline Length": str(length),
        "Reader Motivation": spec["reader_motivation"],
        "Replicable Element": spec["replicable_element"],
        "Notes": spec["notes"],
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            headline = clean(row["Post Metadata (Latest) Headline"])
            vertical = clean(row["Post Metadata (Latest) Main Edit Vertical"])
            rows.append(render_row(headline, vertical))
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    fields = [
        "Headline",
        "Main Point of Interest",
        "Subject",
        "Topic",
        "Framing",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_schema() -> None:
    SCHEMA.write_text(
        """# MSN Story Framing Schema

This database focuses on framing, angle, and reader appeal rather than topic taxonomy.

## Columns

- `Headline`: the original Business Insider headline
- `Main Point of Interest`: the normalized reader-interest category
- `Subject`: the specific story subject or angle driver
- `Topic`: the broader subject-matter bucket, based only on topic/subject and not framing
- `Framing`: the editorial frame or pattern

## Working Rule

Two stories can cover different subjects and still use the same framing pattern. The database should capture the pattern, not just the topic.

Column B should use a controlled category list, and column E should use consistent framing labels.
""",
        encoding="utf-8",
    )


def write_summary(rows: list[dict[str, str]]) -> None:
    main_point_counts = Counter(row["Main Point of Interest"] for row in rows)
    topic_counts = Counter(row["Topic"] for row in rows)
    framing_counts = Counter(row["Framing"] for row in rows)
    replicable_counts = Counter(row["Replicable Element"] for row in rows)

    broad_frames = [row for row in rows if row["Notes"].startswith("Broad")]
    broad_counts = Counter(row["Framing"] for row in broad_frames)

    top_formulas = [
        "Authority-backed forecast -> Use a recognizable figure, a time-bound claim, and a practical consequence.",
        "Expert check -> Put a disputed claim in front of outside voices and let the disagreement do the work.",
        "First-person tradeoff -> Follow one person's life change and make the hidden costs explicit.",
        "Policy-to-wallet -> Translate a policy or market change into direct household impact.",
        "Utility/eligibility -> Give the reader a shortcut, deadline, or action item they can use immediately.",
        "Winners and losers -> Show who gains and who loses, then make the distribution feel concrete.",
        "Insider/backstage -> Reveal how people inside the system think and decide.",
        "Repeat oddity -> Make recurrence the hook so a strange incident becomes a pattern.",
    ]

    lines = []
    lines.append("# MSN Story Framing Summary")
    lines.append("")
    lines.append("## Most Common Main Point Categories")
    for main_point, count in main_point_counts.most_common(10):
        lines.append(f"- {main_point}: {count}")
    lines.append("")
    lines.append("## Most Common Broad Topics")
    for topic, count in topic_counts.most_common(10):
        lines.append(f"- {topic}: {count}")
    lines.append("")
    lines.append("## Most Common Framing Patterns")
    for framing, count in framing_counts.most_common(10):
        lines.append(f"- {framing}: {count}")
    lines.append("")
    lines.append("## Strongest Repeatable Editorial Frameworks")
    for framing, count in broad_counts.most_common(8):
        example = next(row for row in rows if row["Framing"] == framing)
        lines.append(f"- {framing}: {count} stories")
        lines.append(f"  - Replicable element: {example['Replicable Element']}")
        lines.append(f"  - Notes: {example['Notes']}")
    lines.append("")
    lines.append("## Actionable Story Formulas")
    for item in top_formulas:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Most Repeated Replicable Elements")
    for element, count in replicable_counts.most_common(8):
        lines.append(f"- {element}: {count}")
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    rows = build_rows()
    write_csv(rows)
    write_schema()
    write_summary(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT}")
