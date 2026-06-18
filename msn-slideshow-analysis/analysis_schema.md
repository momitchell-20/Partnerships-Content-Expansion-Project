# MSN Story Analysis Schema

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
