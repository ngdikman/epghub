# Astro Go (astro.com.my, 马来西亚 Astro 卫星电视)
# API: https://sg-sg-sg.astro.com.my:9443/ctap/r1.6.0/shared/grid

import datetime
import math
from urllib.parse import urlparse

from epg.model import Channel, Program
from . import get_session, tz_shanghai

BASE_URL = "https://sg-sg-sg.astro.com.my:9443"
OAUTH_URL = f"{BASE_URL}/oauth2/authorize"
GRID_URL = f"{BASE_URL}/ctap/r1.6.0/shared/grid"
REFERER = "https://astrogo.astro.com.my/"
CLIENT_TOKEN = (
    "v:1!r:80800!ur:GUEST_REGION!community:Malaysia%20Live!"
    "t:k!dt:PC!f:Astro_unmanaged!pd:CHROME-FF!pt:Adults"
)

# 模块级缓存，避免同一轮更新中重复请求
_access_token = None
_epg_cache: dict[str, dict] = {}  # key: date_str -> raw API response


def _get_access_token() -> str | None:
    global _access_token
    if _access_token:
        return _access_token

    try:
        resp = get_session().get(
            OAUTH_URL,
            params={
                "client_id": "browser",
                "state": "guestUserLogin",
                "response_type": "token",
                "redirect_uri": "https://astrogo.astro.com.my",
                "scope": "urn:synamedia:vcs:ovp:guest-user",
                "prompt": "none",
            },
            headers={"Referer": REFERER},
            allow_redirects=False,
            timeout=15,
        )

        location = resp.headers.get("Location")
        if not location:
            return None

        parsed = urlparse(location)
        fragment = parsed.fragment
        params = {}
        for item in fragment.split("&"):
            if "=" in item:
                key, value = item.split("=", 1)
                params[key] = value

        _access_token = params.get("access_token")
        return _access_token

    except Exception:
        return None


def _fetch_epg(date_str: str) -> dict:
    """获取指定日期的 EPG 数据，结果缓存到模块级"""
    if date_str in _epg_cache:
        return _epg_cache[date_str]

    token = _get_access_token()
    if not token:
        return {}

    headers = {
        "Referer": REFERER,
        "Authorization": f"Bearer {token}",
        "Accept-Language": "zh",
    }

    params = {
        "startDateTime": date_str,
        "channelId": "711",  # 任意频道 ID，API 会返回全部
        "limit": 200,
        "genreId": "",
        "isPlayable": "true",
        "duration": 24,
        "clientToken": CLIENT_TOKEN,
    }

    try:
        resp = get_session().get(GRID_URL, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        _epg_cache[date_str] = data
        return data
    except Exception:
        return {}


def _get_utc_date_str(dt: datetime.date) -> str:
    """将日期转为 UTC 零点 ISO 字符串"""
    target = datetime.datetime.combine(
        dt, datetime.time(0, 0), tzinfo=tz_shanghai
    )
    return target.astimezone(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )


def update(
    channel: Channel,
    scraper_id: str | None = None,
    dt: datetime.date | None = None,
) -> bool:
    if dt is None:
        dt = datetime.datetime.today().date()

    channel_id = str(channel.id if scraper_id is None else scraper_id)
    date_str = _get_utc_date_str(dt)

    try:
        epg_data = _fetch_epg(date_str)
    except Exception:
        return False

    if not epg_data:
        return False

    # 在返回的频道中查找匹配的 channel_id
    epg_channels = epg_data.get("channels", [])
    matched_schedule = None
    for ch in epg_channels:
        if str(ch.get("id", "")) == channel_id:
            matched_schedule = ch.get("schedule", [])
            break

    if matched_schedule is None:
        return False

    programs = []
    for prog in matched_schedule:
        start_str = prog.get("startDateTime")
        duration = prog.get("duration")

        if not start_str or not duration:
            continue

        try:
            start_utc = datetime.datetime.strptime(
                start_str, "%Y-%m-%dT%H:%M:%S.000Z"
            ).replace(tzinfo=datetime.timezone.utc)
            end_utc = start_utc + datetime.timedelta(seconds=duration)
            start_local = start_utc.astimezone(tz_shanghai)
            end_local = end_utc.astimezone(tz_shanghai)
        except (ValueError, OverflowError):
            continue

        # 只保留目标日期的节目
        if start_local.date() != dt:
            continue

        title = prog.get("title", "")
        desc = prog.get("synopsis", "")
        episode = prog.get("episodeNumber")

        # 集数处理
        if episode:
            if _has_chinese(title) or _has_chinese(desc):
                title += f" 第{episode}集"
            else:
                title += f" Ep{episode}"

        programs.append(
            Program(
                title,
                start_local,
                end_local,
                channel_id + "@astro.com.my",
                desc,
                str(episode) if episode else "",
            )
        )

    if not programs:
        return False

    channel.flush(dt)
    channel.programs.extend(programs)
    channel.metadata.update({"last_update": datetime.datetime.now().astimezone()})
    return True


def _has_chinese(text: str) -> bool:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False