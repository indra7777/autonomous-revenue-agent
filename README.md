# Autonomous Revenue Agent

An always-on, zero-capital revenue scout that runs every four hours, scans free public feeds, ranks quick revenue opportunities, writes a single human instruction, and notifies the overseer through Slack or email.

The agent is intentionally approval-gated: it does not create accounts, buy ads, submit proposals, or send public posts by itself. It prepares the exact next action so the human can approve and execute it in under ten minutes.

## What It Does

- Scans free public sources:
  - Reddit JSON feeds for small gigs and freelance leads.
  - Hacker News Algolia search for "looking for" and launch/service opportunities.
  - Google News RSS for affiliate/product angles.
  - Optional custom RSS feeds through `CUSTOM_FEED_URLS`.
- Scores opportunities by ease, payment probability, and repeatability.
- Produces one instruction file per run under `reports/`.
- Keeps simple state under `state/`.
- Sends the latest instruction to Slack and/or email.
- Sends the latest instruction to a GitHub Issue inbox with no extra secrets.
- Runs on GitHub Actions every four hours with no paid server.

## Local Run

```bash
python3 -m unittest discover -s tests
python3 -m revenue_agent --once
```

The latest instruction is written to:

```text
reports/latest.md
```

## Slack Notification

The workflow automatically posts to a GitHub issue named `Autonomous Revenue Agent Inbox`. Slack is optional.

Create a Slack incoming webhook and set this secret in GitHub:

```text
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Optional Email Notification

Set these GitHub secrets if you want email delivery:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
EMAIL_FROM
EMAIL_TO
```

## Free Deployment

1. Push this folder to a public GitHub repository.
2. Add `SLACK_WEBHOOK_URL` as a repository secret.
3. Enable GitHub Actions.
4. Run the `Autonomous Revenue Agent` workflow manually once.

The scheduled workflow uses:

```yaml
cron: "17 */4 * * *"
```

That runs every four hours, offset from the top of the hour to reduce GitHub schedule congestion.

## Human Overseer Routine

Every day, open the latest Slack/email message and do only the requested action. Then update revenue manually in `state/revenue.json` if money was earned. The agent reads that file to decide whether to reinvest.

## Boundaries

The agent will not:

- Create third-party accounts or API keys.
- Circumvent platform terms or anti-spam rules.
- Send paid ads, public posts, DMs, or proposals without human approval.
- Pretend to have portfolio items, credentials, or experience it does not have.

It will:

- Find leads.
- Draft exact messages.
- Decide whether to continue, stop, or reduce effort.
- Generate task files for sub-agents under `state/subagents/`.
- Keep the daily human workload small.

## 💰 Bounty Contribution

- **Task:** Autonomous Revenue Agent Inbox
- **Reward:** $21
- **Source:** GitHub-Paid
- **Date:** 2026-04-27

