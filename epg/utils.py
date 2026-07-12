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
            if channel.metadata.get("plugin") is not None:
                try:
                    plugin_module = importlib.import_module(
                        "epg.plugin" + "." + channel.metadata["plugin"]
                    )
                    plugin_update = getattr(plugin_module, "update")
                    plugin_update(channel, date)
                except Exception as exc:
                    print(
                        f"!!!Plugin '{channel.metadata['plugin']}' failed on {channel.id}: {exc}!!!"
                    )
            return True
    return False


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


def update_preview(channel: Channel, log: list[str]) -> int:
    """
    Update channel preview.

    Args:
        channel (Channel): The channel to update.
        log (list[str]): Buffer that per-channel progress lines are appended to.

    Returns:
        int: The number of days previewed."""
    previewed_days = 0
    preview = channel.metadata.get("preview") or 0
    if preview <= 0:
        return previewed_days
    max_date = datetime.now().date() + timedelta(preview)
    pointer_date = datetime.now().date()
    parts = []
    while pointer_date < max_date:
        pointer_date += timedelta(1)
        if channel.update(pointer_date):
            previewed_days += 1
            parts.append(f"{pointer_date} {channel.metadata['last_scraper']}")
    if parts:
        log.append(f"preview <- {', '.join(parts)} total: {previewed_days}")
    return previewed_days


def update_recap(channel: Channel, log: list[str]) -> int:
    """
    Update channel recap.

    Args:
        channel (Channel): The channel to update.
        log (list[str]): Buffer that per-channel progress lines are appended to.

    Returns:
        int: The number of days recaped."""
    recaped_days = 0
    recap = channel.metadata.get("recap") or 0
    if recap <= 0:
        return recaped_days
    min_date = datetime.now().date() - timedelta(recap)
    pointer_date = min_date
    max_date = datetime.now().date()
    for program in channel.programs:
        if program.start_time.date() < max_date:
            max_date = program.start_time.date()
    parts = []
    while pointer_date < max_date:
        if channel.update(pointer_date):
            recaped_days += 1
            parts.append(f"{pointer_date} {channel.metadata['last_scraper']}")
        pointer_date += timedelta(1)
    if parts:
        log.append(
            f"recap {min_date} -> {max_date - timedelta(1)}: "
            f"{', '.join(parts)} total: {recaped_days}"
        )
    return recaped_days


def update_channel_full(channel: Channel, index: int | None = None) -> bool:
    """
    Fully update a channel (recap + today + preview) according to its
    refresh policy, printing its progress as one atomic block so that
    concurrent updates do not interleave.

    Args:
        channel (Channel): The channel to update.
        index (int, optional): Ordinal shown in the progress output.

    Returns:
        bool: True if the channel was refreshed.
    """
    refresh = channel.metadata.get("refresh", "once")
    today = datetime.now().date()
    if (
        refresh == "once"
        and channel.metadata["last_update"].date() == today
        # Only trust today's last_update if today's programs actually
        # exist: a run whose "today" scrape failed (but whose recap
        # succeeded) still stamps last_update, and skipping here would
        # leave the channel empty for the whole day (issue #7).
        and any(program.start_time.date() == today for program in channel.programs)
    ):
        return False
    log: list[str] = []
    header = f"{index if index is not None else '-'} {channel.id} {channel.metadata['name']}"
    log.append(f"{header} last update: {channel.metadata['last_update']}")
    update_recap(channel, log)
    if channel.update():
        log.append(
            f"{refresh} <- now {datetime.now().astimezone().isoformat()} "
            f"{channel.metadata['last_scraper']}"
        )
    else:
        log.append(f"{refresh} <- now {datetime.now().astimezone().isoformat()} FAILED")
    update_preview(channel, log)
    print("\n".join(log), flush=True)
    return True
