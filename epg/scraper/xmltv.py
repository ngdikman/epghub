from epg.scraper import xmlxmltv
from epg.model import Channel, Program
from datetime import datetime, date, timezone

def update(
    channel: Channel, scraper_params: str, dt: date = datetime.today().date()
) -> bool:
    # 解析参数
    if "@http" in scraper_params:
        scraper_id, scraper_url = scraper_params.split("@http", 1)
        scraper_url = f"http{scraper_url}"  # 正确处理http/https
    else:
        scraper_id = None
        scraper_url = scraper_params
    
    # 确定要匹配的频道ID
    channel_id = scraper_id if scraper_id is not None else channel.id
    
    # 获取源数据
    scraper_channels = xmlxmltv.get_channels(scraper_url)
    if not scraper_channels:
        return False
    
    # 查找匹配频道
    target_channel = next(
        (c for c in scraper_channels if c.id == channel_id), 
        None
    )
    if not target_channel:
        return False
    
    # 清空当前频道指定日期的节目
    channel.flush(dt)
    
    # 添加新节目
    added = False
    for program in target_channel.programs:
        if program.start_time.date() == dt:
            channel.programs.append(
                Program(
                    program.title,
                    program.start_time,
                    program.end_time,
                    channel.id,
                    program.description,
                    sub_title=program.sub_title
                )
            )
            added = True
    
    if added:
        channel.metadata.update(
            {"last_update": datetime.now(timezone.utc).astimezone()}
        )
    
    return added