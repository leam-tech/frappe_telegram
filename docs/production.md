# Setting Up for Production

We can have the bot running in its own supervisor process, independent from frappe processes. You can update your supervisor configuration with the following commands

```bash
$ bench telegram supervisor-add --help
Usage: bench  telegram supervisor-add [OPTIONS] TELEGRAM_BOT

  Sets up supervisor process

Options:
  --polling               Start bot in Polling Mode
  --poll-interval FLOAT   Time interval between each poll. Default is 0
  --webhook               Start Webhook Server
  --webhook-port INTEGER  The port to listen on for webhook events. Default is
                          8080

  --webhook-url TEXT      Explicitly specify webhook URL. Useful for NAT,
                          reverse-proxy etc

  --help                  Show this message and exit.
```

All the parameters of `start-bot` are available here. Similarly, you can remove the supervisor process with `supervisor-remove`.

Please do update supervisor after configuration changes are made
```bash
$ sudo supervisorctl update
```

## Webhooks & Nginx Guide
⌛ Coming soon!