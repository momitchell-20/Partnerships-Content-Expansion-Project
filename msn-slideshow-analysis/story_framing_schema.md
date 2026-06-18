# MSN Story Framing Schema

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
