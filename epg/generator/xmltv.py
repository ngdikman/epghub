# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd

import re

from lxml import etree
from epg.model import Channel
from datetime import datetime

# XML 1.0 forbids most control characters; scraped descriptions
# occasionally contain them (e.g. \x0b) and would abort the whole
# write, so strip everything but tab/newline/carriage return.
_XML_ILLEGAL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]")


def _sanitize(text: str) -> str:
    if not text:
        return text
    return _XML_ILLEGAL_CHARS.sub("", text)


def write(filepath: str, channels: list[Channel], info: str = "") -> bool:
    root = etree.Element("tv")
    tree = etree.ElementTree(root)
    tree.docinfo.system_url = "xmltv.dtd"
    root.set("generator-info-name", info)
    last_update_time_list = []
    for channel in channels:
        # Optional per-channel language stamped as the xmltv 'lang'
        # attribute (two-letter code, e.g. 'zh' or 'en').
        xml_lang = channel.metadata.get("xml_lang")
        last_update_time_list.append(channel.metadata["last_update"])
        channel_element = etree.SubElement(root, "channel")
        channel_element.set("id", channel.id)
        for name in channel.metadata["name"]:
            display_name = etree.SubElement(channel_element, "display-name")
            display_name.text = _sanitize(name)
            if xml_lang:
                display_name.set("lang", xml_lang)
    last_update_time = max(last_update_time_list)
    root.set(
        "date",
        datetime(
            last_update_time.year,
            last_update_time.month,
            last_update_time.day,
            tzinfo=last_update_time.tzinfo,
        ).strftime("%Y%m%d%H%M%S %z"),
    )
    for channel in channels:
        xml_lang = channel.metadata.get("xml_lang")
        channel.programs.sort(key=lambda x: x.start_time)
        for program in channel.programs:
            program_element = etree.SubElement(root, "programme")
            program_element.set(
                "start", program.start_time.astimezone().strftime("%Y%m%d%H%M%S %z")
            )  # astimezone() is necessary
            program_element.set(
                "stop", program.end_time.astimezone().strftime("%Y%m%d%H%M%S %z")
            )  # astimezone() is necessary
            program_element.set("channel", channel.id)
            title = etree.SubElement(program_element, "title")
            title.text = _sanitize(program.title)
            if xml_lang:
                title.set("lang", xml_lang)
            if program.sub_title != "":
                sub_title = etree.SubElement(program_element, "sub-title")
                sub_title.text = _sanitize(program.sub_title)
                if xml_lang:
                    sub_title.set("lang", xml_lang)
            if program.desc != "":
                desc = etree.SubElement(program_element, "desc")
                desc.text = _sanitize(program.desc)
                if xml_lang:
                    desc.set("lang", xml_lang)
    tree.write(filepath, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return True
