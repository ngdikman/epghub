import threading

from lxml import etree
from epg.model import Channel, Program
from datetime import datetime
from . import get_session
from epg.scraper import tz_shanghai

# Remote XMLTV files are untrusted input: refuse entity expansion, DTD
# fetching and oversized trees so a hostile source cannot XXE or OOM us.
_parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    huge_tree=False,
)

# One XMLTV source is often shared by many channels/dates in a single run;
# cache the parsed result per URL so it is fetched only once per process.
# A per-URL lock serializes concurrent cache misses so only one thread
# fetches a given source while the others wait for its result.
_cache: dict[str, list[Channel]] = {}
_cache_lock = threading.Lock()
_url_locks: dict[str, threading.Lock] = {}


def _find_text(element: etree._Element, tag: str) -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text


def get_channels(xmltv_url: str, dtd: etree.DTD | None = None) -> list[Channel]:
    with _cache_lock:
        if xmltv_url in _cache:
            return _cache[xmltv_url]
        url_lock = _url_locks.setdefault(xmltv_url, threading.Lock())
    with url_lock:
        # Another thread may have fetched this URL while we waited.
        with _cache_lock:
            if xmltv_url in _cache:
                return _cache[xmltv_url]
        channels = _fetch_channels(xmltv_url, dtd)
        # Do not cache a failed/empty fetch: a transient error must not
        # poison the source for every remaining channel in the run.
        if channels:
            with _cache_lock:
                _cache[xmltv_url] = channels
        return channels


def _fetch_channels(xmltv_url: str, dtd: etree.DTD | None = None) -> list[Channel]:
    try:
        xml = get_session().get(xmltv_url, timeout=10).content
    except Exception:
        print("Failed to get XMLTV:", xmltv_url)
        return []
    try:
        root = etree.XML(xml, _parser)
    except etree.XMLSyntaxError as e:
        print("XML is not valid:", e)
        return []
    if dtd is not None:
        if not dtd.validate(root):
            print(dtd.error_log.filter_from_errors()[0])
            return []
    try:
        last_update = datetime.strptime(root.get("date"), "%Y%m%d%H%M%S %z")
    except (TypeError, ValueError):
        last_update = datetime(1970, 1, 1, 0, 0, 0, tzinfo=tz_shanghai)
    channels = []
    channels_by_id: dict[str, Channel] = {}
    for xml_channel in root.iter("channel"):
        channel_id = xml_channel.get("id")
        if channel_id is None or channel_id in channels_by_id:
            continue
        channel_names = [
            x.text for x in xml_channel.iter("display-name") if x.text is not None
        ]
        metadata = {"name": channel_names, "last_update": last_update}
        channel = Channel(channel_id, metadata)
        channels.append(channel)
        channels_by_id[channel_id] = channel
    # Single pass over all programmes instead of one XPath query per channel.
    for xml_programme in root.iter("programme"):
        channel = channels_by_id.get(xml_programme.get("channel"))
        if channel is None:
            continue
        try:
            start_time = datetime.strptime(
                xml_programme.get("start"), "%Y%m%d%H%M%S %z"
            )
            end_time = datetime.strptime(xml_programme.get("stop"), "%Y%m%d%H%M%S %z")
        except (TypeError, ValueError):
            continue
        title = _find_text(xml_programme, "title")
        sub_title = _find_text(xml_programme, "sub-title")
        desc = _find_text(xml_programme, "desc")
        channel.programs.append(
            Program(
                title,
                start_time,
                end_time,
                channel.id + "@xmltv",
                desc,
                sub_title=sub_title,
            )
        )
    for channel in channels:
        channel.programs.sort(key=lambda x: x.start_time)
    return channels
