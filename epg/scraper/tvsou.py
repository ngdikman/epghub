from epg.model import Channel, Program
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from . import get_session, tz_shanghai

baseurl = "https://www.tvsou.com/epg/"


def grab_programs(channel_id: str, need_weekday: int) -> tuple | bool:
    """
    Grab programs from tvsou.com.
    Return: (content, date) in tuple
    Args:
        channel_id (str): The channel id.
        need_weekday (int): The weekday to grab.
    """
    channel_baseurl = baseurl + channel_id + "/"  # get channel_id
    try:
        res = get_session().get(channel_baseurl + "w" + str(need_weekday), timeout=5)
    except Exception:
        return False
    if res.status_code != 200:
        return False
    soup = BeautifulSoup(res.text, "html.parser")
    try:
        content = soup.find("div", class_="layui-tab-item layui-show").find_all("td")
        date_str = soup.find("a", class_="week_active").find("i").text
        date = (
            datetime.strptime(date_str, "%m月%d日")
            .date()
            .replace(year=datetime.now().year)
        )
    except (AttributeError, ValueError):
        return False
    return (content, date)


def parse_programs(content: tuple) -> list:
    """
    Parse web page to find out program list.
    Return: (title, start time, end time) in list
    Args:
        content (tuple): The content of the web page. (content, date)
    """
    date = content[1]
    programs: list = list()
    title = None
    start = None
    for line in content[0]:
        if line.text:
            try:
                # Times on the page are Beijing time; parse the wall time
                # and attach the timezone without converting.
                start_time = datetime.strptime(line.text, "%H:%M").time()
                start = datetime(
                    year=date.year,
                    month=date.month,
                    day=date.day,
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0,
                    microsecond=0,
                    tzinfo=tz_shanghai,
                )
            except ValueError:
                title = str(line.text).replace("::", ":")
        if title and start:
            programme = dict()
            programme["start"] = start
            programme["title"] = title
            # programme['desc'] = ''
            programs.append(programme)
            title = None
            start = None
    return programs


def update(
    channel: Channel, scraper_id: str | None = None, dt: date | None = None
):
    """
    Update channel with new data for the given date.
    Return: True if success, False if not.
    Args:
        channel (Channel): The channel to update.
        scraper_id (str): The scraper id.
        dt (date): The date to update.
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
    bs_programs = grab_programs(scraper_id, need_weekday)
    if not bs_programs:
        return False
    else:
        programs = parse_programs(bs_programs)
        if len(programs) == 0:
            return False
        # Purge channel programs on this date only after data is confirmed,
        # so an empty response does not wipe previously stored programs.
        channel.flush(dt)
        temp_program = None
        for program in programs:
            title = program["title"]
            starttime = program["start"]
            if temp_program != None:
                temp_program.end_time = starttime
                channel.programs.append(temp_program)
            temp_program = Program(title, starttime, None, channel.id + "@tvsou.com")
        temp_program.end_time = temp_program.start_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        channel.programs.append(temp_program)
        return True
