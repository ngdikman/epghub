# Original: https://github.com/iptv-org/epg/blob/master/sites/mytvsuper.com/mytvsuper.com.config.js
# Channels: https://github.com/iptv-org/epg/blob/master/sites/mytvsuper.com/mytvsuper.com.channels.xml
# Translated by: https://chat.openai.com/share/e1a723db-d273-4241-97b9-cf8497b5c746

import datetime
import json
from epg.model import Channel, Program
from . import get_session, tz_hong_kong

API_ENDPOINT = "https://content-api.mytvsuper.com/v1"


def parse_title(item, site_channel):
    return (
        item["programme_title_en"]
        if site_channel["lang"] == "en"
        else item["programme_title_tc"]
    )


def parse_description(item, site_channel):
    return (
        item["episode_synopsis_en"]
        if site_channel["lang"] == "en"
        else item["episode_synopsis_tc"]
    )


def parse_start(item):
    # API times are Hong Kong wall time: attach the timezone directly
    # instead of converting from the (arbitrary) local timezone.
    start_datetime = datetime.datetime.strptime(
        item["start_datetime"], "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=tz_hong_kong)
    return start_datetime


def parse_items(content, date):
    data = json.loads(content)
    if (
        not isinstance(data, list)
        or not data
        or not isinstance(data[0].get("item"), list)
    ):
        return []

    day_data = next(
        (i for i in data[0]["item"] if i["date"] == date.strftime("%Y-%m-%d")), None
    )
    if not day_data or not isinstance(day_data.get("epg"), list):
        return []

    return day_data["epg"]


def fetch_data(site_channel, date):
    url = f"{API_ENDPOINT}/epg?network_code={site_channel['site_id']}&from={date.strftime('%Y%m%d')}&to={date.strftime('%Y%m%d')}&platform=web"
    response = get_session().get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_programs(content, site_channel, date):
    programs = []
    items = parse_items(content, date)
    prev = None

    for item in items:
        start = parse_start(item)
        stop = start + datetime.timedelta(minutes=30)

        if prev:
            prev["stop"] = start

        episode = int(item["episode_no"]) if item["episode_no"] else 0

        programs.append(
            {
                "title": parse_title(item, site_channel),
                "description": parse_description(item, site_channel),
                "episode": episode,
                "start": start,
                "stop": stop,
            }
        )

        prev = programs[-1]

    return programs


def get_channels(lang):
    response = get_session().get(f"{API_ENDPOINT}/channel/list?platform=web", timeout=10)
    response.raise_for_status()
    data = response.json()

    channels = []

    for channel in data["channels"]:
        name = channel["name_en"] if lang == "en" else channel["name_tc"]
        channels.append(
            {"site_id": channel["network_code"], "name": name, "lang": lang}
        )

    return channels


def update(
    channel: Channel,
    scraper_id: str | None = None,
    dt: datetime.date | None = None,
) -> bool:
    if dt is None:
        dt = datetime.datetime.today().date()
    channel_id = channel.id if scraper_id is None else scraper_id
    lang = channel.metadata.get("lang", "tc")
    site_channel = {
        "site_id": channel_id,
        "lang": lang,
    }  # Replace with your channel data

    try:
        data = fetch_data(site_channel, dt)
    except Exception:
        return False
    programs = parse_programs(data, site_channel, dt)
    if not programs:
        return False
    # Purge channel programs on this date only after a successful fetch,
    # so a failed request does not wipe previously stored data.
    channel.flush(dt)
    # Update channel programs on this date
    for program in programs:
        channel.programs.append(
            Program(
                program["title"],
                program["start"],
                program["stop"],
                channel_id + "@mytvsuper.com",
                program["description"],
                program["episode"],
            )
        )
    channel.metadata.update({"last_update": datetime.datetime.now().astimezone()})
    return True
