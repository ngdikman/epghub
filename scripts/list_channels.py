"""
List the channels available from a scraper's data source.

Usage:
    python scripts/list_channels.py mytvsuper [--lang tc|en] [--save]
    python scripts/list_channels.py nowtv [--lang zh|en] [--save]
    python scripts/list_channels.py cztv [--range 1-120] [--save]
    python scripts/list_channels.py discoverychannel_tw [--range 1-10]

--save writes the result to reference/<scraper>.json in the same format
as reference/cntv.json; scripts/generate_channel_docs.py then picks the
file up automatically and adds a table to docs/channels.md.

cctv and tvmao already have curated lists in /reference. tvsou cannot be
enumerated (its channel ids are opaque hashes) -- see docs/channels.md.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def parse_range(text: str) -> tuple[int, int]:
    start, _, end = text.partition("-")
    return int(start), int(end or start)


def list_mytvsuper(args) -> list[dict]:
    from epg.scraper.mytvsuper import get_channels

    channels = get_channels(args.lang)
    return [
        {"ename": str(c["site_id"]), "chname": c["name"], "type": "香港 TVB"}
        for c in channels
    ]


def list_nowtv(args) -> list[dict]:
    from epg.scraper.nowtv import get_channels

    lang = "zh" if args.lang in ("zh", "tc") else "en"
    channels = get_channels(lang)
    return [
        {"ename": str(c["site_id"]), "chname": c["name"], "type": "香港 NowTV"}
        for c in channels
    ]


def list_cztv(args) -> list[dict]:
    from epg.scraper import get_session

    start, end = parse_range(args.range or "1-120")
    date_str = datetime.now().strftime("%Y%m%d")
    found = []
    for station_id in range(start, end + 1):
        url = f"https://p.cztv.com/api/paas/program/{station_id}/{date_str}"
        try:
            data = get_session().get(url, timeout=5).json()
            station = data["content"]["list"][0]
            found.append(
                {
                    "ename": str(station["station_id"]),
                    "chname": station["station_name"],
                    "type": "浙江广电",
                }
            )
            print(f"  found {station['station_id']}: {station['station_name']}")
        except Exception:
            pass
        time.sleep(0.2)  # be polite to the API
    return found


def list_discoverychannel_tw(args) -> list[dict]:
    from epg.scraper import get_session
    from epg.scraper.discoverychannel_tw import API_ENDPOINT

    start, end = parse_range(args.range or "1-10")
    date_str = datetime.now().strftime("%Y-%m-%d")
    found = []
    for channel_id in range(start, end + 1):
        try:
            res = get_session().post(
                API_ENDPOINT,
                data={"date": date_str, "channel": str(channel_id)},
                timeout=5,
            )
            programs = res.json()
        except Exception:
            programs = []
        if programs:
            # The schedule API does not expose the channel name, only
            # which ids respond; check the site to see which is which.
            found.append(
                {
                    "ename": str(channel_id),
                    "chname": f"频道 {channel_id}（{len(programs)} 个节目，名称见官网）",
                    "type": "台湾探索",
                }
            )
            print(f"  found channel id {channel_id}: {len(programs)} programs")
        time.sleep(0.2)
    return found


SOURCES = {
    "mytvsuper": list_mytvsuper,
    "nowtv": list_nowtv,
    "cztv": list_cztv,
    "discoverychannel_tw": list_discoverychannel_tw,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scraper", choices=sorted(SOURCES))
    parser.add_argument("--lang", default="tc", choices=("tc", "zh", "en"))
    parser.add_argument("--range", help="id range to probe, e.g. 1-120")
    parser.add_argument(
        "--save",
        action="store_true",
        help="write result to reference/<scraper>.json",
    )
    args = parser.parse_args()
    print(f"querying {args.scraper}...")
    channels = SOURCES[args.scraper](args)
    if not channels:
        print("no channels found (network problem or empty source)")
        sys.exit(1)
    print(f"\n{len(channels)} channels:")
    for channel in channels:
        print(f"  {channel['ename']} | {channel['chname']}")
    if args.save:
        path = os.path.join(ROOT, "reference", f"{args.scraper}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(channels, f, ensure_ascii=False, indent=4)
        print(f"\nsaved to {path}")
        print("run 'python scripts/generate_channel_docs.py' to refresh the docs")


if __name__ == "__main__":
    main()
