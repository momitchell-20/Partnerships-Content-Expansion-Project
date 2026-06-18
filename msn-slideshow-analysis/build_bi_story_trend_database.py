from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit, urlunsplit


BASE_DIR = Path("/Users/mmitchell/Desktop/coconut")
DATA_DIR = BASE_DIR / "partnerships-peeler" / "msn-slideshow-analysis"
DEFAULT_SOURCE = Path("/Users/mmitchell/Downloads/evergreen stories pull 2026-06-09T1228.csv")
DEFAULT_OUTPUT = DATA_DIR / "bi_story_trend_database.csv"
DEFAULT_SCHEMA = DATA_DIR / "bi_story_trend_schema.md"
DEFAULT_SUMMARY = DATA_DIR / "bi_story_trend_summary.md"


IGNORED_SOURCE_TAGS = {
    "ai generated",
    "as told to",
    "bi graphics",
    "bi select",
    "bi prime",
    "bi-transpo",
    "bi-prime",
    "business visual features",
    "contributor",
    "contributor 2021",
    "evergreen story",
    "features",
    "freelancer",
    "freelancer-le",
    "insider news",
    "news uk",
    "pyramid",
    "review",
    "reviews",
    "trending news holiday save 2024",
    "trending uk",
    "yahooadd",
}


TOPIC_LABELS = {
    "ai_and_automation": "AI and automation",
    "capital_markets_and_fundraising": "capital markets and fundraising",
    "careers_and_labor": "careers and labor",
    "crime_and_safety": "crime and safety",
    "education_and_family": "education and family",
    "electric_vehicles_and_transport": "electric vehicles and transport",
    "energy_and_infrastructure": "energy and infrastructure",
    "entertainment_and_culture": "entertainment and culture",
    "health_and_wellness": "health and wellness",
    "history_and_explainer": "history and explainer",
    "legal_and_regulatory": "legal and regulatory",
    "lifestyle_and_relationships": "lifestyle and relationships",
    "media_and_public_figures": "media and public figures",
    "military_and_defense": "military and defense",
    "personal_finance_and_affordability": "personal finance and affordability",
    "politics_and_public_conflict": "politics and public conflict",
    "real_estate_and_housing": "real estate and housing",
    "retail_and_shopping": "retail and shopping",
    "science_and_research": "science and research",
    "space_and_aerospace": "space and aerospace",
    "sports_and_fandom": "sports and fandom",
    "travel_and_transportation": "travel and transportation",
    "business_strategy_and_companies": "business strategy and companies",
    "consumer_tech_and_platforms": "consumer tech and platforms",
    "food_and_consumer_habits": "food and consumer habits",
    "other": "other",
}


MAIN_POINT_LABELS = {
    "current development": "Current development",
    "future implications": "Future implications",
    "market consequence": "Market consequence",
    "institutional strain": "Institutional strain",
    "cost-of-living impact": "Cost-of-living impact",
    "career impact": "Career impact",
    "relocation tradeoff": "Relocation tradeoff",
    "personal lesson": "Personal lesson",
    "travel disruption": "Travel disruption",
    "public conflict": "Public conflict",
    "utility payoff": "Utility payoff",
    "consumer decision": "Consumer decision",
    "comparison tradeoff": "Comparison tradeoff",
    "health outcome": "Health outcome",
    "legal fallout": "Legal fallout",
    "business consequence": "Business consequence",
    "cultural reaction": "Cultural reaction",
    "investor focus": "Investor focus",
}


