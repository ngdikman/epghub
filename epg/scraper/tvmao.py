from datetime import date, datetime, time, timedelta
from epg.model import Channel, Program
from . import get_session, tz_shanghai


# Credits to https://github.com/supzhang/epg/blob/master/crawl/spiders/tvmao.py
def update(
    channel: Channel, scraper_id: str | None = None, dt: date | None = None
) -> bool:
    """
    Update channel with new data for the given date.

    Args:
        channel (Channel): The channel to update.
        scraper_id (str): The scraper id.
        dt (date): The date to update.

    Returns:
        bool: True if success, False if not.
    """
    if dt is None:
        dt = datetime.today().date()
    if scraper_id is None:
        return False
    now_date = datetime.now().date()
    request_date = dt
    delta = request_date - now_date
    now_weekday = now_date.weekday()
    need_weekday = now_weekday + delta.days + 1
    if delta.days < 0:
        if abs(delta.days) > now_weekday:
            return False
    if delta.days > 0:
        if delta.days > 6 - now_weekday:
            return False
    id_split = scraper_id.split("-")
    if len(id_split) == 2:
        id = id_split[1]
    elif len(id_split) == 3:
        id = "-".join(id_split[1:3])
    else:
        id = scraper_id
    url = f"https://lighttv.tvmao.com/qa/qachannelschedule?epgCode={id}&op=getProgramByChnid&epgName=&isNew=on&day={need_weekday}"
    try:
        res = get_session().get(url, timeout=5)
    except Exception:
        return False
    if res.status_code != 200:
        return False
    try:
        programs_data = res.json()[2]["pro"]
    except Exception:
        return False
    if len(programs_data) == 0:
        return False
    # Purge channel programs on this date only after data is confirmed,
    # so an empty response does not wipe previously stored programs.
    channel.flush(dt)
    temp_program = None
    for program in programs_data:
        title = program["name"]
        try:
            start_of_program = datetime.strptime(program["time"], "%H:%M").time()
        except ValueError:
            continue
        # tvmao times are Beijing time: attach the timezone directly
        # instead of converting from the (arbitrary) local timezone.
        starttime = datetime.combine(dt, start_of_program, tzinfo=tz_shanghai)
        if temp_program is not None:
            temp_program.end_time = starttime
            channel.programs.append(temp_program)
        temp_program = Program(title, starttime, None, channel.id + "@tvmao.com")
    if temp_program is None:
        return False
    temp_program.end_time = datetime.combine(
        dt + timedelta(days=1), time(0, 0), tzinfo=tz_shanghai
    )
    channel.programs.append(temp_program)
    return True
