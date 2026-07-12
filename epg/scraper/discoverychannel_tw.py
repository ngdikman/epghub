from epg.model import Channel, Program
from datetime import datetime, date, time, timedelta
from . import get_session, tz_shanghai

API_ENDPOINT = "https://www.discoverychannel.com.tw/ajax/getschedule.php"


def update(
    channel: Channel, scraper_id: str | None = None, dt: date | None = None
) -> bool:
    if dt is None:
        dt = datetime.today().date()
    channel_id = channel.id if scraper_id is None else scraper_id
    date_str = dt.strftime("%Y-%m-%d")
    r_data = {"date": date_str, "channel": channel_id}
    try:
        res = get_session().post(API_ENDPOINT, data=r_data, timeout=5)
    except Exception:
        print("Fail:", API_ENDPOINT)
        return False
    # handle error
    if res.status_code != 200:
        return False
    try:
        programs_data = res.json()
    except ValueError:
        return False
    if len(programs_data) == 0:
        return False
    # Purge channel programs on this date only after data is confirmed,
    # so an empty response does not wipe previously stored programs.
    channel.flush(dt)
    temp_program = None
    for program in programs_data:
        title = program["title"]
        try:
            # Schedule times are UTC+8 wall time: attach the timezone
            # directly instead of converting from the local timezone.
            starttime = datetime.strptime(
                program["publictime"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=tz_shanghai)
        except ValueError:
            continue
        if temp_program is not None:
            temp_program.end_time = starttime
            channel.programs.append(temp_program)
        temp_program = Program(
            title, starttime, None, channel.id + "@discoverychannel.com.tw"
        )
    if temp_program is None:
        return False
    temp_program.end_time = datetime.combine(
        dt + timedelta(days=1), time(0, 0), tzinfo=tz_shanghai
    )
    channel.programs.append(temp_program)
    return True
