from . import __xmltv
from epg.model import Channel, Program
from datetime import datetime, date, timezone


def update(
    channel: Channel, scraper_params: str, dt: date | None = None
) -> bool:
    """
    Import programs from a remote XMLTV file.

    scraper_params is either a plain URL (the channel id in the remote
    file must match this channel's id) or "<remote_id>@<url>" to map a
    different remote channel id onto this channel.
    """
    if dt is None:
        dt = datetime.today().date()
    if "@http" not in scraper_params:
        scraper_id = None
        scraper_url = scraper_params
    else:
        scraper_id, url_part = scraper_params.split("@http", 1)
        scraper_url = "http" + url_part
    channel_id = channel.id if not scraper_id else scraper_id
    for scraper_channel in __xmltv.get_channels(scraper_url):
        if scraper_channel.id != channel_id:
            continue
        programs = [
            program
            for program in scraper_channel.programs
            if program.start_time.date() == dt
        ]
        if not programs:
            return False
        # Purge channel programs on this date
        channel.flush(dt)
        # Update channel programs on this date
        for program in programs:
            channel.programs.append(
                Program(
                    program.title,
                    program.start_time,
                    program.end_time,
                    channel.id + "@xmltv",
                    program.desc,
                    sub_title=program.sub_title,
                )
            )
        channel.metadata.update(
            {"last_update": datetime.now(timezone.utc).astimezone()}
        )
        return True
    return False
