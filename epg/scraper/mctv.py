from epg.model import Channel, Program
from datetime import datetime, date, timezone, timedelta
from . import get_session, tz_shanghai


def update(
    channel: Channel, scraper_id: str | None = None, dt: date | None = None
) -> bool:
    if dt is None:
        dt = datetime.today().date()
    if scraper_id is None:
        return False

    channel_num = int(scraper_id)
    date_from = f"{dt.strftime('%Y-%m-%d')} 00:00:00"
    date_to = f"{(dt + timedelta(days=1)).strftime('%Y-%m-%d')} 04:00:00"

    url = "https://app.ksmctv.com/ApiWebService/rest/query"
    payload = {
        "header": {"encrypt": False},
        "request": {
            "data": {
                "APP": "MCTVWEB",
                "Device": "MCTV001",
                "Channel": channel_num,
                "CategoryCode": "",
                "DateFrom": date_from,
                "DateTo": date_to,
                "Lang": "TC",
            },
            "resource_id": "/mctvweb/get_epg_list",
        },
    }

    try:
        res = get_session().post(url, json=payload, timeout=10)
    except Exception:
        return False

    if res.status_code != 200:
        return False

    try:
        data = res.json()
        if data.get("request_status") != "no_error":
            return False
        programs_data = data["result"]["List"]
    except Exception:
        return False

    if len(programs_data) == 0:
        return False

    channel.flush(dt)

    for program in programs_data:
        title = program["ProgramName"]
        sub_title = program.get("EpisodeName", "")
        desc = program.get("EpisodeSynopsis", "")
        start_time = datetime.strptime(
            program["StartDate"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=tz_shanghai)
        end_time = datetime.strptime(
            program["EndDate"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=tz_shanghai)
        channel.programs.append(
            Program(
                title,
                start_time,
                end_time,
                channel.id + "@mctv.com",
                desc=desc,
                sub_title=sub_title,
            )
        )

    channel.metadata.update({"last_update": datetime.now(timezone.utc).astimezone()})
    return True