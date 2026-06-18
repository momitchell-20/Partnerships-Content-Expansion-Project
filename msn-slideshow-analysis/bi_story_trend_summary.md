# BI Story Trend Database Summary

Source file: `/Users/mmitchell/Downloads/evergreen stories pull 2026-06-09T1228.csv`
Rows processed: 1,318

## What This Database Does

This build turns a headline-and-tag export into a queryable story database with controlled framing labels and a retrieval layer built for trend-aware searching.

The key design choice is to keep stable story identity, entity labels, topical buckets, and retrieval hints separate. That prevents broad overmatching, especially for high-frequency names like Elon Musk.

## Identity Layer

- Duplicate URL rows: 344
- Duplicate URL families: 172
- Source batches represented: 1

Use `canonical_url` as the dedupe key and `story_family_key` when collapsing repeated exports or multiple versions of the same story.

## Top Story Mix

Most common topic clusters:
- other: 298
- entertainment and culture: 216
- health and wellness: 118
- politics and public conflict: 72
- real estate and housing: 71
- retail and shopping: 71
- travel and transportation: 66
- food and consumer habits: 63
- education and family: 54
- careers and labor: 47
- personal finance and affordability: 46
- history and explainer: 31

Most common main-point labels:
- Current development: 629
- Cultural reaction: 189
- Utility payoff: 114
- Relocation tradeoff: 80
- Public conflict: 69
- Travel disruption: 68
- Career impact: 43
- Cost-of-living impact: 41
- Comparison tradeoff: 25
- Health outcome: 16
- Future implications: 13
- Legal fallout: 9

Most common framing labels:
- straight-news framing: 769
- human-interest lesson framing: 218
- utility / decision-aid framing: 121
- conflict / fallout framing: 77
- housing / relocation tradeoff framing: 38
- travel-disruption framing: 20
- science/tech implication framing: 19
- policy-to-wallet framing: 18
- career-security framing: 18
- business consequence framing: 14

Most common trend anchors:
- broad news interest: 534
- celebrity attention and audience interest: 216
- health habits and outcomes: 118
- public conflict and reputation risk: 72
- housing costs and relocation: 71
- travel disruption and trip reliability: 66
- workforce change: 47
- money pressure and affordability: 41
- public-figure reputation and attention: 28
- AI product adoption and consequences: 25
- Costco coverage: 12
- space and aerospace execution: 12

## Trend Fit Distribution

- Median trend fit score: 35
- Range: 15 to 95

Trend-fit bands:
- high: 5
- medium-high: 130
- medium: 423
- low: 760

## Musk Guardrail Readout

- Rows with Musk in the headline or tags: 25
- Rows that survive the narrower business-angle filter: 11

This is the main proof that the database is not returning every Musk story for every Musk query.

## Example Rows

- Artificial Intelligence | xAI | AI and automation | AI product adoption and consequences | 55
- We created the first-ever searchable database of 259 LGBTQ characters in cartoons that bust the myth that kids can't handle inclusion |  | education and family | broad news interest | 20
- Grok has an AI chatbot for young kids. I used it to try to understand why. | xAI | AI and automation | consumer AI behavior | 75
- A competitive eater shares her diet and workout routine to stay healthy while tackling 10,000-calorie food challenges | workouts | health and wellness | health habits and outcomes | 25
- At Rosemead High, generations of students were harassed or groomed for sex as they tried to get an education | will varner | education and family | broad news interest | 35

## Practical Query Guidance

- For Musk, search the `trend_anchor` field first, not just `primary_entity`.
- For SpaceX, prefer `trend_anchor` values like `SpaceX financing / IPO` or `SpaceX launch system`.
- For AI coverage, use `topic_cluster = ai_and_automation` plus a specific `trend_anchor`.
- For company coverage, combine `primary_entity`, `entity_type`, `topic_cluster`, and `main_point_of_interest`.
- For broad searches, use `trend_fit_score >= 60` to keep the results focused.
