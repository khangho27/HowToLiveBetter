# Daily English advice for Discord

One compact Discord message with three random entries, translated and shortened
into English by Claude. Scheduled daily at **8 AM America/Los_Angeles**, including
weekends and adjusting automatically for daylight saving time. GitHub queues can
delay delivery, so 8 AM is a target rather than an exact delivery guarantee.

## Enable on your fork

1. Merge the workflow and script into your default branch.
2. Open Settings → Secrets and variables → Actions → Secrets. Add these
   **repository secrets to this repository**:
   - `ANTHROPIC_API_KEY`: your Anthropic Platform API key with available credits.
   - `DISCORD_WEBHOOK_URL`: the webhook copied from your chosen Discord channel.
   Keys in a different repository do not carry over. Never commit either value.
3. Open Actions and enable workflows if prompted. Select **Daily English Advice**
   and use **Run workflow** for an initial test. This posts to the webhook channel
   and consumes Anthropic API credits. A successful manual send counts as today's
   digest, so a later scheduled run that day skips delivery while history exists.
4. Future sends run daily without keeping your computer on. To pause, open this
   workflow's Actions page, select its three-dot menu, and choose Disable workflow.

Optional repository variable: `ADVICE_MODEL` overrides the default
`claude-haiku-4-5-20251001`. Use an Anthropic API model ID available to your account.
No Claude chat subscription is required; translation uses separately billed API usage.

## Content and history

The digest samples local `book/` files in chapters 3, 4, 14, 22, and 23: attention,
time, account security, relaxation, and learning. It excludes entries that match
jurisdiction-specific terms or audience tags and several specialist topics. This
filter is intentionally conservative but is not a substitute for reviewing sources.
Sync your fork from upstream when you want newer book content.

Each tip includes a short English title and summary, the book's evidence grade,
and an immutable link to the exact original entry in the checked-out commit.
The message credits the original book, links CC BY 4.0, and labels the summaries
as translations/adaptations. Existing book content and evidence ratings are unchanged.
The model sees each complete selected entry, including sources and caveats; it is
instructed to preserve limitations. This does not independently verify the book.

The workflow caches successful deliveries to avoid repeats within 30 days where
the pool permits; otherwise it prefers the oldest entries. A cached same-day marker
prevents another send that day. GitHub cache eviction can reset this memory. A
crash between Discord accepting a message and saving the cache can also duplicate
a digest on a later run. Inspect the channel before manually retrying an uncertain
delivery. Errors are visible in Actions; the script does not post failure alerts.
Discord delivery is not retried automatically, to avoid duplicating uncertain sends.

## Validate without credentials or delivery

Run from the repository root with Python 3.11 or later:

```sh
python -m unittest discover -s tools/discord -p 'test_*.py'
python tools/discord/daily_advice.py --list-only
```

No dependencies need installing. Pull-request checks never access secrets, call
the translation API, or post to Discord. The script rejects invalid or oversized
translations rather than cutting off a potentially important caveat.
