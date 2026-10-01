# Email Deliverability (Resend)

How verification and password-reset emails are sent, and how to keep them out of spam.

## How email is sent

The API sends plain-text emails through Resend's SMTP relay (`aiosmtplib`, STARTTLS on port 587), not the Resend SDK. The adapter is `src/app/shared/infrastructure/email/smtp_email_sender.py`, built by `get_email_sender` in `src/app/composition/infrastructure.py`.

| Variable | Value |
| --- | --- |
| `SMTP_HOST` | `smtp.resend.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | `resend` |
| `SMTP_PASSWORD` | Resend API key (`re_...`) |
| `SMTP_FROM_ADDRESS` | `Open Projects Hub <no-reply@send.example.com>` |

`get_email_sender` is cached: **restart the API after changing any `SMTP_*` value.**

## Sender address rules

- `SMTP_FROM_ADDRESS` must be a full address on a domain verified in Resend (`no-reply@send.example.com`). A bare domain (`send.example.com`) is rejected by Resend.
- The API refuses to start sending if the value has no `@`.
- Use cases log and swallow send errors, so a bad sender shows up only as an `email.send_failed` log line while the API still returns 200.

## DNS checklist

Add these in your DNS provider (Cloudflare: **DNS only**, not proxied) for the sending subdomain. Resend lists the exact values on the domain page.

| Purpose | Type | Name (relative to root domain) |
| --- | --- | --- |
| DKIM | TXT | `resend._domainkey.send` |
| SPF | CNAME | `rsend.send` |
| SPF | CNAME | `send.send` |
| DMARC | TXT | `_dmarc` = `v=DMARC1; p=none; rua=mailto:<mailbox you read>;` |

DMARC is marked optional in Resend but **Gmail and Yahoo penalise senders without it**. Keep `p=none` while the domain is new. All four rows must show Verified in Resend.

## Resend settings

- Domain → **Configuration**: turn **open tracking and click tracking off**. Verification codes need neither, and tracking adds a third-party domain that hurts delivery.
- Domain → **Enable Sending**: on.

## Verify

1. DNS is public:
   ```bash
   dig +short TXT _dmarc.example.com @8.8.8.8
   ```
2. Send a code to a Gmail address, open it, then **⋮ → Show original**. Expect `SPF: PASS`, `DKIM: PASS` (domain = the sending subdomain) and `DMARC: PASS`.
3. DMARC passes through DKIM alignment with the From domain. A `DMARC: FAIL` on a message sent right after adding the record is usually DNS caching: retest after 30–60 minutes. If it persists, check the `Authentication-Results` header.

## Warm-up (new domains)

A new sending domain has no reputation, so the first emails often land in spam even with correct DNS.

- Mark the message **Not spam**, and reply to it.
- Avoid repeated bulk test sends to one inbox.
- Expect it to settle over a few days of normal use.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing arrives, API returns 200 | Logs for `email.send_failed`; `SMTP_FROM_ADDRESS` format; `SMTP_PASSWORD` is a valid API key; API restarted after `.env` change |
| macOS `CERTIFICATE_VERIFY_FAILED` | See the troubleshooting note in the repo `README.md` |
| Arrives in spam | DMARC record published and verified; tracking off; SPF/DKIM PASS in "Show original"; warm-up |
| `DMARC: FAIL` with DKIM PASS | DNS cache; retest later (see Verify) |

## Known limits

- Resend's relay replaces `Message-ID`, so the app does not set one.
- No `Reply-To` header and no HTML part: the email is plain text.
- Failed sends are logged only; the user is not told.
- Retry and rate limiting are deferred to EPIC-9.
