# Email Notification Setup

The weekly metrics report can be automatically emailed to **preston.fay@kearney.com**.

## Overview

The metrics report workflow sends two types of notifications:

1. **GitHub Issue** - Created automatically in the repository with the markdown report
2. **Email Notification** - HTML-formatted email sent to preston.fay@kearney.com

## Prerequisites

- Repository admin access to configure GitHub Secrets
- Email account with SMTP access (Gmail or Kearney email)
- 2-factor authentication enabled (for Gmail)

## Setup Steps

### Option A: Gmail Setup (Recommended for Testing)

#### 1. Enable 2-Factor Authentication

- Go to your Google Account: https://myaccount.google.com/security
- Enable 2-Step Verification if not already enabled

#### 2. Generate App-Specific Password

- Visit: https://myaccount.google.com/apppasswords
- Select:
  - **App:** Mail
  - **Device:** GitHub Actions (or Other: Metrics Dashboard)
- Click **Generate**
- **Copy the 16-character password** (you won't see it again)

#### 3. Add GitHub Secrets

Navigate to repository settings:

```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

Add two secrets:

**Secret 1:**
- Name: `SMTP_USERNAME`
- Value: `your-email@gmail.com`

**Secret 2:**
- Name: `SMTP_PASSWORD`
- Value: `[16-character app password from step 2]`

### Option B: Kearney SMTP Setup

If you have access to Kearney's SMTP server:

#### 1. Get SMTP Server Details

Contact Kearney IT to obtain:
- SMTP server address (e.g., `smtp.kearney.com`)
- Port (typically 587 for TLS or 465 for SSL)
- Authentication requirements

#### 2. Update Workflow Configuration

Edit `.github/workflows/metrics-report.yml`:

```yaml
env:
  RECIPIENT_EMAIL: preston.fay@kearney.com
  SMTP_SERVER: smtp.kearney.com  # Update this
  SMTP_PORT: 587                   # Update this
```

#### 3. Add GitHub Secrets

Add these secrets in repository settings:

**Secret 1:**
- Name: `SMTP_USERNAME`
- Value: `preston.fay@kearney.com` (or your Kearney email)

**Secret 2:**
- Name: `SMTP_PASSWORD`
- Value: Your Kearney email password or application token

## Testing Email Delivery

### Manual Workflow Trigger

1. Go to: **Actions** → **Metrics Weekly Report**
2. Click **Run workflow**
3. Select branch: `main`
4. Click **Run workflow**

### Verify Delivery

1. Check **preston.fay@kearney.com** inbox
2. Look for subject: "Weekly Metrics Report - Week of YYYY-MM-DD"
3. Verify HTML formatting displays correctly
4. If not received, check **spam/junk folder**

### Check Workflow Logs

If email not received:

1. Go to: **Actions** → Failed workflow run
2. Click on **send-email** job
3. Review logs for error messages
4. Common errors:
   - Authentication failure → Check SMTP credentials
   - Connection timeout → Check SMTP server/port
   - Invalid recipient → Verify email address

## Email Content

The HTML email includes:

- **Header:** Purple Kearney branding with report title
- **Executive Summary:** DORA rating and key metrics
- **DORA Metrics:** Deployment frequency, lead time, MTTR, change failure rate
- **AI Contribution:** Collaborative work percentage and lines of code
- **AI Review Impact:** Coverage and acceptance rates
- **GitHub Collaboration:** PR cycle time and velocity (if available)
- **Recommendations:** Automated suggestions based on trends
- **Footer:** Links to dashboard and repository

## Scheduled Delivery

The email is sent automatically:

- **Schedule:** Every Monday at 9:00 AM UTC
- **Trigger:** After metrics collection workflow completes
- **Recipients:** preston.fay@kearney.com (configured in workflow)

To modify the schedule, edit `.github/workflows/metrics-report.yml`:

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Modify this line
```

Cron syntax:
- `0 9 * * 1` = 9:00 AM UTC, every Monday
- `0 9 * * 5` = 9:00 AM UTC, every Friday
- `0 14 * * 1` = 2:00 PM UTC, every Monday

## Troubleshooting

### Email Not Received

**Check 1: Verify secrets are set**
```
Repository → Settings → Secrets and variables → Actions
```
Ensure `SMTP_USERNAME` and `SMTP_PASSWORD` exist.

**Check 2: Test SMTP credentials locally**
```python
import smtplib
from email.mime.text import MIMEText

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'app-password')
server.quit()
print("SMTP authentication successful")
```

**Check 3: Review workflow logs**
- Go to failed workflow run
- Click **send-email** job
- Look for error messages in logs

### HTML Not Formatting Correctly

**Issue:** Email displays plain text instead of HTML

**Solution:** Some email clients block HTML. Try:
- Opening email in different client (Gmail web, Outlook, Apple Mail)
- Checking if client has "Display HTML" setting enabled
- Viewing the attached markdown file instead

**Issue:** Purple colors not showing

**Solution:** Email uses inline CSS which should work in all clients. If colors missing:
- Check email client security settings
- Try viewing in Gmail web interface
- Verify HTML file was generated correctly

### Authentication Failures

**Gmail Error: "Username and Password not accepted"**

**Solution:**
- Verify you're using app-specific password, NOT your Google account password
- Ensure 2-factor authentication is enabled
- Regenerate app password if needed
- Check for typos in GitHub secret

**Kearney SMTP Error: "Authentication failed"**

**Solution:**
- Verify SMTP server address and port
- Contact Kearney IT to confirm SMTP access is enabled
- Check if VPN or firewall is blocking connection
- Verify username format (may need domain: `KEARNEY\username`)

## Security Considerations

### Secrets Management

- **NEVER** commit SMTP credentials to repository
- **ALWAYS** use GitHub Secrets for sensitive data
- **ROTATE** app passwords periodically (every 90 days)
- **REVOKE** app passwords if compromised

### Email Content

The email contains:
- ✅ Aggregated metrics (safe to share)
- ✅ Trends and summaries (safe to share)
- ❌ NO source code
- ❌ NO credentials
- ❌ NO personally identifiable information

### Access Control

Who can trigger the workflow:
- Repository admins (via manual workflow dispatch)
- GitHub Actions (via scheduled cron job)
- Metrics collection workflow (via workflow_run trigger)

## Additional Recipients

To add more email recipients:

Edit `.github/workflows/metrics-report.yml`:

```yaml
env:
  RECIPIENT_EMAIL: preston.fay@kearney.com,additional@email.com
```

Separate multiple emails with commas.

## Disabling Email Notifications

To disable email while keeping GitHub Issues:

Comment out the `send-email` job in `.github/workflows/metrics-report.yml`:

```yaml
# send-email:
#   name: Send Email Notification
#   needs: generate-weekly-report
#   runs-on: ubuntu-latest
#   ...
```

Or remove the SMTP secrets from repository settings.

## Support

For issues with:
- **GitHub Actions:** Check workflow logs and GitHub Actions documentation
- **SMTP Setup:** Contact your email provider's support
- **Kearney SMTP:** Contact Kearney IT support
- **Report Content:** Review metrics collection workflow logs

## References

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [GitHub Actions Send Mail](https://github.com/dawidd6/action-send-mail)
- [Cron Schedule Syntax](https://crontab.guru/)
