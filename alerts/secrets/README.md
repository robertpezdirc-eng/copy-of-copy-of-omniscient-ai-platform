This directory holds secret files used by Alertmanager via Docker Secrets.

Required files:

- slack_webhook_url.txt: contains the Slack incoming webhook URL on a single line.
- smtp_password.txt: contains the SMTP password for the configured SMTP user.

Security notes:

- Do NOT commit real secrets to version control.
- Consider adding these files to your global gitignore if needed.
- The docker-compose.yml maps these into the container as Docker Secrets under /run/secrets/.

Quickstart:

1) Create the directory if not present: alerts/secrets/
2) Put your secrets:
   - alerts/secrets/slack_webhook_url.txt
   - alerts/secrets/smtp_password.txt
3) Select the secure config by setting env var ALERTMANAGER_CONFIG=alertmanager.secure.yml before starting compose.