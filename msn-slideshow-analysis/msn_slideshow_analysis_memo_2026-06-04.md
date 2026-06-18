# MSN Slideshow Analysis Memo

Date: 2026-06-04
Folder: `msn-slideshow-analysis/`

## Purpose

This memo consolidates the latest MSN slideshow analysis outputs into a clean, document-ready format. It is designed to be easy to paste into Google Docs or use as a working memo.

## Latest Report Outputs

The most recent report files in this folder were generated on June 1, 2026.

### 1. Top 100 vs Middle 100 vs Bottom 100 Page-View Analysis

Source file: `top_middle_bottom_100_pageviews_analysis.md`

What it does:
Compares three groups of stories from the full dataset of 8,651 stories:
- The top 100 by page views
- The middle 100 around the median
- The bottom 100 by page views

Core findings:
- Top performers heavily over-index on current developments, visible consequences, conflict, and broadly legible stakes.
- Middle performers skew more toward careers, housing, and tech implication stories without the same urgency.
- Bottom performers include a larger share of utility, guide, and topic-first tech coverage.
- The strongest performance gap is not just subject matter. It is framing that makes the consequence immediate.

Top 100 snapshot:
- Median page views: 140,878
- Mean page views: 186,566.8
- Most common framing: Straight-news framing
- Most common high-performing topics: politics/public conflict, travel/transportation, real estate/housing, military/defense

Middle 100 snapshot:
- Median page views: 1,018
- Mean page views: 1,018.4
- Most common framing: Straight-news framing
- Most common topics: technology/platforms, careers/labor, real estate/housing

Bottom 100 snapshot:
- Median page views: 12
- Mean page views: 11.9
- Most common framing: Straight-news framing, followed by utility/decision-aid
- Most common topics: technology/platforms, reviews/guides, travel/transportation

Editorial takeaway:
Stories perform best when the headline quickly answers three questions:
- What happened?
- Why does it matter now?
- Who is affected?

### 2. Full-Sample Top vs Bottom Story Patterns

Source file: `top_vs_bottom_story_patterns.md`

What it does:
Compares the 25 highest-performing and 25 lowest-performing stories by page views and tags each story with the framing pattern that best explains its performance.

Top-story patterns:
- Concrete event or disruption
- Visible stakes
- Recognizable anchor such as Elon Musk, Target, United, Navy, or JPMorgan
- Conflict, surprise, reversal, or public fallout
- Human-scale framing
- Scene-rich detail
- Broad legibility outside a niche beat

Bottom-story patterns:
- Guide, utility, promo, or shopping language
- Topic-first rather than event-first framing
- Insider or industry-specific framing
- Abstract consequence
- Lower emotional or practical payoff
- Commentary or explanation without strong tension

Practical readout:
- Top stories tend to be built around a real event, a visible consequence, or a personal/institutional tradeoff.
- Bottom stories are more likely to be informative but low-urgency.
- AI, tech, markets, and shopping stories need a sharper event hook or clearer human stakes to break into the top tier.

### 3. Story Framing Summary

Source file: `story_framing_summary.md`

What it does:
Summarizes the most common framing choices across the full story set.

Most common main-point categories:
- Current development: 3,068
- Practical answer: 894
- Future implications: 813
- Market consequence: 730

Most common framing patterns:
- Straight-news framing: 3,081
- Utility/decision-aid framing: 897
- Science/tech implication framing: 820
- Market consequence framing: 731

Most useful repeatable frameworks:
- Straight-news framing
- Utility/decision-aid framing
- Science/tech implication framing
- Policy-to-wallet framing
- Housing/relocation tradeoff framing
- Career-security framing
- Human-interest lesson framing
- Hidden-system framing

Editorial takeaway:
The broadest repeatable formula is still simple straight-news framing, but specialized formulas work when they translate complexity into visible reader consequences.

## Output Inventory

Below is the full set of main outputs in `msn-slideshow-analysis/`.

### Input Dataset

- `MSN Story Audit Oct 2025 - May 2026 - all stories.csv`
  Master source dataset used for the analyses.

### Analysis Databases

- `story_analysis_database.csv`
  Story-by-story analysis database with fields such as framing, angle, content type, tone, stakes, and replicable elements.

- `story_framing_database.csv`
  Framing-focused database for the same story universe, optimized for summary and pattern analysis.

### Report Files

- `top_middle_bottom_100_pageviews_analysis.md`
  Latest memo-style comparison of top, middle, and bottom 100 stories by page views.

- `top_middle_bottom_pageviews_analysis.md`
  Earlier large-sample page-view comparison report.

- `top_vs_bottom_story_patterns.md`
  Top 25 vs bottom 25 framing-pattern comparison report.

- `story_framing_summary.md`
  Cross-dataset framing summary and editorial formulas.

### CSV Output Files

- `top_middle_bottom_100_pageviews_analysis.csv`
  Structured data behind the latest top/middle/bottom 100 comparison.

- `top_middle_bottom_pageviews_analysis.csv`
  Structured data behind the earlier broad top/middle/bottom analysis.

- `top_vs_bottom_story_patterns.csv`
  Structured data behind the top vs bottom pattern report.

### Schema and Build Files

- `analysis_schema.md`
  Field definitions and working rules for the story analysis database.

- `story_framing_schema.md`
  Field definitions and working rules for the framing database.

- `build_story_analysis.py`
  Script that generates `story_analysis_database.csv`.

- `build_framing_database.py`
  Script that generates `story_framing_database.csv` and the framing summary.

## Bottom-Line Takeaways

- The strongest MSN performers are usually event-led, consequence-led, or conflict-led.
- High-performing stories make the stakes visible immediately, often through money, jobs, travel, institutional failure, or public conflict.
- Lower-performing stories tend to be more abstract, more insider-oriented, or more utility-driven without urgency.
- The best reusable lesson is to frame stories around immediate consequence, not just topic relevance.

## Recommended Use

If you need one short report to share, use this memo together with:
- `top_middle_bottom_100_pageviews_analysis.md` for the latest detailed comparison
- `top_vs_bottom_story_patterns.md` for the clearest framing explanation
- `story_framing_summary.md` for repeatable formulas and editorial templates
