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
Though you can run your telegram-bot-server in polling mode, it is recommended to run them in webhook mode in production. `frappe_telegram` comes with utility commands to easily add webhook location-blocks to your bench-nginx.conf.

It might be a good idea to backup your existing nginx.conf (bench/config/nginx.conf) before making any changes.

```bash
$ bench telegram nginx-add --help
Usage: bench  telegram nginx-add [OPTIONS] TELEGRAM_BOT

  Modifies existing nginx-config for telegram-webhook support. You can
  specify webhook url, port & nginx_path to override existing value in
  TelegramBot Doc

  Args:
      webhook_port: Specify the port to override
      webhook_url: Specify the url to override existing webhook_url
      nginx_path: Use custom path in nginx location block

Options:
  --webhook-port INTEGER  The port to listen on for webhook events. Default is
                          8080

  --webhook-url TEXT      Explicitly specify webhook URL. Useful for NAT,
                          reverse-proxy etc

  --nginx-path TEXT       Use custom nginx path for webhook reverse-proxy
  --help                  Show this message and exit.
```
Similarly, you can remove the webhook location block with `nginx-remove`.
Test and reload nginx to have the changes reflected.

```bash
# Test nginx config
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

# Reload nginx
$ sudo service nginx reload
```