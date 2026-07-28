"""
EPGHUB command line interface.

    epghub update              # update the EPG once (default command)
    epghub schedule            # first update, then keep updating on CRON_TRIGGER
    epghub update -c my.yaml -o ./out

Also runnable without installation as `python -m epg.cli` or through the
back-compat wrappers `python main.py` / `python scheduler.py`.

Behaviour is configured by environment variables (TZ, CRON_TRIGGER,
XMLTV_URL, MAX_WORKERS, CF_PAGES, DEPLOY_HOOK, CLOUDFLARE_API_TOKEN),
see README. Paths can be overridden per invocation with --config/--output.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib import resources

from croniter import croniter
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml import etree

from epg import utils
from epg.generator import diyp, xmltv
from epg.scraper import __xmltv

CF_PAGES = os.getenv("CF_PAGES")
DEPLOY_HOOK = os.getenv("DEPLOY_HOOK")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
XMLTV_URL = os.getenv("XMLTV_URL", "")
TZ = os.getenv("TZ")
CRON_TRIGGER = os.getenv("CRON_TRIGGER", "0 0 * * *")
try:
    MAX_WORKERS = max(1, int(os.getenv("MAX_WORKERS", "8")))
except ValueError:
    MAX_WORKERS = 8

DEFAULT_CONFIG = os.path.join("config", "channels.yaml")
DEFAULT_OUTPUT = "web"


def _data_dir():
    """Packaged data (templates, xmltv.dtd) shipped inside the epg package."""
    return resources.files("epg").joinpath("data")


def update(config_path: str, output_dir: str) -> int:
    """Run one full EPG update + static site generation. Returns exit code."""
    if TZ is None:
        print(
            "!!!Please set TZ environment variables to define timezone or it will use system timezone by default!!!"
        )
    next_cron_time = (
        croniter(CRON_TRIGGER, datetime.now(timezone.utc))
        .get_next(datetime)
        .replace(tzinfo=timezone.utc)
        .astimezone()
    )

    data_dir = _data_dir()
    with (data_dir / "xmltv.dtd").open("r") as dtd_file:
        dtd = etree.DTD(dtd_file)

    now = datetime.now()
    current_timezone = now.astimezone().tzinfo
    timezone_name = current_timezone.tzname(now) if current_timezone else "UTC"
    timezone_offset = now.astimezone().strftime("%z")
    print("use timezone:", timezone_name, f"UTC{timezone_offset}", flush=True)

    epg_path = os.path.join(output_dir, "epg.xml")
    os.makedirs(output_dir, exist_ok=True)

    channels = utils.load_config(config_path)
    if not channels:
        print(f"!!!No valid channels defined in {config_path}, nothing to do!!!")
        return 1

    if XMLTV_URL == "":
        print("!!!Please set XMLTV_URL environment variables to reuse XML!!!")
    else:
        print("reuse XML:", XMLTV_URL, flush=True)
        xml_channels = __xmltv.get_channels(XMLTV_URL, dtd)
        # Reuse channels
        if xml_channels != []:
            xml_result = utils.copy_channels(channels, xml_channels)
            num_reuse_channels = xml_result[0]
            xml_dates = xml_result[1]
            if xml_dates:
                min_xml_date = min(xml_dates)
                max_xml_date = max(xml_dates)
            else:
                print("xml_dates is empty")
                min_xml_date = None
                max_xml_date = None
            print(
                f"number of reused channels: {num_reuse_channels}/{len(channels)} from {min_xml_date} to {max_xml_date}",
                flush=True,
            )

    print(f"refreshing with {MAX_WORKERS} workers...", flush=True)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(
            executor.map(
                utils.update_channel_full, channels, range(1, len(channels) + 1)
            )
        )
    num_refresh_channels = sum(1 for refreshed in results if refreshed)

    print(
        f"number of refreshed channels: {num_refresh_channels}/{len(channels)}",
        flush=True,
    )

    print("deploying...", flush=True)
    print("file path:", epg_path, flush=True)
    xmltv.write(epg_path, channels, "epghub")

    with open(epg_path, "rb") as xml:
        root = etree.XML(xml.read())
    valid = dtd.validate(root)
    if not valid:
        print(dtd.error_log.filter_from_errors()[0])

    diyp.write(os.path.join(output_dir, "diyp_files"), channels)

    # Render the site index from the packaged template
    templates_dir = data_dir / "templates"
    env = Environment(
        loader=FileSystemLoader(searchpath=str(templates_dir)),
        autoescape=select_autoescape(["html", "xml", "jinja2"]),
    )
    template = env.get_template("index.html.jinja2")

    title = "電視直播節目表"
    channel_list = [channel.metadata["name"][0] for channel in channels]
    first_channel = channel_list[0]
    channel_list = channel_list[1:]

    rendered_html = template.render(
        title=title,
        channel_list=channel_list,
        first_channel=first_channel,
        num_refresh_channels=num_refresh_channels,
        num_channels=len(channels),
        last_update_time=datetime.now().astimezone().isoformat(timespec="seconds"),
        next_update_time=next_cron_time,
        update_trigger=CRON_TRIGGER,
        timezone_offset=timezone_offset,
    )

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
        index_file.write(rendered_html)
    for static_file in ("404.html", "404.json", "robots.txt"):
        shutil.copyfile(
            str(templates_dir / static_file),
            os.path.join(output_dir, static_file),
        )

    if CF_PAGES is not None:
        if CLOUDFLARE_API_TOKEN is None:
            print(
                "!!!Please set CLOUDFLARE_API_TOKEN environment variables to deploy automatically!!!"
            )
        if DEPLOY_HOOK is None:
            print(
                "!!!Please set DEPLOY_HOOK environment variables to deploy automatically!!!"
            )
        if DEPLOY_HOOK is not None and CLOUDFLARE_API_TOKEN is not None:
            # Run wrangler without a shell so values coming from environment
            # variables cannot be used for command injection.
            subprocess.run(
                [
                    "npx",
                    "--yes",
                    "wrangler",
                    "deploy",
                    "--var",
                    f"DEPLOY_HOOK:{DEPLOY_HOOK}",
                    "--triggers",
                    CRON_TRIGGER,
                ],
                cwd=os.path.join(os.getcwd(), "workers"),
                check=False,
            )
    return 0


def schedule(config_path: str, output_dir: str) -> int:
    """Run one update now, then keep updating on CRON_TRIGGER forever."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    try:
        cron_trigger = CronTrigger.from_crontab(CRON_TRIGGER, timezone.utc)
    except ValueError as exc:
        print(f"!!!Invalid CRON_TRIGGER {CRON_TRIGGER!r}: {exc}!!!")
        return 1

    def run_update() -> None:
        # Each run in a fresh interpreter, without a shell: scrapers and
        # in-process caches never leak state between scheduled runs.
        print("CRON task：", time.strftime("%Y-%m-%d %H:%M:%S"), flush=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "epg.cli",
                "update",
                "--config",
                config_path,
                "--output",
                output_dir,
            ],
            check=False,
        )

    scheduler = BlockingScheduler()
    scheduler.add_job(run_update, cron_trigger)
    print("Run first update...", flush=True)
    run_update()
    print(f"Start scheduler with cron trigger: {CRON_TRIGGER}", flush=True)
    scheduler.start()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="epghub",
        description="A multi-source EPG builder with extensibility.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="update",
        choices=("update", "schedule"),
        help="update: run once (default); schedule: run on CRON_TRIGGER",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help=f"channels config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"output directory for the static site (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args(argv)
    if args.command == "schedule":
        return schedule(args.config, args.output)
    return update(args.config, args.output)


if __name__ == "__main__":
    sys.exit(main())
