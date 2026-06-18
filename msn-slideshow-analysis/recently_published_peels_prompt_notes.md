# Recently Published Peels Prompt Notes

Use these notes when generating peel audits from recently published stories.

## Core Goal

Every `Suggested new headline` must read like a publishable Business Insider headline, not like scaffolding, commentary about the task, or explanation of the ideation process.

## Hard Bans

Do not generate headlines that include or imply any of the following:

- `this story`
- `this piece`
- `this debate`
- `this list`
- `the original headline`
- `worth following up on`
- `hiding underneath`
- `says more than`
- `may resonate beyond`
- `readers`
- `what readers should know`
- `detail readers are most likely to remember`
- `bigger angle than`
- `inside this story`
- `angle inside this story`

If a draft headline contains any of those patterns, rewrite it. Do not ship it.

## Headline Standard

The headline should:

- name the actual subject from the story
- package that subject in a real BI-style frame
- sound like something we would actually publish
- avoid meta language about the prompt, task, or story mechanics

If the model cannot produce a real headline, it should fail the peel instead of outputting a placeholder.

## Peel-Specific Rules

### Peel Option #1

Keep the broader reusable framing logic we were using previously.

- This can be a broad consumer, reaction, takeaway, or utility frame.
- It should still feel like a real headline, not a generic template.

### Peel Option #2

`Peel Option #2` must select one concrete detail and turn it into a real standalone headline.

That detail can be:

- one item from a list
- one product
- one example
- one subgroup
- one location
- one design feature
- one relationship dynamic
- one institutional tension

The headline itself should already reflect that concrete choice.

Bad:

- `The one long term care angle inside this story that could go deeper`
- `The one cover letters angle in this Discourse story that could be peeled out`
- `The one decluttering example on this list that could support a standalone story`

Good:

- `Why attic sanctuaries are becoming a new kind of retreat at home`
- `Why cover letters are quietly losing their place in the hiring process`
- `Why Celebrity's most divisive cruise cabin might actually work`
- `The Trader Joe's beauty buys that actually feel high-end`

### Peel Option #3

`Peel Option #3` should return to the more reusable BI-style packaging we were using before:

- emotional twist
- surprise takeaway
- sharper verdict
- practical warning
- generational mood
- broader implication

It should not drift into generic fallback phrasing.

Bad:

- `The claude code shift hiding underneath this story`
- `The relationship shift hiding underneath this story`
- `The decluttering detail readers are most likely to remember`

Good:

- `The hidden work powering Claude Code's improvement`
- `Why protecting your own balance can put new pressure on a marriage`
- `The care-cost workaround more families may start considering`

## Claude Code Example Fixes

For:

- `Inside the unseen operation to turbocharge Claude Code`

Avoid:

- `Why this claude code story says more than the original headline suggests`
- `The claude code shift hiding underneath this story`

Prefer:

- `Inside the hidden work to improve Claude Code`
- `How Anthropic is trying to make Claude Code better behind the scenes`
- `The unseen effort to sharpen Claude Code`

## Relationship Story Example Fixes

For relationship or family-pressure stories, avoid generic fallback phrasing.

Avoid:

- `The relationship shift hiding underneath this story`

Prefer:

- `Why protecting your own balance can put new pressure on a marriage`
- `What multigenerational living can do to a couple's relationship`
- `The marriage strain that can build when families live with in-laws`

## Review / Travel Example Fixes

For reviews, cabins, trains, cruises, or travel features, prefer publishable consumer or verdict frames.

Avoid:

- `What readers should know about this cruise before booking or buying`

Prefer:

- `What it's really like to stay in Celebrity's Infinite Veranda cabin`
- `Why the smaller Amtrak bunk may be the better sleeper-train choice`
- `What it is really like to sleep in an Amtrak bedroom`

## Quality Check Before Final Output

Before finalizing any report, scan all suggested headlines and reject any that:

- mention `story`, `piece`, `debate`, or `list` in a meta way
- mention `readers`
- sound like prompt scaffolding
- merely describe the ideation process
- fail to name a concrete subject
- would look embarrassing if published as-is

If a headline fails those checks, rewrite it before shipping.
