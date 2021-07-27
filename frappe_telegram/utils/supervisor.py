import os
import configparser
from frappe.translate import get_bench_dir
from frappe.utils import get_bench_path, get_site_path


"""
supervisor.conf follows configparser format (Win-INI style)
We will have a new process group for all the telegram-bots
"""


def add_supervisor_entry(
        botname, polling=False, poll_interval=0,
        webhook=False, webhook_port=0, webhook_url=None):
    config = get_supervisor_config()

    # Program
    program_name, program = get_bot_program(
        config=config, botname=botname, polling=polling, poll_interval=poll_interval,
        webhook=webhook, webhook_port=webhook_port, webhook_url=webhook_url)

    config[program_name] = program

    # Bot Group
    group_name = get_bot_group_name()
    bot_programs = []
    if group_name in config:
        bot_programs = config[group_name]["programs"].split(",")

    bot_programs.append(program_name.replace("program:", ""))
    config[group_name] = {"programs": ",".join(bot_programs)}

    write_supervisor_config(config)


def remove_supervisor_entry(botname):
    config = get_supervisor_config()

    # Remove Program Entry
    program_name = get_bot_program_name(botname)
    if program_name in config:
        del config[program_name]

    # Remove Group Entry
    group_name = get_bot_group_name()
    bot_programs = []
    if group_name in config:
        bot_programs = config[group_name]["programs"].split(",")

    bot_programs.remove(program_name.replace("program:", ""))

    if len(bot_programs):
        config[group_name] = {"programs": ",".join(bot_programs)}
    elif group_name in config:
        del config[group_name]

    write_supervisor_config(config)


def get_bot_program(config, botname, **kwargs):
    program_name = get_bot_program_name(botname)
    logs = get_bot_log_paths(botname)

    command = "bench telegram start-bot"
    for k, v in kwargs.items():
        if not v:
            continue
        k = k.replace("_", "-")
        command += f" --{k} {v}"

    program = {
        "command": command,
        "priority": 1,
        "autostart": "true",
        "autorestart": "true",
        "stdout_logfile": logs[0],
        "stderr_logfile": logs[1],
        "user": guess_user_from_web_program(config=config),
        "directory": os.path.abspath(get_site_path(".."))
    }

    return program_name, program


def get_supervisor_config() -> configparser.ConfigParser():
    supervisor_conf = os.path.join(get_bench_path(), "config", "supervisor.conf")
    if not os.path.exists(supervisor_conf):
        raise Exception(
            "Please generate supervisor file using 'bench setup supervisor' before this action")

    config = configparser.ConfigParser()
    config.read(supervisor_conf)

    return config


def write_supervisor_config(config: configparser.ConfigParser):
    supervisor_conf = os.path.join(get_bench_path(), "config", "supervisor.conf")
    with open(supervisor_conf, 'w') as configfile:
        config.write(configfile)

    # TODO: Ask to restart supervisorctl or do automatically


def guess_user_from_web_program(config: configparser.ConfigParser):
    web_program_name = f"program:{get_bench_name()}-frappe-web"
    if web_program_name not in config:
        return

    return config[web_program_name]["user"]


def get_bot_log_paths(botname):
    logs_path = os.path.abspath(os.path.join(get_bench_dir(), "logs"))
    stdout = os.path.join(logs_path, f"bot-{botname}.log")
    stderr = os.path.join(logs_path, f"bot-{botname}.error.log")

    return stdout, stderr


def get_bot_program_name(botname):
    return f"program:{get_bench_name()}-telegram-bot-{botname}"


def get_bot_group_name():
    return f"group:{get_bench_name()}-telegram-bots"


def get_bench_name():
    return os.path.basename(os.path.abspath(get_bench_path()))
