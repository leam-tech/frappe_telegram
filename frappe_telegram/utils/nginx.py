import os
import re
import sys
import subprocess
import crossplane

import frappe
from .bench import get_bench_path, get_bench_name


def add_nginx_config(
        telegram_bot: str,
        webhook_url=None,
        webhook_port=None,
        webhook_nginx_path=None):
    if not frappe.db.exists("Telegram Bot", telegram_bot):
        frappe.throw("TelegramBot: {} not found".format(telegram_bot))

    telegram_bot = frappe.get_doc("Telegram Bot", telegram_bot)
    if not webhook_url:
        webhook_url = telegram_bot.webhook_url
    if not webhook_port:
        webhook_port = telegram_bot.webhook_port
    if not webhook_nginx_path:
        webhook_nginx_path = telegram_bot.webhook_nginx_path

    config = get_parsed_bench_nginx_config()

    remove_upstream(config, telegram_bot=telegram_bot.name)
    remove_location(config, telegram_bot=telegram_bot.name)
    add_upstream(config, telegram_bot=telegram_bot.name, port=webhook_port)
    add_location(config, telegram_bot=telegram_bot.name, path=webhook_nginx_path)

    nginx_raw = crossplane.build(config["parsed"])
    nginx_raw = re.sub(r"}\n([^\n])", r"}\n\n\1", nginx_raw)
    write_config(nginx_raw)


def remove_nginx_config(telegram_bot: str):
    config = get_parsed_bench_nginx_config()

    remove_upstream(config, telegram_bot=telegram_bot)
    remove_location(config, telegram_bot=telegram_bot)

    nginx_raw = crossplane.build(config["parsed"])
    nginx_raw = re.sub(r"}\n([^\n])", r"}\n\n\1", nginx_raw)
    write_config(nginx_raw)


def add_upstream(config: dict, telegram_bot: str, port: int):
    directive = dict(
        directive="upstream", args=[get_telegram_upstream_name(telegram_bot=telegram_bot)],
        block=[
            dict(directive="#", comment=f" TelegramBot: {telegram_bot}", line=1),
            dict(directive="server", args=["127.0.0.1:" + str(port), "fail_timeout=0"])
        ]
    )

    # Assuming we have two upstream blocks already (gunicorn, socketio)
    insert_at = config["parsed"].index(
        list(filter(lambda x: x["directive"] == "upstream", config["parsed"]))[-1]) + 1
    config["parsed"].insert(insert_at, directive)


def remove_upstream(config: dict, telegram_bot: str):
    upstream_name = get_telegram_upstream_name(telegram_bot=telegram_bot)
    config["parsed"] = list(filter(
        lambda x: x["directive"] != "upstream" or x["args"][0] != upstream_name, config["parsed"]))


def add_location(config, telegram_bot: str, path: str):
    directive = dict(
        directive="location", args=[path],
        block=[
            dict(directive="#", comment=f" TelegramBot: {telegram_bot}", line=1),
            dict(directive="proxy_pass",
                 args=[f"http://{get_telegram_upstream_name(telegram_bot=telegram_bot)}"])
        ]
    )

    server_directive = next(filter(lambda x: x["directive"] == "server", config["parsed"]))
    webserver_location = next(
        filter(lambda x: x["args"][0] == "@webserver",
               server_directive["block"]))
    insert_at = server_directive["block"].index(webserver_location) + 1
    server_directive["block"].insert(insert_at, directive)


def remove_location(config, telegram_bot: str):
    upstream_loc = "http://" + get_telegram_upstream_name(telegram_bot=telegram_bot)
    server_directive = next(filter(lambda x: x["directive"] == "server", config["parsed"]))
    location_directives = filter(lambda x: x["directive"] == "location", server_directive["block"])
    for directive in location_directives:
        if not len(directive.get("block", [])):
            continue

        for block in directive["block"]:
            if block["directive"] == "proxy_pass" and block["args"][0] == upstream_loc:
                server_directive["block"].remove(directive)
                break


def write_config(content):
    local_file = get_nginx_config_path()
    with open(local_file, "w") as f:
        f.write(content)


def get_parsed_bench_nginx_config():
    """
    Returns a JSON representation of local bench nginx conf if it exists
    """
    root_path = get_nginx_root_config_path()
    local_path = os.path.normpath(get_nginx_config_path())

    nginx_parsed = crossplane.parse(
        filename=root_path,
        comments=True,  # we need the comments to be intact
    )
    if nginx_parsed["status"] != "ok":
        print(nginx_parsed)
        print("Please fix your current nginx-config")
        return

    # Now, we parsed the whole nginx-config on the system.
    # We have to narrow down to our bench-nginx config file
    for parsed_file in nginx_parsed["config"]:
        file_path = parsed_file["file"]
        if os.path.islink(file_path):
            file_path = os.readlink(file_path)

        if os.path.normpath(file_path) == local_path:
            # Found it!
            return parsed_file

    print("We were not able to find the current bench's nginx file" +
          " included within {}".format(root_path))
    print("Please setup production to have it done automatically by bench")
    frappe.throw("Failed getting parsed nginx config")


def get_nginx_root_config_path() -> str:
    """
    Returns the main nginx-config path
    This is usually /etc/nginx/nginx.conf
    It is read by executing `nginx -V` and checking the value of --conf-path
    """

    nginx_verbose = subprocess.check_output(
        ["nginx", "-V"], stderr=subprocess.STDOUT).decode(sys.stdout.encoding).strip()
    match = re.match(r"^.*(--conf-path=([\.\/a-zA-Z]+)).*$", nginx_verbose, flags=re.S)
    if match:
        return match.group(2)

    frappe.throw(
        "Please make sure you nginx installed" +
        " and is accessible by current user to execute `nginx -V`")


def get_nginx_config_path() -> str:
    """
    Returns the nginx-config path of current bench
    """
    nginx_conf = os.path.join(get_bench_path(), "config", "nginx.conf")
    if not os.path.exists(nginx_conf):
        frappe.throw(
            "Please generate nginx file using 'bench setup nginx' before this action")

    return nginx_conf


def get_telegram_upstream_name(telegram_bot):
    """
    Gets the nginx-upstream name for telegram-bot
    eg: frappe-bench-random-chat
    """
    return f"{get_bench_name()}-{frappe.scrub(telegram_bot).replace('_', '-')}"
