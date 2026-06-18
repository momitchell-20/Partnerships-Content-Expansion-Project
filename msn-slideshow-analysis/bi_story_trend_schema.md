# BI Story Trend Database Schema

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
