from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from statistics import median


BASE_DIR = Path("/Users/mmitchell/Desktop/coconut")
DATA_DIR = BASE_DIR / "msn-slideshow-analysis"
SOURCE = DATA_DIR / "story_analysis_database.csv"
OUTPUT = DATA_DIR / "msn_slideshow_report_latest.md"


def load_rows() -> list[dict[str, str]]:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["page_views_int"] = int((row.get("page_views") or "0").replace(",", "") or 0)
        row["headline_word_count_int"] = int(row.get("headline_word_count") or 0)
    return rows


def mean_int(values: list[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def top_counts(rows: list[dict[str, str]], key: str, limit: int = 8) -> list[tuple[str, int]]:
    counter = Counter(row.get(key, "").strip() or "Unknown" for row in rows)
    return counter.most_common(limit)


def fmt_counts(items: list[tuple[str, int]]) -> str:
    return "\n".join(f"- {label}: {count}" for label, count in items)


def group_stats(rows: list[dict[str, str]]) -> dict[str, float | int]:
    values = [row["page_views_int"] for row in rows]
    return {
        "stories": len(rows),
        "median": int(median(values)),
        "mean": mean_int(values),
        "min": min(values),
        "max": max(values),
    }


def example_lines(rows: list[dict[str, str]], limit: int = 5) -> str:
    lines = []
    for row in rows[:limit]:
        lines.append(
            f"- {row['headline']} | {row['framing']} | {row['topic_subject']} | {row['page_views_int']:,}"
        )
    return "\n".join(lines)


def main() -> None:
    rows = load_rows()
    ranked = sorted(rows, key=lambda row: row["page_views_int"])
    total = len(ranked)
    top_100 = ranked[-100:][::-1]
    bottom_100 = ranked[:100]
    middle_start = max(0, total // 2 - 50)
    middle_100 = ranked[middle_start:middle_start + 100]
    top_25 = ranked[-25:][::-1]
    bottom_25 = ranked[:25]

    overall_framings = top_counts(rows, "framing", 10)
    overall_topics = top_counts(rows, "topic_subject", 10)

    top_stats = group_stats(top_100)
    middle_stats = group_stats(middle_100)
    bottom_stats = group_stats(bottom_100)

    report = f"""# MSN Slideshow Analysis Report

Date: 2026-06-04
Source dataset: `msn-slideshow-analysis/MSN Story Audit Oct 2025 - May 2026 - all stories.csv`
Rebuilt inputs: `story_analysis_database.csv`, `story_framing_database.csv`, `story_framing_summary.md`

## Executive Summary

This rerun covers {total:,} MSN stories. The clearest pattern is that top-performing stories are usually event-led, conflict-led, or consequence-led. Lower-performing stories are more often topic-led, utility-led, or explanatory without a strong immediate stake.

The strongest editorial lesson remains simple: performance rises when a headline makes the consequence visible fast, ideally through money, job security, travel disruption, institutional strain, or public conflict.

## Overall Story Mix

Most common framings across the full dataset:
{fmt_counts(overall_framings)}

Most common topics across the full dataset:
{fmt_counts(overall_topics)}

## Performance Bands

### Top 100 Stories

- Median page views: {top_stats['median']:,}
- Mean page views: {top_stats['mean']:.1f}
- Range: {top_stats['min']:,} to {top_stats['max']:,}

Top main points:
{fmt_counts(top_counts(top_100, "main_point_of_interest"))}

Top framings:
{fmt_counts(top_counts(top_100, "framing"))}

Top topics:
{fmt_counts(top_counts(top_100, "topic_subject"))}

Representative top stories:
{example_lines(top_100)}

### Middle 100 Stories

- Median page views: {middle_stats['median']:,}
- Mean page views: {middle_stats['mean']:.1f}
- Range: {middle_stats['min']:,} to {middle_stats['max']:,}

Top main points:
{fmt_counts(top_counts(middle_100, "main_point_of_interest"))}

Top framings:
{fmt_counts(top_counts(middle_100, "framing"))}

Top topics:
{fmt_counts(top_counts(middle_100, "topic_subject"))}

### Bottom 100 Stories

- Median page views: {bottom_stats['median']:,}
- Mean page views: {bottom_stats['mean']:.1f}
- Range: {bottom_stats['min']:,} to {bottom_stats['max']:,}

Top main points:
{fmt_counts(top_counts(bottom_100, "main_point_of_interest"))}

Top framings:
{fmt_counts(top_counts(bottom_100, "framing"))}

Top topics:
{fmt_counts(top_counts(bottom_100, "topic_subject"))}

Representative bottom stories:
{example_lines(bottom_100)}

## Top 25 vs Bottom 25 Readout

Top 25 stories over-index on:
- Concrete incidents and disruptions
- Famous or recognizable names
- Direct household, career, or travel consequences
- Conflict, surprise, or visible fallout

Bottom 25 stories over-index on:
- Utility and promo language
- Topic-first AI, tech, and market framing
- Commentary or implications without a sharp event
- Narrower insider framing

Top 25 most common framings:
{fmt_counts(top_counts(top_25, "framing"))}

Bottom 25 most common framings:
{fmt_counts(top_counts(bottom_25, "framing"))}

Top 25 most common topics:
{fmt_counts(top_counts(top_25, "topic_subject"))}

Bottom 25 most common topics:
{fmt_counts(top_counts(bottom_25, "topic_subject"))}

## Editorial Takeaways

- Prioritize headlines that start with a concrete development, not a category or theme.
- Make the consequence visible in the headline whenever possible.
- AI, tech, and market stories need sharper human stakes to compete with top-tier event stories.
- Utility stories can work, but they generally underperform unless tied to urgency, deadlines, or clear money-saving value.
- The best repeatable formula is still straightforward: what happened, why it matters now, and who it affects.
"""

    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote report to {OUTPUT}")


if __name__ == "__main__":
    main()
