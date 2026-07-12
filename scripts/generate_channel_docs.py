"""
Generate the channel reference doc and the example channel config from
the JSON files in /reference.

Usage:
    python scripts/generate_channel_docs.py

Outputs:
    docs/channels.md            -- scraper id reference tables
    config/channels.example.yaml -- ready-to-use full channel config
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CNTV_TYPE_ORDER = ["央视", "卫视", "地方", "CETV", "数字", "原创", "其他"]


def load_reference(name: str) -> list[dict]:
    with open(os.path.join(ROOT, "reference", f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def pretty_name(chname: str) -> str:
    """CCTV1综合 -> CCTV1 综合 (keep other names untouched)."""
    match = re.match(r"^(CCTV[0-9]*\+?)([^0-9+].*)$", chname)
    if match and not match.group(2).startswith("-"):
        return f"{match.group(1)} {match.group(2)}"
    return chname


def channel_key(chname: str, ename: str) -> str:
    """A yaml-friendly channel id."""
    return ename.lower().replace(" ", "")


def group_by_type(channels: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for channel in channels:
        groups.setdefault(channel["type"], []).append(channel)
    return groups


def gen_docs(cntv: list[dict], tvmao: list[dict]) -> str:
    lines = [
        "# 频道配置参考",
        "",
        "本文档由 `scripts/generate_channel_docs.py` 根据 [`/reference`](../reference) 目录中的数据自动生成，",
        "列出了各刮削器可用的频道 id，便于快速编写 [`/config/channels.yaml`](../config/channels.yaml)。",
        "",
        "完整的示例配置见 [`/config/channels.example.yaml`](../config/channels.example.yaml)，可直接复制需要的频道段落。",
        "",
        "## 配置格式速查",
        "",
        "```yaml",
        "频道id:            # 输出到 xmltv 的频道 id，对应播放器 m3u8 里的 tvg-id",
        "  name:",
        "    - 显示名        # DIYP 接口用第一个显示名匹配频道",
        "  scraper:          # 依次尝试，直到成功",
        "    cctv: cctv1     # 刮削器名: 该刮削器中的频道 id",
        "    tvmao: CCTV1",
        "  refresh: once     # once=只增补 / today=刷新今天",
        "  recap: 7          # 保留过去 7 天",
        "  preview: 2        # 预抓未来 2 天",
        "```",
        "",
        "## cctv 刮削器（tv.cctv.com，央视官方，推荐）",
        "",
        "数据来源为央视官方接口，覆盖央视、卫视和部分地方频道，稳定性最好。",
        "",
    ]
    groups = group_by_type(cntv)
    for type_name in CNTV_TYPE_ORDER:
        channels = groups.get(type_name)
        if not channels:
            continue
        lines += [f"### {type_name}", "", "| 频道 | scraper id |", "| --- | --- |"]
        for channel in channels:
            lines.append(f"| {pretty_name(channel['chname'])} | `{channel['ename']}` |")
        lines.append("")
    lines += [
        "## tvmao 刮削器（tvmao.com 电视猫）",
        "",
        "覆盖各省卫视，可作为 cctv 刮削器的备选数据源。只能获取本周（周一到周日）范围内的节目表。",
        "",
        "| 频道 | scraper id |",
        "| --- | --- |",
    ]
    for channel in tvmao:
        lines.append(f"| {channel['chname']} | `{channel['ename']}` |")
    lines += [
        "",
        "## 其它刮削器",
        "",
        "### cztv（cztv.com 浙江广电）",
        "",
        "scraper id 为 cztv 接口中的 station id，例如：",
        "",
        "```yaml",
        "zhejiangtv:",
        "  name:",
        "    - 浙江卫视",
        "  scraper:",
        "    cztv: 31",
        "```",
        "",
        "### tvsou（tvsou.com 搜视网）",
        "",
        "scraper id 为搜视网 URL `https://www.tvsou.com/epg/<id>/` 中的路径段。只能获取本周范围内的节目表。",
        "",
        "### mytvsuper（mytvsuper.com，香港 TVB）",
        "",
        "scraper id 为频道的 network code，完整列表见",
        "[iptv-org 的频道文件](https://github.com/iptv-org/epg/blob/master/sites/mytvsuper.com/mytvsuper.com.channels.xml)。",
        "在频道配置中可加 `lang: en` 输出英文节目名（默认繁体中文）。",
        "",
        "```yaml",
        "tvb_pearl:",
        "  name:",
        "    - 明珠台",
        "  scraper:",
        "    mytvsuper: PEAR",
        "```",
        "",
        "### discoverychannel_tw（discoverychannel.com.tw）",
        "",
        "scraper id 为台湾探索频道网站上的 channel 参数，如 `DC`。",
        "",
        "### xmltv（任意远程 XMLTV 文件）",
        "",
        "把别处生成的 xmltv 文件作为数据源，两种写法：",
        "",
        "```yaml",
        "somechannel:",
        "  name:",
        "    - 某频道",
        "  scraper:",
        "    # 远程文件中的频道 id 与本频道 id 相同时，直接写 URL：",
        "    xmltv: https://example.com/epg.xml",
        "    # 频道 id 不同时，用 远程id@URL 的形式映射：",
        "    # xmltv: remote_id@https://example.com/epg.xml",
        "```",
        "",
        "同一个 URL 在一次更新中只会下载一次（进程内缓存），多个频道共用同一来源不会重复抓取。",
        "",
    ]
    return "\n".join(lines)


def yaml_entry(
    key: str,
    display_name: str,
    scrapers: list[tuple[str, str]],
    refresh: str = "once",
    recap: int = 7,
    preview: int = 2,
) -> str:
    lines = [f"{key}:", "  name:", f"    - {display_name}", "  scraper:"]
    for scraper, scraper_id in scrapers:
        lines.append(f"    {scraper}: {scraper_id}")
    lines += [f"  refresh: {refresh}", f"  recap: {recap}", f"  preview: {preview}"]
    return "\n".join(lines)


def gen_example_config(cntv: list[dict], tvmao: list[dict]) -> str:
    tvmao_by_name = {channel["chname"]: channel["ename"] for channel in tvmao}
    parts = [
        "# 完整频道配置参考（由 scripts/generate_channel_docs.py 自动生成）",
        "#",
        "# 用法：从本文件复制需要的频道段落到 config/channels.yaml，",
        "# 或直接以本文件为底稿删掉不需要的频道。",
        "# 频道 id 与 scraper id 的对照表见 docs/channels.md。",
        "---",
    ]
    groups = group_by_type(cntv)
    for type_name in CNTV_TYPE_ORDER:
        channels = groups.get(type_name)
        if not channels:
            continue
        parts.append(f"\n# ==================== {type_name} ====================\n")
        for channel in channels:
            display = pretty_name(channel["chname"])
            scrapers = [("cctv", channel["ename"])]
            # 卫视频道追加 tvmao 作为备选数据源
            tvmao_id = tvmao_by_name.get(channel["chname"])
            if tvmao_id:
                scrapers.append(("tvmao", tvmao_id))
            parts.append(
                yaml_entry(channel_key(channel["chname"], channel["ename"]), display, scrapers)
            )
            parts.append("")
    # tvmao 独有的频道（cntv 没有对应名字的）
    cntv_names = {channel["chname"] for channel in cntv}
    tvmao_only = [channel for channel in tvmao if channel["chname"] not in cntv_names]
    if tvmao_only:
        parts.append("\n# ============== 以下频道仅 tvmao 提供 ==============\n")
        for channel in tvmao_only:
            parts.append(
                yaml_entry(
                    channel_key(channel["chname"], channel["ename"]),
                    channel["chname"],
                    [("tvmao", channel["ename"])],
                )
            )
            parts.append("")
    parts += [
        "# ============== 其它数据源示例（按需取消注释） ==============",
        "#",
        "# tvb_pearl:",
        "#   name:",
        "#     - 明珠台",
        "#   scraper:",
        "#     mytvsuper: PEAR",
        "#   refresh: once",
        "#   recap: 7",
        "#   preview: 2",
        "#",
        "# discovery_tw:",
        "#   name:",
        "#     - Discovery 探索频道",
        "#   scraper:",
        "#     discoverychannel_tw: DC",
        "#   refresh: once",
        "#   recap: 7",
        "#   preview: 2",
        "#",
        "# remote_xmltv_example:",
        "#   name:",
        "#     - 远程XMLTV频道",
        "#   scraper:",
        "#     xmltv: remote_channel_id@https://example.com/epg.xml",
        "#   refresh: once",
        "#   recap: 7",
        "#   preview: 2",
        "",
    ]
    return "\n".join(parts)


def main() -> None:
    cntv = load_reference("cntv")
    tvmao = load_reference("tvmao")
    docs_dir = os.path.join(ROOT, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    docs_path = os.path.join(docs_dir, "channels.md")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(gen_docs(cntv, tvmao))
    print("wrote", docs_path)
    example_path = os.path.join(ROOT, "config", "channels.example.yaml")
    with open(example_path, "w", encoding="utf-8") as f:
        f.write(gen_example_config(cntv, tvmao))
    print("wrote", example_path)


if __name__ == "__main__":
    main()
