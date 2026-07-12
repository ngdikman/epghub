"""
This file includes utils for grab and generate EPG.
They are referenced in main.py.

Channel updates may run concurrently (see main.py), so per-channel
progress is buffered and printed in one atomic block per channel.
"""

import yaml
import importlib
from epg.model import Channel
from datetime import datetime, date, timedelta
from epg.scraper import tz_shanghai

VALID_REFRESH = ("once", "today")


def _validate_channel_config(channel_id: str, metadata) -> list[str]:
    """
    Validate a single channel config entry.

    Returns:
        list[str]: Human-readable problems; empty if the entry is valid.
    """
    problems = []
    if not isinstance(metadata, dict):
        return [f"channel '{channel_id}': config must be a mapping"]
    name = metadata.get("name")
    if not isinstance(name, list) or len(name) == 0 or not all(name):
        problems.append(
            f"channel '{channel_id}': 'name' must be a non-empty list of display names"
        )
    elif isinstance(name[0], str) and any(
        seq in name[0] for seq in ("/", "\\", "..")
    ):
        # The first display name is used as the DIYP directory name and
        # as the ch= query value; path separators in it cannot round-trip
        # through the static file layout, so reject them up front.
        problems.append(
            f"channel '{channel_id}': first display name {name[0]!r} must not "
            "contain '/', '\\' or '..' (it is used as the DIYP directory and "
            "query name)"
        )
    scraper = metadata.get("scraper")
    if not isinstance(scraper, dict) or len(scraper) == 0:
        problems.append(
            f"channel '{channel_id}': 'scraper' must be a mapping of scraper name -> scraper id"
        )
    refresh = metadata.get("refresh", "once")
    if refresh not in VALID_REFRESH:
        problems.append(
            f"channel '{channel_id}': 'refresh' must be one of {VALID_REFRESH}, got {refresh!r}"
        )
    for key in ("recap", "preview"):
        value = metadata.get(key, 0)
        if not isinstance(value, int) or value < 0:
            problems.append(
                f"channel '{channel_id}': '{key}' must be a non-negative integer, got {value!r}"
            )
    xml_lang = metadata.get("xml_lang")
    if xml_lang is not None and (not isinstance(xml_lang, str) or not xml_lang.strip()):
        problems.append(
            f"channel '{channel_id}': 'xml_lang' must be a non-empty language code, got {xml_lang!r}"
        )
    return problems


def load_config(path: str) -> list[Channel]:
    """
    Load channels config from yaml file.

    Invalid channel entries are reported and skipped instead of
    crashing later in the middle of an update run.

    Args:
        path (str): The path of the yaml file.

    Returns:
        list[Channel]: The channels.
    """
    channels = []
    try:
        with open(path, "r", encoding="utf-8") as stream:
            channels_config = yaml.safe_load(stream)
    except FileNotFoundError:
        print(f"!!!Config file not found: {path}!!!")
        return channels
    except yaml.YAMLError as exc:
        print(f"!!!Config file is not valid YAML: {path}!!!")
        print(exc)
        return channels
    if not isinstance(channels_config, dict):
        print(f"!!!Config file must be a mapping of channel id -> config: {path}!!!")
        return channels
    for channel_id in channels_config:
        metadata = channels_config[channel_id]
        problems = _validate_channel_config(channel_id, metadata)
        if problems:
            for problem in problems:
                print("!!!Invalid config,", problem, "-> channel skipped!!!")
            continue
        metadata.setdefault("refresh", "once")
        metadata.update(
            {"last_update": datetime(1970, 1, 1, 0, 0, 0, tzinfo=tz_shanghai)}
        )
        channels.append(
            Channel(
                channel_id,
                metadata,
                lambda channel, date: scrap_channel(channel, channels_config, date),
            )
        )
    return channels


def scrap_channel(channel: Channel, channels_config, date: date | None = None) -> bool:
    """
    Scrap channel with the given date.

    Args:
        channel (Channel): The channel to scrap.
        channels_config (dict): The channels config.
        date (date, optional): The date to scrap. Defaults to today's date.

    Returns:
        bool: True if the channel is updated, False otherwise.
    """
    if date is None:
        date = datetime.today().date()
    channel.metadata["last_scraper"] = "FAILED"
    for scraper in channels_config[channel.id]["scraper"]:
        try:
            scraper_module = importlib.import_module("epg.scraper" + "." + scraper)
            update = getattr(scraper_module, "update")
        except (ImportError, AttributeError) as exc:
            print(f"!!!Scraper '{scraper}' is not available: {exc}!!!")
            continue
        try:
            success = update(
                channel, channels_config[channel.id]["scraper"][scraper], date
            )
        except Exception as exc:
            print(f"!!!Scraper '{scraper}' crashed on {channel.id} {date}: {exc}!!!")
            continue
        if success:
            channel.metadata["last_scraper"] = scraper
            channel.metadata["last_update"] = datetime.now().astimezone()
            return True
    return False


