# Example:
# {
#     "channel_name": "CCTV1",
#     "date": "2023-10-10",
#     "epg_data": [
#         {
#             "start": "00:00",
#             "end": "00:59",
#             "title": "精彩节目-暂未提供节目预告信息",
#             "desc": ""
#         },
#         {
#             "start": "01:00",
#             "end": "01:59",
#             "title": "精彩节目-暂未提供节目预告信息",
#             "desc": ""
#         }
#     ]
# }

from epg.model import Channel
import json
import os
import shutil


def _safe_segment(name: str) -> str:
    # Channel display names become directory names; keep them to a single
    # path segment so a misconfigured name cannot write outside the dir.
    return name.replace("/", "_").replace("\\", "_").replace("..", "_")


def write(dir: str, channels: list[Channel]) -> bool:
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)
    for channel in channels:
        channel_name = channel.metadata["name"][0]
        days: dict[str, list] = {}
        for program in sorted(channel.programs, key=lambda x: x.start_time):
            date_str = program.start_time.strftime("%Y-%m-%d")
            days.setdefault(date_str, []).append(
                {
                    "start": program.start_time.astimezone().strftime(
                        "%H:%M"
                    ),  # astimezone() is necessary
                    "end": program.end_time.astimezone().strftime(
                        "%H:%M"
                    ),  # astimezone() is necessary
                    "title": program.title,
                    "desc": program.desc,
                }
            )
        json_dir = os.path.join(dir, _safe_segment(channel_name))
        os.makedirs(json_dir, exist_ok=True)
        for date_str, epg_data in days.items():
            json_path = os.path.join(json_dir, date_str + ".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "channel_name": channel_name,
                        "date": date_str,
                        "epg_data": epg_data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=4,
                )
    return True
