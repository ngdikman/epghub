# Original: https://github.com/iptv-org/epg/blob/master/sites/nowplayer.now.com/nowplayer.now.com.config.js
# Channels: https://nowplayer.now.com/channels
# NowTV (nowplayer.now.com, 香港 Now 宽频电视)

import datetime

from epg.model import Channel, Program
from . import get_session, tz_hong_kong

API_ENDPOINT = "https://nowplayer.now.com/tvguide"
# The API only serves a rolling window starting today (day=1).
MAX_DAYS = 7


def fetch_items(site_id: str, day: int, lang: str) -> list:
    response = get_session().get(
        f"{API_ENDPOINT}/epglist",
        params={"channelIdList[]": site_id, "day": str(day)},
        cookies={"LANG": lang},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    # One list of programs per requested channel id.
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return []
    return data[0]


def get_channels(lang: str = "zh") -> list[dict]:
    response = get_session().get(
        f"{API_ENDPOINT}/channellist",
        cookies={"LANG": lang},
        timeout=10,
    )
    response.raise_for_status()
    return [
        {"site_id": str(item["channelNo"]), "name": item["name"], "lang": lang}
        for item in response.json()
    ]


def update(
    channel: Channel,
    scraper_id: str | None = None,
    dt: datetime.date | None = None,
) -> bool:
    if dt is None:
        dt = datetime.datetime.today().date()
    day = (dt - datetime.datetime.now(tz_hong_kong).date()).days + 1
    if not 1 <= day <= MAX_DAYS:
        return False
    channel_id = channel.id if scraper_id is None else scraper_id
    lang = channel.metadata.get("lang", "zh")

    try:
        items = fetch_items(channel_id, day, lang)
    except Exception:
        return False
    programs = []
    for item in items:
        try:
            start = datetime.datetime.fromtimestamp(
                int(item["start"]) / 1000, tz=tz_hong_kong
            )
            end = datetime.datetime.fromtimestamp(
                int(item["end"]) / 1000, tz=tz_hong_kong
            )
            title = item["name"]
        except (KeyError, TypeError, ValueError):
            continue
        if start.date() != dt:
            continue
        # The epglist API only carries name/start/end, no synopsis.
        programs.append(Program(title, start, end, channel_id + "@nowtv"))
    if not programs:
        return False
    # Purge channel programs on this date only after a successful fetch,
    # so a failed request does not wipe previously stored data.
    channel.flush(dt)
    channel.programs.extend(programs)
    channel.metadata.update({"last_update": datetime.datetime.now().astimezone()})
    return True