FRAMING_SCOPE_MAP = {
    "ai_and_automation": "Broad, especially strong in AI, tech, and workplace coverage",
    "capital_markets_and_fundraising": "Broad, especially strong in finance, markets, and startup coverage",
    "careers_and_labor": "Broad, especially strong in jobs, hiring, and workplace coverage",
    "crime_and_safety": "Broad, especially strong in public-safety and legal coverage",
    "education_and_family": "Broad, especially strong in education and parenting coverage",
    "electric_vehicles_and_transport": "Broad, especially strong in EV and transport coverage",
    "energy_and_infrastructure": "Broad, especially strong in energy and infrastructure coverage",
    "entertainment_and_culture": "Broad, especially strong in celebrity and culture coverage",
    "health_and_wellness": "Broad, especially strong in health and wellness coverage",
    "history_and_explainer": "Broad, especially strong in explainer and heritage coverage",
    "legal_and_regulatory": "Broad, especially strong in legal and regulatory coverage",
    "lifestyle_and_relationships": "Broad, especially strong in lifestyle and relationship coverage",
    "media_and_public_figures": "Broad, especially strong in media and public-figure coverage",
    "military_and_defense": "Subject-specific: military and defense",
    "personal_finance_and_affordability": "Broad, especially strong in finance and personal-money coverage",
    "politics_and_public_conflict": "Broad, especially strong in politics and public-conflict coverage",
    "real_estate_and_housing": "Broad, especially strong in housing and relocation coverage",
    "retail_and_shopping": "Broad, especially strong in retail and consumer coverage",
    "science_and_research": "Broad, especially strong in science and innovation coverage",
    "space_and_aerospace": "Broad, especially strong in space and aerospace coverage",
    "sports_and_fandom": "Broad, especially strong in sports coverage",
    "travel_and_transportation": "Broad, especially strong in travel and transportation coverage",
    "business_strategy_and_companies": "Broad, especially strong in company strategy coverage",
    "consumer_tech_and_platforms": "Broad, especially strong in consumer tech and platform coverage",
    "food_and_consumer_habits": "Broad, especially strong in food and consumer coverage",
    "other": "Broad, reusable",
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def lower(text: str) -> str:
    return clean(text).lower()


def canonicalize_url(source_url: str) -> str:
    cleaned = clean(source_url)
    if not cleaned:
        return ""
    parsed = urlsplit(cleaned)
    normalized = parsed._replace(query="", fragment="")
    return urlunsplit(normalized).rstrip("/")


def split_tags(text: str) -> list[str]:
    if not text:
        return []
    items = []
    for part in str(text).split("|"):
        item = clean(part)
        if item:
            items.append(item)
    return items


def contains_term(text: str, term: str) -> bool:
    text = lower(text)
    term = lower(term)
    if not term:
        return False
    if " " in term or len(term) <= 3 or re.search(r"[^\w]", term):
        return re.search(rf"\b{re.escape(term)}\b", text) is not None
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def has_any(text: str, terms: list[str]) -> bool:
    return any(contains_term(text, term) for term in terms)


def normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for tag in tags:
        cleaned = lower(tag)
        if not cleaned or cleaned in IGNORED_SOURCE_TAGS:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            normalized.append(tag.strip())
    return normalized


def pipe_join(values: list[str]) -> str:
    return "|".join(v for v in (clean(v) for v in values) if v)


def headline_word_count(headline: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", clean(headline)))


def slug_from_url(source_url: str) -> str:
    slug = clean(source_url).rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ")


def normalize_headline(raw_headline: str, source_url: str) -> str:
    headline = clean(raw_headline)
    if not headline:
        return clean(slug_from_url(source_url)).title()

    source_slug = slug_from_url(source_url)
    comparison = re.sub(r"[^a-z0-9]+", "", headline.lower())
    source_comparison = re.sub(r"[^a-z0-9]+", "", source_slug.lower())
    if comparison and comparison == source_comparison and ("-" in headline or " " not in headline):
        return source_slug.title()
    return headline


def short(text: str, limit: int = 14) -> str:
    words = re.findall(r"\b[\w'-]+\b", clean(text))
    if len(words) <= limit:
        return clean(text)
    return " ".join(words[:limit]) + "..."


def get_text_bundle(headline: str, tags: list[str], source_url: str) -> str:
    return " ".join([lower(headline), lower(" ".join(tags)), lower(source_url)])


def infer_topic_cluster(headline: str, tags: list[str], source_url: str) -> str:
    text = get_text_bundle(headline, tags, source_url)
    headline_text = lower(headline)

    if has_any(text, ["starlink"]) and has_any(text, ["airline", "airlines", "flight", "flights", "in-flight", "wifi", "internet"]):
        return "travel_and_transportation"
    if has_any(headline_text, ["daily schedule", "spouse history", "relationship timeline", "private jet", "inside the ceo", "look inside", "love-hate relationship", "who is", "paypal mafia", "members are now", "where its members are now"]):
        return "media_and_public_figures"

    if has_any(text, ["spacex", "starship", "saturn v", "apollo", "nasa", "rocket", "launch", "space", "starlink"]):
        return "space_and_aerospace"
    if has_any(text, ["tesla", "electric car", "ev", "model y", "cybertruck", "byd", "xiaomi", "lucid", "rivian"]):
        return "electric_vehicles_and_transport"
    if has_any(text, ["ipo", "funding", "valuation", "revenue", "profit", "earnings", "market cap", "capital raise", "venture", "round"]):
        return "capital_markets_and_fundraising"
    if has_any(text, ["retirement", "401k", "401(k)", "saving", "savings", "money", "inflation", "rates", "mortgage", "affordability", "cost of living", "debt", "paycheck", "budget"]):
        return "personal_finance_and_affordability"
    if has_any(text, ["job", "career", "layoff", "hiring", "worker", "workers", "employee", "employees", "workplace", "recruiter", "salary", "union"]):
        return "careers_and_labor"
    if has_any(text, ["real estate", "housing", "rent", "house", "home", "apartment", "property", "moving", "relocation", "assisted living"]):
        return "real_estate_and_housing"
    if has_any(text, ["flight", "airline", "airport", "travel", "cruise", "trip", "tsa", "train", "commute", "transport", "aviation", "jet", "plane"]):
        return "travel_and_transportation"
    if has_any(text, ["health", "medical", "doctor", "hospital", "cancer", "diet", "nutrition", "workout", "fitness", "wellness"]):
        return "health_and_wellness"
    if has_any(text, ["store", "retail", "shopping", "consumer", "price", "buy", "product", "amazon", "costco", "walmart", "target"]):
        return "retail_and_shopping"
    if has_any(text, ["politics", "election", "trump", "biden", "white house", "president", "campaign", "congress", "don lemon", "ice protest"]):
        return "politics_and_public_conflict"
    if has_any(text, ["arrest", "lawsuit", "court", "legal", "settlement", "claim", "charges", "attorney", "silence"]):
        return "legal_and_regulatory"
    if has_any(text, ["celebrity", "movie", "music", "tv", "television", "relationship", "marriage", "dating", "breakup", "grimes"]):
        return "entertainment_and_culture"
    if has_any(text, ["ai", "artificial intelligence", "chatbot", "grok", "openai", "xai", "machine learning", "automation"]):
        return "ai_and_automation"
    if has_any(text, ["twitter", "x money", "platform", "app", "software", "website", "social media", "chatbot"]):
        return "consumer_tech_and_platforms"
    if has_any(text, ["navy", "military", "defense", "weapon", "weaponry", "missile", "fighter", "aircraft carrier"]):
        return "military_and_defense"
    if has_any(text, ["science", "research", "data", "study", "satellite", "biology", "physics", "chemistry"]):
        return "science_and_research"
    if has_any(text, ["food", "fast food", "restaurant", "meal", "grocer", "grocery", "eat", "diet"]):
        return "food_and_consumer_habits"
    if has_any(text, ["ad", "advertising", "marketing", "brand", "business strategy", "company", "ceo", "startup"]):
        return "business_strategy_and_companies"
    if has_any(text, ["history", "origin", "timeline", "explained", "what is", "who is"]):
        return "history_and_explainer"
    if has_any(text, ["parent", "kids", "family", "child", "children", "married", "wife", "husband"]):
        return "education_and_family"
    if has_any(text, ["sports", "athlete", "game", "world cup", "team", "nfl", "nba", "soccer"]):
        return "sports_and_fandom"
    return "other"


def infer_primary_entity(headline: str, tags: list[str]) -> tuple[str, str, list[str]]:
    text = get_text_bundle(headline, tags, "")
    headline_lower = lower(headline)
    normalized_tags = [lower(tag) for tag in tags]
    candidate_entities: list[str] = []

    def add(entity: str) -> None:
        if entity and entity not in candidate_entities:
            candidate_entities.append(entity)

    if has_any(headline_lower, ["x money"]):
        add("X")
    elif has_any(headline_lower, ["starlink", "spacex", "starship", "launch", "rocket", "nasa"]):
        add("SpaceX")
    elif has_any(headline_lower, ["tesla", "ev", "model y", "cybertruck", "electric car", "autopilot"]):
        add("Tesla")
    elif has_any(headline_lower, ["grok", "xai", "artificial intelligence", "chatbot", "ai"]):
        add("xAI")
    elif has_any(headline_lower, ["twitter", "platform", "social media", "app"]):
        add("X")
    elif has_any(headline_lower, ["elon musk", "musk"]):
        add("Elon Musk")
    elif has_any(text, ["elon musk", "musk", "tesla", "spacex", "starlink", "xai", "x money", "x.com", "twitter"]):
        if has_any(text, ["spacex", "starship", "launch", "rocket", "nasa", "space", "starlink"]):
            add("SpaceX")
        elif has_any(text, ["tesla", "ev", "model y", "cybertruck", "electric car", "autopilot"]):
            add("Tesla")
        elif has_any(text, ["grok", "xai", "artificial intelligence", "chatbot", "ai"]):
            add("xAI")
        elif has_any(text, ["twitter", "x money", "platform", "social media", "app"]):
            add("X")
        else:
            add("Elon Musk")
    if has_any(text, ["donald trump", "trump"]):
        add("Donald Trump")
    if has_any(text, ["don lemon"]):
        add("Don Lemon")
    if has_any(text, ["grimes"]):
        add("Grimes")
    if has_any(text, ["openai"]):
        add("OpenAI")
    if has_any(text, ["nvidia"]):
        add("Nvidia")
    if has_any(text, ["byd"]):
        add("BYD")
    if has_any(text, ["xiaomi"]):
        add("Xiaomi")
    if has_any(text, ["amazon"]):
        add("Amazon")
    if has_any(text, ["costco"]):
        add("Costco")
    if has_any(text, ["target"]):
        add("Target")
    if has_any(text, ["walmart"]):
        add("Walmart")
    if has_any(text, ["nasa"]):
        add("NASA")
    if has_any(text, ["spacex"]) and not has_any(text, ["elon musk", "musk"]):
        add("SpaceX")

    if not candidate_entities:
        for tag in normalized_tags:
            if tag in {"elon musk", "tesla", "spacex", "xai", "x", "twitter", "grimes", "trump", "donald trump"}:
                add(tag.title())
                break

    primary = candidate_entities[0] if candidate_entities else ""
    secondary = candidate_entities[1:]

    if not primary:
        return "", "", secondary

    if primary in {"Elon Musk", "Donald Trump", "Don Lemon", "Grimes"}:
        if has_any(text, ["wife", "husband", "marriage", "spouse", "kids", "family", "relationship", "dating", "breakup", "house", "home", "daily schedule", "routine"]):
            role = "private_life"
        elif has_any(text, ["says", "thinks", "predicts", "wants", "told", "claimed"]):
            role = "quoted_voice"
        else:
            role = "public_figure"
    elif primary in {"SpaceX", "Tesla", "xAI", "X", "OpenAI", "Nvidia", "BYD", "Xiaomi", "Amazon", "Costco", "Target", "Walmart", "NASA"}:
        role = "organizational_actor"
    else:
        role = "primary_subject"

    return primary, role, secondary


def infer_main_point(headline: str, topic_cluster: str, entity_role: str) -> str:
    text = lower(headline)

    if has_any(text, ["arrest", "released after arrest", "will not be silenced"]):
        return "Public conflict"
    if has_any(text, ["lawsuit", "settlement", "court", "claims", "attorney", "silence"]):
        return "Legal fallout"
    if has_any(text, ["ipo", "revenue", "profit", "earnings", "funding", "valuation", "market cap", "shares"]):
        return "Market consequence"
    if has_any(text, ["retirement", "saving", "savings", "money", "inflation", "mortgage", "affordability", "budget", "paycheck"]):
        return "Cost-of-living impact"
    if has_any(text, ["job", "hiring", "layoff", "worker", "workers", "career", "workplace", "salary"]):
        return "Career impact"
    if has_any(text, ["moving", "relocation", "home", "housing", "rent", "assisted living", "house", "apartment"]):
        return "Relocation tradeoff"
    if has_any(text, ["flight", "airport", "airline", "travel", "cruise", "trip", "tsa"]):
        return "Travel disruption"
    if has_any(text, ["health", "medical", "diet", "nutrition", "workout", "fitness", "wellness"]):
        return "Health outcome"
    if has_any(text, ["how to", "what to know", "best ", "top ", "guide", "tips", "what is", "who is"]):
        return "Utility payoff"
    if has_any(text, ["versus", "compare", "compares", "compared", "comparison"]):
        return "Comparison tradeoff"
    if topic_cluster == "entertainment_and_culture":
        return "Cultural reaction"
    if topic_cluster == "business_strategy_and_companies":
        return "Business consequence"
    if topic_cluster == "space_and_aerospace":
        return "Future implications"
    if topic_cluster == "politics_and_public_conflict":
        return "Public conflict"
    if topic_cluster == "personal_finance_and_affordability":
        return "Cost-of-living impact"
    if topic_cluster == "careers_and_labor":
        return "Career impact"
    if topic_cluster == "real_estate_and_housing":
        return "Relocation tradeoff"
    if topic_cluster == "travel_and_transportation":
        return "Travel disruption"
    if topic_cluster == "capital_markets_and_fundraising":
        return "Investor focus"
    if entity_role == "private_life":
        return "Personal lesson"
    return "Current development"


def infer_framing(headline: str, topic_cluster: str, main_point: str) -> tuple[str, str, str, str, str, str]:
    text = lower(headline)

    if re.match(r"^why .+ says .+", text):
        return (
            "authority-backed forecast",
            "Explainer / analysis",
            "Provocative, speculative, debate-oriented",
            "authority quote",
            "prediction",
            "expert quote",
        )
    if text.startswith("we asked ") or "we asked " in text and "what they think" in text:
        return (
            "expert check",
            "Explainer / analysis",
            "Curious, adjudicative, connective",
            "expert consensus check",
            "multi-voice contrast",
            "expert quotes",
        )
    if has_any(text, ["how to", "what to know", "best ", "top ", "guide", "tips", "what is", "who is"]):
        return (
            "utility / decision-aid framing",
            "Guide / service",
            "Helpful, practical, direct",
            "utility",
            "service promise",
            "mixed",
        )
    if has_any(text, ["arrest", "released after arrest", "will not be silenced", "lawsuit", "settlement", "court", "claims", "attorney"]):
        return (
            "conflict / fallout framing",
            "Breaking news / report",
            "Urgent, adversarial, high-stakes",
            "conflict",
            "escalation",
            "reporting",
        )
    if has_any(text, ["launch", "satellite", "rocket", "starship", "nasa", "space", "starlink"]):
        return (
            "science/tech implication framing",
            "Explainer / analysis",
            "Speculative, explanatory, consequential",
            "technology implication",
            "implication",
            "analysis",
        )
    if has_any(text, ["ipo", "revenue", "profit", "earnings", "market cap", "valuation", "funding", "shares"]):
        return (
            "market consequence framing",
            "Explainer / analysis",
            "Practical, consequential, investor-facing",
            "financial consequence",
            "implication",
            "analysis",
        )
    if has_any(text, ["retirement", "saving", "savings", "money", "inflation", "mortgage", "budget", "paycheck"]):
        return (
            "policy-to-wallet framing",
            "Explainer / analysis",
            "Practical, consequential, consumer-facing",
            "financial consequence",
            "implication",
            "analysis",
        )
    if has_any(text, ["job", "hiring", "layoff", "worker", "workers", "career", "workplace", "salary"]):
        return (
            "career-security framing",
            "Explainer / analysis",
            "Cautionary, practical, workforce-oriented",
            "career impact",
            "pressure buildup",
            "reporting",
        )
    if has_any(text, ["moving", "relocation", "home", "housing", "rent", "assisted living", "house", "apartment"]):
        return (
            "housing / relocation tradeoff framing",
            "Feature / report",
            "Reflective, comparative, tradeoff-oriented",
            "housing tradeoff",
            "before/after",
            "reporting",
        )
    if has_any(text, ["flight", "airport", "airline", "travel", "cruise", "trip", "tsa"]):
        return (
            "travel-disruption framing",
            "News / report",
            "Surprised, concrete, traveler-focused",
            "travel disruption",
            "disruption",
            "reporting",
        )
    if topic_cluster == "space_and_aerospace":
        return (
            "science/tech implication framing",
            "Explainer / analysis",
            "Speculative, explanatory, consequential",
            "technology implication",
            "forecast",
            "analysis",
        )
    if topic_cluster in {"media_and_public_figures", "entertainment_and_culture"}:
        return (
            "human-interest lesson framing",
            "Feature / report",
            "Personal, revealing, narrative",
            "personal story",
            "before/after",
            "first-person anecdote",
        )
    if topic_cluster in {"capital_markets_and_fundraising", "business_strategy_and_companies"}:
        return (
            "business consequence framing",
            "Explainer / analysis",
            "Practical, consequential, business-facing",
            "business consequence",
            "implication",
            "analysis",
        )
    if topic_cluster == "politics_and_public_conflict":
        return (
            "conflict / fallout framing",
            "Breaking news / report",
            "Urgent, adversarial, high-stakes",
            "conflict",
            "escalation",
            "reporting",
        )
    return (
        "straight-news framing",
        "News / report",
        "Neutral, informative",
        "current development",
        "event lead",
        "reporting",
    )


def infer_specificity_level(headline: str, topic_cluster: str) -> str:
    text = lower(headline)
    if has_any(text, ["exactly", "how many", "first-ever", "first look", "inside", "timeline", "exclusive"]):
        return "Highly specific"
    if has_any(text, ["why", "how", "what", "who"]):
        return "Specific"
    if topic_cluster in {"other", "history_and_explainer"}:
        return "Moderately specific"
    return "Specific"


def infer_analysis_basis(tags: list[str]) -> str:
    if tags:
        return "headline + source tags"
    return "headline only"


def infer_confidence(headline: str, tags: list[str], topic_cluster: str) -> str:
    score = 1
    if tags:
        score += 1
    if topic_cluster != "other":
        score += 1
    if headline_word_count(headline) >= 8:
        score += 1
    if has_any(lower(headline), ["how", "why", "what", "who", "inside", "first", "we asked"]):
        score += 1
    return {1: "low", 2: "medium", 3: "medium", 4: "high", 5: "high"}[score]


def infer_topic_subject(headline: str, topic_cluster: str, primary_entity: str) -> str:
    text = lower(headline)

    if topic_cluster == "space_and_aerospace":
        if "ipo" in text or "funding" in text or "valuation" in text:
            return "SpaceX financing and IPO readiness"
        if "launch" in text or "starship" in text:
            return "SpaceX launch systems and mission risk"
        return "Space and aerospace business stakes"
    if topic_cluster == "capital_markets_and_fundraising":
        if "ipo" in text:
            return "IPO timing, valuation, and market appetite"
        if "revenue" in text or "profit" in text or "earnings" in text:
            return "Revenue, profit, and earnings pressure"
        if "funding" in text or "raise" in text:
            return "Fundraising and capital access"
        return "Capital markets and financing stakes"
    if topic_cluster == "personal_finance_and_affordability":
        if "retirement" in text or "saving" in text:
            return "Retirement saving and long-run money planning"
        if "inflation" in text:
            return "Inflation and household purchasing power"
        if "mortgage" in text or "rent" in text or "housing" in text:
            return "Housing costs and affordability pressure"
        return "Money decisions and affordability pressure"
    if topic_cluster == "careers_and_labor":
        if "layoff" in text:
            return "Layoffs and job security"
        if "hiring" in text:
            return "Hiring trends and recruiting pressure"
        if "salary" in text or "pay" in text:
            return "Compensation and workplace tradeoffs"
        return "Workplace pressure and career consequences"
    if topic_cluster == "real_estate_and_housing":
        if "assisted living" in text:
            return "Housing and elder-care tradeoffs"
        if "moving" in text or "relocation" in text:
            return "Relocation and cost-of-living tradeoffs"
        return "Housing costs and relocation decisions"
    if topic_cluster == "travel_and_transportation":
        if "flight" in text or "airport" in text:
            return "Flight and airport disruption"
        if "cruise" in text:
            return "Cruise travel behavior and disruption"
        return "Travel disruption and traveler experience"
    if topic_cluster == "health_and_wellness":
        if "diet" in text or "nutrition" in text:
            return "Diet and nutrition habits"
        if "workout" in text or "fitness" in text:
            return "Fitness routine and health tradeoffs"
        return "Health decisions and wellness outcomes"
    if topic_cluster == "politics_and_public_conflict":
        return "Public conflict and political fallout"
    if topic_cluster == "entertainment_and_culture":
        if "relationship" in text or "breakup" in text:
            return "Celebrity relationship fallout"
        return "Celebrity attention and culture coverage"
    if topic_cluster == "ai_and_automation":
        if primary_entity == "Elon Musk":
            if "retirement" in text or "saving" in text:
                return "Elon Musk's AI-abundance view of retirement saving"
            if "grok" in text:
                return "Grok and consumer-facing AI experimentation"
        if "chatbot" in text:
            return "Consumer AI chatbot behavior and use cases"
        return "AI capability and business implications"
    if topic_cluster == "consumer_tech_and_platforms":
        if "x money" in text:
            return "X's payments ambitions and platform expansion"
        return "Platform strategy and consumer tech changes"
    if topic_cluster == "business_strategy_and_companies":
        return "Company strategy, competition, and execution"
    if topic_cluster == "legal_and_regulatory":
        return "Legal dispute and accountability fallout"
    if topic_cluster == "military_and_defense":
        return "Military readiness and operational strain"
    if topic_cluster == "science_and_research":
        return "Scientific development and its implications"
    if topic_cluster == "food_and_consumer_habits":
        return "Food behavior and consumer habits"
    if topic_cluster == "education_and_family":
        return "Family and caregiving tradeoffs"
    if topic_cluster == "media_and_public_figures":
        return "Public-figure behavior and reputation"
    if topic_cluster == "sports_and_fandom":
        return "Sports performance and fan attention"
    if primary_entity:
        return f"{primary_entity} coverage and related stakes"
    return "A news development with reader consequences"


def infer_search_use_case(topic_cluster: str, trend_anchor: str, entity_role: str) -> str:
    base = {
        "space_and_aerospace": "Use when the query is about SpaceX, Starship, launch risk, NASA comparisons, or aerospace financing.",
        "capital_markets_and_fundraising": "Use when the query is about IPOs, funding rounds, valuations, earnings, or capital access.",
        "personal_finance_and_affordability": "Use when the query is about savings, retirement, inflation, affordability, or household money pressure.",
        "careers_and_labor": "Use when the query is about layoffs, hiring, jobs, compensation, or workplace disruption.",
        "real_estate_and_housing": "Use when the query is about housing costs, relocation, renting, or property tradeoffs.",
        "travel_and_transportation": "Use when the query is about flights, airports, disruptions, cruise behavior, or transport problems.",
        "health_and_wellness": "Use when the query is about health habits, diet, fitness, or medical risk.",
        "politics_and_public_conflict": "Use when the query is about political confrontation or public fallout.",
        "ai_and_automation": "Use when the query is about AI products, automation, the future of work, or consumer AI behavior.",
        "consumer_tech_and_platforms": "Use when the query is about platforms, apps, payments, or consumer technology change.",
        "business_strategy_and_companies": "Use when the query is about company strategy, competition, or management decisions.",
    }.get(topic_cluster, "Use when the query needs a specific story angle rather than a broad topic result.")
    if entity_role == "private_life":
        base += " Exclude generic celebrity lookups unless the user needs the personal-life angle."
    if trend_anchor:
        base += f" Anchor: {trend_anchor}."
    return base


def infer_trend_anchor(headline: str, topic_cluster: str, primary_entity: str) -> str:
    text = lower(headline)

    if topic_cluster == "space_and_aerospace":
        if "ipo" in text or "funding" in text or "valuation" in text:
            return "SpaceX financing / IPO"
        if "launch" in text or "starship" in text:
            return "SpaceX launch system"
        return "space and aerospace execution"
    if topic_cluster == "capital_markets_and_fundraising":
        if "ipo" in text:
            return "IPO timing and valuation"
        if "revenue" in text or "profit" in text:
            return "revenue and profit performance"
        if "funding" in text:
            return "fundraising and capital access"
        return "capital markets appetite"
    if topic_cluster == "personal_finance_and_affordability":
        if "retirement" in text:
            return "retirement saving and AI abundance"
        if "inflation" in text:
            return "inflation and household purchasing power"
        if "mortgage" in text or "rent" in text:
            return "housing affordability pressure"
        return "money pressure and affordability"
    if topic_cluster == "careers_and_labor":
        if "layoff" in text:
            return "layoff pressure and job security"
        if "hiring" in text:
            return "hiring slowdown or recruiting pressure"
        return "workforce change"
    if topic_cluster == "real_estate_and_housing":
        return "housing costs and relocation"
    if topic_cluster == "travel_and_transportation":
        return "travel disruption and trip reliability"
    if topic_cluster == "health_and_wellness":
        return "health habits and outcomes"
    if topic_cluster == "politics_and_public_conflict":
        return "public conflict and reputation risk"
    if topic_cluster == "ai_and_automation":
        if primary_entity == "Elon Musk" and "retirement" in text:
            return "AI abundance and retirement saving"
        if "grok" in text:
            return "consumer AI behavior"
        return "AI product adoption and consequences"
    if topic_cluster == "consumer_tech_and_platforms":
        if "x money" in text:
            return "platform payments expansion"
        return "platform strategy and user behavior"
    if topic_cluster == "business_strategy_and_companies":
        return "company strategy and competitive pressure"
    if topic_cluster == "legal_and_regulatory":
        return "legal fallout and accountability"
    if topic_cluster == "entertainment_and_culture":
        return "celebrity attention and audience interest"
    if topic_cluster == "media_and_public_figures":
        return "public-figure reputation and attention"
    if primary_entity:
        return f"{primary_entity} coverage"
    return "broad news interest"


def infer_query_terms(headline: str, tags: list[str], topic_cluster: str, primary_entity: str) -> list[str]:
    text = lower(headline)
    terms = []

    def add(term: str) -> None:
        term = clean(term)
        if term and term not in terms:
            terms.append(term)

    if primary_entity:
        add(primary_entity)
    if topic_cluster == "space_and_aerospace":
        for term in ["spacex", "starship", "rocket", "launch", "nasa", "ipo", "funding", "valuation", "revenue", "profit"]:
            add(term)
    elif topic_cluster == "capital_markets_and_fundraising":
        for term in ["ipo", "funding", "valuation", "revenue", "profit", "earnings", "shares", "capital raise"]:
            add(term)
    elif topic_cluster == "personal_finance_and_affordability":
        for term in ["retirement", "saving", "savings", "inflation", "mortgage", "affordability", "budget", "cost of living"]:
            add(term)
    elif topic_cluster == "careers_and_labor":
        for term in ["layoffs", "hiring", "jobs", "salary", "workplace", "employees"]:
            add(term)
    elif topic_cluster == "real_estate_and_housing":
        for term in ["housing", "rent", "relocation", "home", "property", "assisted living"]:
            add(term)
    elif topic_cluster == "travel_and_transportation":
        for term in ["flight", "airport", "airline", "cruise", "trip", "travel"]:
            add(term)
    elif topic_cluster == "ai_and_automation":
        for term in ["ai", "artificial intelligence", "chatbot", "grok", "automation", "future of work"]:
            add(term)
    elif topic_cluster == "consumer_tech_and_platforms":
        for term in ["platform", "app", "payments", "social media", "x money", "technology"]:
            add(term)
    elif topic_cluster == "politics_and_public_conflict":
        for term in ["politics", "arrest", "lawsuit", "public conflict", "fallout"]:
            add(term)
    elif topic_cluster == "entertainment_and_culture":
        for term in ["celebrity", "relationship", "breakup", "culture", "media"]:
            add(term)
    else:
        for term in ["business", "story", "trend"]:
            add(term)

    if "musk" in text and "Elon Musk" not in terms:
        add("Elon Musk")
    if "spacex" in text:
        add("SpaceX")
    if "tesla" in text:
        add("Tesla")
    if "xai" in text or "grok" in text:
        add("xAI")
    if "twitter" in text or "x money" in text:
        add("X")
    return terms[:10]


def infer_trend_exclusion(headline: str, primary_entity: str, topic_cluster: str, trend_anchor: str) -> str:
    text = lower(headline)
    notes = []

    if primary_entity == "Elon Musk":
        if topic_cluster in {"space_and_aerospace", "capital_markets_and_fundraising", "personal_finance_and_affordability", "ai_and_automation", "consumer_tech_and_platforms"}:
            if "spacex" in text or "starship" in text:
                notes.append("Do not use as generic Musk filler; keep it for SpaceX financing or launch-system queries.")
            elif "tesla" in text:
                notes.append("Do not use for generic Musk lookups; keep it for Tesla finance, product, or strategy queries.")
            elif "retirement" in text or "savings" in text:
                notes.append("Use only for AI-abundance or retirement-saving angles, not broad Musk lookups.")
            elif "grok" in text or "xai" in text:
                notes.append("Use only for consumer AI or xAI-specific queries.")
            else:
                notes.append("Avoid broad Musk retrieval; this story only matters if the query is about the specific business angle.")
    if primary_entity == "Donald Trump" and topic_cluster != "politics_and_public_conflict":
        notes.append("Avoid generic Trump retrieval unless the query needs this exact conflict or business angle.")
    if topic_cluster == "entertainment_and_culture" and has_any(text, ["relationship", "breakup", "marriage", "wife", "husband"]):
        notes.append("Do not use for broad celebrity search unless the relationship angle matters.")
    if topic_cluster == "other":
        notes.append("Broad topic only; treat as low-priority unless the query is very specific.")
    if trend_anchor == "broad news interest":
        notes.append("No strong trend anchor beyond the headline itself.")
    return " ".join(notes)


def trend_score(headline: str, topic_cluster: str, primary_entity: str) -> int:
    text = lower(headline)
    score = 35
    if topic_cluster in {"space_and_aerospace", "capital_markets_and_fundraising", "personal_finance_and_affordability", "careers_and_labor", "real_estate_and_housing", "travel_and_transportation", "ai_and_automation"}:
        score += 20
    if has_any(text, ["ipo", "revenue", "profit", "funding", "valuation", "earnings", "launch", "layoff", "hiring", "retirement", "inflation", "housing", "mortgage", "airline", "airport", "chatbot", "grok"]):
        score += 20
    if has_any(text, ["exclusive", "first look", "inside", "timeline", "how", "why", "what", "who", "we asked"]):
        score += 10
    if primary_entity in {"Elon Musk", "Donald Trump", "SpaceX", "Tesla", "OpenAI", "Nvidia", "Amazon", "Target", "Walmart", "NASA"}:
        score += 10
    if has_any(text, ["family", "spouse", "kids", "marriage", "date", "routine", "house"]):
        score -= 10
    if has_any(text, ["pyramid", "list", "timeline", "database", "photo", "photo gallery"]):
        score -= 5
    if topic_cluster == "other":
        score -= 10
    return max(0, min(100, score))


def inferred_entities(primary: str, secondary: list[str], tags: list[str]) -> tuple[str, str]:
    secondary_values = list(secondary)
    if not primary and tags:
        for tag in tags:
            candidate = clean(tag)
            if candidate:
                primary = candidate
                break
    return primary, pipe_join(secondary_values)


def infer_entity_type(primary_entity: str) -> str:
    if primary_entity in {"Elon Musk", "Donald Trump", "Don Lemon", "Grimes"}:
        return "person"
    if primary_entity in {"SpaceX", "Tesla", "xAI", "X", "OpenAI", "Nvidia", "BYD", "Xiaomi", "Amazon", "Costco", "Target", "Walmart", "NASA"}:
        return "organization"
    if primary_entity:
        return "entity"
    return "topic"


def build_row(idx: int, raw: dict[str, str], source_batch: str, duplicate_count: int) -> dict[str, str]:
    source_url = clean(raw.get("Link Current") or "")
    canonical_url = canonicalize_url(source_url)
    raw_headline = clean(raw.get("Headline") or "")
    published_at = clean(raw.get("  Story Display Date") or raw.get("Story Display Date") or "")
    editorial_team = clean(raw.get("Editorial Team List") or "")
    source_tags_raw = split_tags(raw.get("Categories List") or "")
    source_tags_clean = normalize_tags(source_tags_raw)
    normalized_headline = normalize_headline(raw_headline, source_url)
    primary_entity, entity_role, secondary_entities = infer_primary_entity(normalized_headline, source_tags_clean)
    topic_cluster = infer_topic_cluster(normalized_headline, source_tags_clean, source_url)
    main_point = infer_main_point(normalized_headline, topic_cluster, entity_role)
    topic_subject = infer_topic_subject(normalized_headline, topic_cluster, primary_entity)
    framing, content_type, tone, hook_type, narrative_device, evidence_type = infer_framing(
        normalized_headline, topic_cluster, main_point
    )
    audience_fit = {
        "ai_and_automation": "readers following AI and tech change",
        "capital_markets_and_fundraising": "market watchers and business readers",
        "careers_and_labor": "job seekers and workers",
        "crime_and_safety": "readers following legal and safety fallout",
        "education_and_family": "parents and family-focused readers",
        "electric_vehicles_and_transport": "EV and transport readers",
        "energy_and_infrastructure": "readers following energy and infrastructure",
        "entertainment_and_culture": "culture and celebrity readers",
        "health_and_wellness": "health-conscious readers",
        "history_and_explainer": "readers looking for context and background",
        "legal_and_regulatory": "readers following legal consequences",
        "lifestyle_and_relationships": "lifestyle and relationship readers",
        "media_and_public_figures": "readers following public figures and media",
        "military_and_defense": "readers following defense and military operations",
        "personal_finance_and_affordability": "people tracking money, saving, and affordability",
        "politics_and_public_conflict": "readers following politics and public conflict",
        "real_estate_and_housing": "people tracking housing and relocation",
        "retail_and_shopping": "shoppers and retail watchers",
        "science_and_research": "readers following science and innovation",
        "space_and_aerospace": "readers following space and aerospace",
        "sports_and_fandom": "sports readers and fans",
        "travel_and_transportation": "travelers and commuters",
        "business_strategy_and_companies": "business readers and operators",
        "consumer_tech_and_platforms": "tech readers and platform users",
        "food_and_consumer_habits": "food and consumer readers",
        "other": "general news readers",
    }.get(topic_cluster, "general news readers")
    specific_scope = FRAMING_SCOPE_MAP.get(topic_cluster, "Broad, reusable")
    specificity_level = infer_specificity_level(normalized_headline, topic_cluster)
    analysis_basis = infer_analysis_basis(source_tags_clean)
    analysis_confidence = infer_confidence(normalized_headline, source_tags_clean, topic_cluster)
    trend_anchor = infer_trend_anchor(normalized_headline, topic_cluster, primary_entity)
    trend_query_terms = infer_query_terms(normalized_headline, source_tags_clean, topic_cluster, primary_entity)
    trend_exclusion_notes = infer_trend_exclusion(normalized_headline, primary_entity, topic_cluster, trend_anchor)
    score = trend_score(normalized_headline, topic_cluster, primary_entity)
    search_use_case = infer_search_use_case(topic_cluster, trend_anchor, entity_role)
    entity_type = infer_entity_type(primary_entity)
    angle = {
        "authority-backed forecast": "Translate a high-profile claim into a practical consequence or debate.",
        "expert check": "Use outside voices to test, challenge, or validate a claim.",
        "utility / decision-aid framing": "Give the reader a direct payoff, shortcut, or recommendation.",
        "conflict / fallout framing": "Lead with the confrontation and widen to the consequence.",
        "science/tech implication framing": "Turn a technical development into a reader-relevant consequence.",
        "market consequence framing": "Translate market or business signals into investor or consumer consequences.",
        "policy-to-wallet framing": "Show how a policy, price change, or market shift hits household budgets.",
        "career-security framing": "Tie the story to jobs, hiring, layoffs, or workplace security.",
        "housing / relocation tradeoff framing": "Use a move or housing decision to surface the hidden tradeoff.",
        "travel-disruption framing": "Make the disruption legible as a trip or transport problem.",
        "human-interest lesson framing": "Use a personal story to make a broader lesson concrete.",
        "business consequence framing": "Show how strategy and execution affect the company or market position.",
        "straight-news framing": "Lead with the event and make the consequence visible fast.",
    }.get(framing, "Make the story's consequence visible fast.")
    reader_promise = {
        "Current development": "The latest development and what it changes.",
        "Future implications": "A forward-looking read on what could change next.",
        "Market consequence": "What the market or business consequence means.",
        "Institutional strain": "How pressure builds inside the organization.",
        "Cost-of-living impact": "How the story affects budgets and affordability.",
        "Career impact": "How the story affects jobs, hiring, or workplace security.",
        "Relocation tradeoff": "How the move or housing choice changes the tradeoff.",
        "Personal lesson": "A personal angle that makes the broader lesson clear.",
        "Travel disruption": "How the disruption changes the trip or travel experience.",
        "Public conflict": "What happened and why the fallout matters.",
        "Utility payoff": "A quick, practical answer the reader can use.",
        "Consumer decision": "A decision-oriented read on what to buy or do.",
        "Comparison tradeoff": "A clear comparison that helps the reader choose.",
        "Health outcome": "How the habit or choice affects health.",
        "Legal fallout": "What the legal action or dispute means next.",
        "Business consequence": "How the company or strategy decision affects outcomes.",
        "Cultural reaction": "How the story plays in public and culture.",
        "Investor focus": "How investors, markets, or valuations are affected.",
    }.get(main_point, "The story's consequence and why it matters.")
    stakes = {
        "Current development": "The main stake is whether the development changes the story's direction or keeps pressure on the people involved.",
        "Future implications": "The stake is whether a forecast becomes a real shift in behavior, markets, or expectations.",
        "Market consequence": "The stake is whether the business or market signal changes investor or company behavior.",
        "Institutional strain": "The stake is whether internal pressure affects performance, credibility, or execution.",
        "Cost-of-living impact": "The stake is whether the development changes how expensive life feels for the reader or the subject.",
        "Career impact": "The stake is whether workers, applicants, or employers face real job-market consequences.",
        "Relocation tradeoff": "The stake is whether moving or staying changes quality of life, cost, and long-term plans.",
        "Travel disruption": "The stake is whether the disruption changes the trip, schedule, or traveler experience.",
        "Public conflict": "The stake is whether the conflict affects reputation, attention, or next-step consequences.",
        "Legal fallout": "The stake is whether the legal issue changes power, liability, or public accountability.",
        "Business consequence": "The stake is whether strategy translates into competitive advantage or visible pressure.",
        "Utility payoff": "The stake is whether the reader can use the information immediately.",
    }.get(main_point, "The stake is the practical consequence the reader can understand immediately.")

    secondary_output = pipe_join(secondary_entities)
    primary_entity, secondary_output = inferred_entities(primary_entity, secondary_entities, source_tags_clean)
    story_family_key = canonical_url or source_url
    is_duplicate_url = "yes" if duplicate_count > 1 else "no"

    return {
        "story_id": str(idx),
        "source_url": source_url,
        "canonical_url": canonical_url,
        "story_family_key": story_family_key,
        "story_family_count": str(duplicate_count),
        "is_duplicate_url": is_duplicate_url,
        "source_batch": source_batch,
        "active_flag": "yes",
        "published_at": published_at,
        "headline_raw": raw_headline,
        "headline": normalized_headline,
        "headline_word_count": str(headline_word_count(normalized_headline)),
        "editorial_team_list": editorial_team,
        "source_tags_raw": pipe_join(source_tags_raw),
        "source_tags_clean": pipe_join(source_tags_clean),
        "analysis_basis": analysis_basis,
        "analysis_confidence": analysis_confidence,
        "primary_entity": primary_entity,
        "entity_type": entity_type,
        "entity_role": entity_role,
        "secondary_entities": secondary_output,
        "topic_cluster": topic_cluster,
        "topic_cluster_label": TOPIC_LABELS.get(topic_cluster, topic_cluster.replace("_", " ")),
        "main_point_of_interest": main_point,
        "topic_subject": topic_subject,
        "framing": framing,
        "angle": angle,
        "content_type": content_type,
        "tone": tone,
        "framing_scope_flag": specific_scope,
        "hook_type": hook_type,
        "reader_promise": reader_promise,
        "narrative_device": narrative_device,
        "stakes": stakes,
        "specificity_level": specificity_level,
        "evidence_type": evidence_type,
        "audience_fit": audience_fit,
        "replicable_elements": infer_replicable_elements(framing, topic_cluster, main_point, source_tags_clean),
        "trend_anchor": trend_anchor,
        "trend_query_terms": pipe_join(trend_query_terms),
        "trend_exclusion_notes": trend_exclusion_notes,
        "trend_fit_score": str(score),
        "search_use_case": search_use_case,
    }


def infer_replicable_elements(framing: str, topic_cluster: str, main_point: str, tags: list[str]) -> str:
    if framing == "authority-backed forecast":
        return "Use a recognizable authority, a time-bound claim, and a practical consequence."
    if framing == "expert check":
        return "Use a disputed claim, then bring in outside voices to test it."
    if framing == "utility / decision-aid framing":
        return "Promise a direct payoff, deliver it early, and make the reader's next step obvious."
    if framing == "conflict / fallout framing":
        return "Lead with the conflict and keep the public consequence visible."
    if framing == "market consequence framing":
        return "Turn business signals into a consequence for investors, workers, or consumers."
    if framing == "policy-to-wallet framing":
        return "Turn a policy or price move into household impact."
    if framing == "career-security framing":
        return "Tie the story to hiring, layoffs, pay, or job security."
    if framing == "housing / relocation tradeoff framing":
        return "Use the move or home decision to surface the hidden tradeoff."
    if framing == "travel-disruption framing":
        return "Make the disruption concrete and traveler-specific."
    if framing == "science/tech implication framing":
        return "Translate a technical development into real-world stakes."
    if framing == "human-interest lesson framing":
        return "Use a personal anecdote to make a broad trend legible."
    if framing == "business consequence framing":
        return "Show how strategy, competition, or execution changes outcomes."
    return "Lead with the event, then make the consequence visible."


def load_source_rows(source_path: Path) -> list[dict[str, str]]:
    with source_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def count_top(rows: list[dict[str, str]], key: str, limit: int = 10) -> list[tuple[str, int]]:
    counter = Counter(clean(row.get(key, "")) or "Unknown" for row in rows)
    return counter.most_common(limit)


def fmt_counts(items: list[tuple[str, int]]) -> str:
    return "\n".join(f"- {label}: {count}" for label, count in items)


def trend_band(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium-high"
    if score >= 45:
        return "medium"
    return "low"


def write_schema(path: Path) -> None:
    path.write_text(
        """# BI Story Trend Database Schema

This database is headline-first and tag-aware. It is designed for query quality, not full article reconstruction.

The key design choice is to separate stable story identity, entity labels, topical buckets, and retrieval hints. That keeps the archive usable when a trend query should return a SpaceX finance story, not every Musk story.

## Core Source Fields

- `story_id`
- `source_url`
- `canonical_url`
- `story_family_key`
- `story_family_count`
- `is_duplicate_url`
- `source_batch`
- `active_flag`
- `published_at`
- `headline_raw`
- `headline`
- `headline_word_count`
- `editorial_team_list`
- `source_tags_raw`
- `source_tags_clean`

## Analysis Layer

- `analysis_basis`: whether the classification used headline only or headline plus tags
- `analysis_confidence`: rough confidence level for the row's classification
- `primary_entity`: the main person, company, brand, or institution that should anchor retrieval
- `entity_type`: coarse identity class such as `person`, `organization`, `entity`, or `topic`
- `entity_role`: how the entity functions in the story, such as `public_figure`, `organizational_actor`, or `private_life`
- `secondary_entities`: additional entities that matter but should not dominate retrieval
- `topic_cluster`: broad normalized search bucket
- `topic_cluster_label`: human-readable version of the topic cluster
- `main_point_of_interest`: the reader-facing consequence or payoff
- `topic_subject`: the specific subject matter
- `framing`: the editorial frame
- `angle`: the editorial move that makes the story work
- `content_type`: the story form
- `tone`: the rhetorical posture
- `framing_scope_flag`: whether the framing is broadly reusable or subject-specific
- `hook_type`: the headline hook
- `reader_promise`: what the reader gets from the story
- `narrative_device`: the structural device
- `stakes`: the consequence that gives the story urgency
- `specificity_level`: how narrow or broad the story is
- `evidence_type`: what kind of evidence carries the story
- `audience_fit`: who should care
- `replicable_elements`: reusable editorial pattern

## Trend Retrieval Layer

- `trend_anchor`: the specific trend or event context that should pull the story into search
- `trend_query_terms`: pipe-delimited query terms for retrieval
- `trend_exclusion_notes`: guardrails that keep broad entities from overmatching
- `trend_fit_score`: 0-100 score for trend usefulness
- `search_use_case`: human-readable search guidance

## Query Rules

- Treat `canonical_url` as the stable dedupe key.
- Use `story_family_key` and `story_family_count` to collapse duplicate or near-duplicate exports before ranking results.
- For broad public figures like Elon Musk, query with `trend_anchor` first and `primary_entity` second.
- Prefer the combination of `primary_entity`, `entity_type`, `topic_cluster`, and `main_point_of_interest` when you need a narrow, business-relevant result.
- Use `trend_query_terms` for positive retrieval and `trend_exclusion_notes` for hard disambiguation.
- Keep `active_flag=yes` for rows that should remain eligible in weekly reruns; flip it only when a story should be retired from the active library.

## Working Rules

- Use the entity and topic fields to avoid broad overmatching.
- A story about Musk should not surface for every Musk query; the `trend_anchor` and `trend_exclusion_notes` must narrow it to the right business or future-of-work angle.
- The database is headline-and-tags based until full-article text is added later.
- Keep `main_point_of_interest` and `framing` controlled so the archive stays queryable.
- The weekly refresh should preserve `canonical_url`-based identity even if the source sheet adds or reorders rows.
""",
        encoding="utf-8",
    )


def write_summary(path: Path, rows: list[dict[str, str]], source_path: Path) -> None:
    total = len(rows)
    topic_counts = count_top(rows, "topic_cluster_label", 12)
    framing_counts = count_top(rows, "framing", 10)
    main_point_counts = count_top(rows, "main_point_of_interest", 12)
    trend_counts = count_top(rows, "trend_anchor", 12)
    duplicate_rows = sum(1 for row in rows if row["is_duplicate_url"] == "yes")
    duplicate_families = len({row["story_family_key"] for row in rows if row["story_family_count"] != "1"})
    source_batches = Counter(row["source_batch"] for row in rows)
    scores = [int(row["trend_fit_score"]) for row in rows]
    score_stats = {
        "median": int(median(scores)) if scores else 0,
        "min": min(scores) if scores else 0,
        "max": max(scores) if scores else 0,
    }
    bands = Counter(trend_band(score) for score in scores)
    band_lines = "\n".join(f"- {band}: {bands.get(band, 0)}" for band in ["high", "medium-high", "medium", "low"])

    musk_rows = [row for row in rows if "musk" in lower(row["headline"]) or "musk" in lower(row["source_tags_raw"]) or row["primary_entity"] == "Elon Musk"]
    musk_filters = [
        row
        for row in musk_rows
        if any(k in lower(row["topic_subject"]) for k in ["spacex", "tesla", "retirement", "ai", "launch", "funding", "ipo", "x money", "grok"])
    ]

    examples = "\n".join(
        f"- {row['headline']} | {row['primary_entity']} | {row['topic_cluster_label']} | {row['trend_anchor']} | {row['trend_fit_score']}"
        for row in rows[:5]
    )

    summary = f"""# BI Story Trend Database Summary

Source file: `{source_path}`
Rows processed: {total:,}

## What This Database Does

This build turns a headline-and-tag export into a queryable story database with controlled framing labels and a retrieval layer built for trend-aware searching.

The key design choice is to keep stable story identity, entity labels, topical buckets, and retrieval hints separate. That prevents broad overmatching, especially for high-frequency names like Elon Musk.

## Identity Layer

- Duplicate URL rows: {duplicate_rows:,}
- Duplicate URL families: {duplicate_families:,}
- Source batches represented: {len(source_batches):,}

Use `canonical_url` as the dedupe key and `story_family_key` when collapsing repeated exports or multiple versions of the same story.

## Top Story Mix

Most common topic clusters:
{fmt_counts(topic_counts)}

Most common main-point labels:
{fmt_counts(main_point_counts)}

Most common framing labels:
{fmt_counts(framing_counts)}

Most common trend anchors:
{fmt_counts(trend_counts)}

## Trend Fit Distribution

- Median trend fit score: {score_stats['median']}
- Range: {score_stats['min']} to {score_stats['max']}

Trend-fit bands:
{band_lines}

## Musk Guardrail Readout

- Rows with Musk in the headline or tags: {len(musk_rows):,}
- Rows that survive the narrower business-angle filter: {len(musk_filters):,}

This is the main proof that the database is not returning every Musk story for every Musk query.

## Example Rows

{examples}

## Practical Query Guidance

- For Musk, search the `trend_anchor` field first, not just `primary_entity`.
- For SpaceX, prefer `trend_anchor` values like `SpaceX financing / IPO` or `SpaceX launch system`.
- For AI coverage, use `topic_cluster = ai_and_automation` plus a specific `trend_anchor`.
- For company coverage, combine `primary_entity`, `entity_type`, `topic_cluster`, and `main_point_of_interest`.
- For broad searches, use `trend_fit_score >= 60` to keep the results focused.
"""
    path.write_text(summary, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the BI story trend database.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source CSV export")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Schema markdown path")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY, help="Summary markdown path")
    args = parser.parse_args()

    source_rows = load_source_rows(args.source)
    source_batch = args.source.stem
    duplicate_counts = Counter(
        canonicalize_url(row.get("Link Current") or "") or clean(row.get("Link Current") or "")
        for row in source_rows
    )
    output_rows = [
        build_row(
            idx,
            row,
            source_batch,
            duplicate_counts[canonicalize_url(row.get("Link Current") or "") or clean(row.get("Link Current") or "")],
        )
        for idx, row in enumerate(source_rows, start=1)
    ]

    fieldnames = [
        "story_id",
        "source_url",
        "canonical_url",
        "story_family_key",
        "story_family_count",
        "is_duplicate_url",
        "source_batch",
        "active_flag",
        "published_at",
        "headline_raw",
        "headline",
        "headline_word_count",
        "editorial_team_list",
        "source_tags_raw",
        "source_tags_clean",
        "analysis_basis",
        "analysis_confidence",
        "primary_entity",
        "entity_type",
        "entity_role",
        "secondary_entities",
        "topic_cluster",
        "topic_cluster_label",
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
        "trend_anchor",
        "trend_query_terms",
        "trend_exclusion_notes",
        "trend_fit_score",
        "search_use_case",
    ]

    write_csv(args.output, output_rows, fieldnames)
    write_schema(args.schema)
    write_summary(args.summary, output_rows, args.source)

    print(f"Wrote {len(output_rows):,} rows to {args.output}")
    print(f"Wrote schema to {args.schema}")
    print(f"Wrote summary to {args.summary}")


if __name__ == "__main__":
    main()