def run_plugin(channel: Channel, dates: list[date], log: list[str]) -> None:
    """
    Post-process a channel with its configured plugin.

    Plugins run after all scraping for the channel is done, once per
    updated date, so they are decoupled from which scraper succeeded.

    Args:
        channel (Channel): The channel to post-process.
        dates (list[date]): The dates that were updated in this run.
        log (list[str]): Buffer that per-channel progress lines are appended to.
    """
    plugin_name = channel.metadata.get("plugin")
    if plugin_name is None or not dates:
        return
    try:
        plugin_module = importlib.import_module("epg.plugin" + "." + plugin_name)
        plugin_update = getattr(plugin_module, "update")
    except (ImportError, AttributeError) as exc:
        print(f"!!!Plugin '{plugin_name}' is not available: {exc}!!!")
        return
    for dt in dates:
        try:
            plugin_update(channel, dt)
        except Exception as exc:
            print(f"!!!Plugin '{plugin_name}' failed on {channel.id} {dt}: {exc}!!!")
    log.append(f"plugin {plugin_name} <- {', '.join(str(dt) for dt in dates)}")


def copy_channels(
    channels: list[Channel], new_channels: list[Channel]
) -> tuple[int, set]:
    """
    Copy channels from new_channels to channels.

    Args:
        channels (list[Channel]): The channels to copy to.
        new_channels (list[Channel]): The channels to copy from.

    Returns:
        tuple[int, set]: The number of reused channels and the dates of the programs.
    """
    num_reuse_channels = 0
    dates = set()
    new_channels_by_id = {new_channel.id: new_channel for new_channel in new_channels}
    today = datetime.now().date()
    for channel in channels:
        new_channel = new_channels_by_id.get(channel.id)
        if new_channel is None:
            continue
        recap_days = channel.metadata.get("recap") or 0
        preview_days = channel.metadata.get("preview") or 0
        min_date = today - timedelta(recap_days)
        max_date = today + timedelta(preview_days)
        # Keep the programs in recap/preview days
        for program in new_channel.programs:
            if min_date <= program.start_time.date() <= max_date:
                dates.add(program.start_time.date())
                channel.programs.append(program)
        num_reuse_channels += 1
        channel.programs = list(set(channel.programs))  # Remove duplicates
        if channel.programs != []:
            channel.metadata["last_update"] = new_channel.metadata["last_update"]
        else:
            channel.metadata["last_update"] = datetime(
                1970, 1, 1, 0, 0, 0, tzinfo=tz_shanghai
            )
    return (num_reuse_channels, dates)


def update_channel_full(channel: Channel, index: int | None = None) -> bool:
    """
    Fully update a channel according to its refresh policy, printing its
    progress as one atomic block so that concurrent updates do not
    interleave.

    Recap, today and preview are handled as one continuous date range
    [today - recap, today + preview]:
      - past dates are scraped only when they have no programs yet
        (fills any gap, not just days before the earliest known one)
      - today follows the refresh policy
      - future dates are re-scraped (sources change their upcoming
        schedules), except on repeat runs of an already-updated
        refresh:once channel, where only empty future dates are filled
    The configured plugin then post-processes every updated date.

    Args:
        channel (Channel): The channel to update.
        index (int, optional): Ordinal shown in the progress output.

    Returns:
        bool: True if the channel was refreshed.
    """
    refresh = channel.metadata.get("refresh", "once")
    today = datetime.now().date()
    recap = channel.metadata.get("recap") or 0
    preview = channel.metadata.get("preview") or 0
    dates_with_programs = {program.start_time.date() for program in channel.programs}
    today_done = (
        refresh == "once"
        and channel.metadata["last_update"].date() == today
        # Only trust today's last_update if today's programs actually
        # exist: a run whose "today" scrape failed (but whose recap
        # succeeded) still stamps last_update, and skipping here would
        # leave the channel empty for the whole day (issue #7).
        and today in dates_with_programs
    )
    if today_done:
        # An earlier run already updated this channel today. Do not
        # refresh anything that exists, but still fill future dates
        # that have no programs at all (e.g. their scrape failed).
        pending_dates = [
            today + timedelta(offset)
            for offset in range(1, preview + 1)
            if today + timedelta(offset) not in dates_with_programs
        ]
        if not pending_dates:
            return False
    else:
        pending_dates = [
            today + timedelta(offset)
            for offset in range(-recap, preview + 1)
            # past days are only filled in, never refreshed
            if offset >= 0 or today + timedelta(offset) not in dates_with_programs
        ]
    log: list[str] = []
    header = f"{index if index is not None else '-'} {channel.id} {channel.metadata['name']}"
    log.append(f"{header} last update: {channel.metadata['last_update']}")
    updated_dates: list[date] = []
    recap_parts: list[str] = []
    preview_parts: list[str] = []
    for pointer_date in pending_dates:
        if not channel.update(pointer_date):
            if pointer_date == today:
                log.append(
                    f"{refresh} <- now {datetime.now().astimezone().isoformat()} FAILED"
                )
            continue
        updated_dates.append(pointer_date)
        part = f"{pointer_date} {channel.metadata['last_scraper']}"
        if pointer_date < today:
            recap_parts.append(part)
        elif pointer_date == today:
            log.append(
                f"{refresh} <- now {datetime.now().astimezone().isoformat()} "
                f"{channel.metadata['last_scraper']}"
            )
        else:
            preview_parts.append(part)
    if recap_parts:
        log.append(
            f"recap <- {', '.join(recap_parts)} total: {len(recap_parts)}"
        )
    if preview_parts:
        log.append(
            f"preview <- {', '.join(preview_parts)} total: {len(preview_parts)}"
        )
    run_plugin(channel, updated_dates, log)
    print("\n".join(log), flush=True)
    return True
