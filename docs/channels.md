# 频道配置参考

本文档由 `scripts/generate_channel_docs.py` 根据 [`/reference`](../reference) 目录中的数据自动生成，
列出了各刮削器可用的频道 id，便于快速编写 [`/config/channels.yaml`](../config/channels.yaml)。

完整的示例配置见 [`/config/channels.example.yaml`](../config/channels.example.yaml)，可直接复制需要的频道段落。

## 配置格式速查

```yaml
频道id:            # 输出到 xmltv 的频道 id，对应播放器 m3u8 里的 tvg-id
  name:
    - 显示名        # DIYP 接口用第一个显示名匹配频道
  scraper:          # 依次尝试，直到成功
    cctv: cctv1     # 刮削器名: 该刮削器中的频道 id
    tvmao: CCTV1
  refresh: once     # once=只增补 / today=刷新今天
  recap: 7          # 保留过去 7 天
  preview: 2        # 预抓未来 2 天
  xml_lang: zh      # 可选，输出 xmltv 的 lang 语言属性
```

## cctv 刮削器（tv.cctv.com，央视官方，推荐）

数据来源为央视官方接口，覆盖央视、卫视和部分地方频道，稳定性最好。

### 央视

| 频道 | scraper id |
| --- | --- |
| CCTV1 综合 | `cctv1` |
| CCTV2 财经 | `cctv2` |
| CCTV3 综艺 | `cctv3` |
| CCTV4 中文国际 | `cctv4` |
| CCTV4 欧洲 | `cctveurope` |
| CCTV4 美洲 | `cctvamerica` |
| CCTV5 体育 | `cctv5` |
| CCTV5+ 体育赛事 | `cctv5plus` |
| CCTV6 电影 | `cctv6` |
| CCTV7 国防军事 | `cctv7` |
| CCTV8 电视剧 | `cctv8` |
| CCTV9 纪录(英) | `cctvdoc` |
| CCTV9 纪录 | `cctvjilu` |
| CCTV10 科教 | `cctv10` |
| CCTV11 戏曲 | `cctv11` |
| CCTV12 社会与法 | `cctv12` |
| CCTV13 新闻 | `cctv13` |
| CCTV14 少儿 | `cctvchild` |
| CCTV15 音乐 | `cctv15` |
| CCTV-Español | `cctvxiyu` |
| CCTV-Français | `cctvfrench` |
| CCTV-NEWS | `cctv9` |
| CCTV-Русский | `cctvrussian` |
| CCTV-العربية | `cctvarabic` |

### 卫视

| 频道 | scraper id |
| --- | --- |
| 安徽卫视 | `anhui` |
| 北京卫视 | `btv1` |
| 东方卫视 | `dongfang` |
| 湖南卫视 | `hunan` |
| 江苏卫视 | `jiangsu` |
| 浙江卫视 | `zhejiang` |
| 山东卫视 | `shandong` |
| 天津卫视 | `tianjin` |
| 内蒙古卫视 | `neimenggu` |
| 东南卫视 | `dongnan` |
| 河南卫视 | `henan` |
| 广西卫视 | `guangxi` |
| 贵州卫视 | `guizhou` |
| 甘肃卫视 | `gansu` |
| 辽宁卫视 | `liaoning` |
| 江西卫视 | `jiangxi` |
| 湖北卫视 | `hubei` |
| 旅游卫视 | `travel` |
| 云南卫视 | `yunnan` |
| 青海卫视 | `qinghai` |
| 厦门卫视 | `xiamen` |
| 河北卫视 | `hebei` |
| 吉林卫视 | `jilin` |
| 重庆卫视 | `chongqing` |
| 西藏卫视 | `xizang` |
| 宁夏卫视 | `ningxia` |
| 山西卫视 | `shan1xi` |
| 黑龙江卫视 | `heilongjiang` |
| 山东教育台 | `sdetv` |
| 广东卫视 | `guangdong` |
| 四川卫视 | `sichuan` |
| 陕西卫视 | `shan3xi` |
| 新疆卫视 | `xinjiang` |
| 香港卫视 | `xianggangweishi` |
| 延边卫视 | `yanbian` |
| 兵团卫视 | `bingtuan` |
| 深圳卫视 | `shenzhen` |

### 地方

| 频道 | scraper id |
| --- | --- |
| BTV财经 | `btv5` |
| BTV文艺 | `btv2` |
| BTV科教 | `btv3` |
| BTV影视 | `btv4` |
| BTV生活 | `btv7` |
| BTV青少 | `btv8` |
| BTV体育 | `btv6` |
| BTV新闻 | `btv9` |
| 滨海综艺频道 | `tianjinbh2` |
| 厦门一套 | `xiamen1` |
| 厦门二套 | `xiamen2` |
| 厦门三套 | `xiamen3` |
| 厦门四套 | `xiamen4` |
| 珠海一套 | `zhuhaiyitao` |
| 珠海二套 | `zhuhaiertao` |
| 邢台综合 | `xingtaizonghe` |
| 邢台生活 | `xingtaishenghuo` |
| 辽宁都市 | `liaoningds` |
| 成都新闻综合 | `cdtv1` |
| 成都公共 | `cdtv5` |
| 滨海新闻综合 | `tianjinbh` |
| 成都经济资讯服务 | `cdtv2new` |
| 宁波一套 | `nbtv1` |
| 宁波二套 | `nbtv2` |
| 宁波三套 | `nbtv3` |
| 广西综艺 | `gxzy` |
| 天津1套 | `tianjin1` |
| 天津2套 | `tianjin2` |
| BTV卡酷少儿 | `btvchild` |
| BTV纪实 | `btvjishi` |
| BTV国际 | `btvInternational` |
| 邢台沙河 | `xingtaishahe` |
| 宁波四套 | `nbtv4` |
| 宁波五套 | `nbtv5` |
| 邢台公共 | `xingtaigonggong` |

### CETV

| 频道 | scraper id |
| --- | --- |
| CETV-1 | `cetv1` |
| CETV-2 | `cetv2` |
| CETV-3 | `cetv3` |

### 数字

| 频道 | scraper id |
| --- | --- |
| CCTV 风云足球 | `cctvfyzq` |
| CCTV 高尔夫网球 | `cctvgaowang` |
| CCTV 央视台球 | `taiqiu` |
| CCTV 电视指南 | `zhinan` |
| CCTV 风云剧场 | `fyjc` |
| CCTV  电影 | `cctvdianying` |
| CCTV 怀旧剧场 | `hjjc` |
| CCTV 第一剧场 | `diyijuchang` |
| CCTV 世界地理 | `shijiedili` |
| CCTV 新科动漫 | `xinkedongman` |
| CCTV 老故事 | `cctvlaogushi` |
| CCTV 发现之旅 | `faxianzhilv` |
| CCTV 央视文化精品 | `jingpin` |
| CCTV 风云音乐 | `fyyy` |
| CCTV 中视购物 | `dianshigouwu` |
| CCTV 中学生 | `zhongxuesheng` |
| CCTV 娱乐 | `cctvyule` |
| CCTV 戏曲 | `cctvxiqu` |
| CCTV 国防军事 | `guofang` |
| CCTV 女性时尚 | `shishang` |
| CCTV 气象 | `cctvqixiang` |
| 证券资讯 | `cctvzhengquanzixun` |
| 靓妆 | `cctvliangzhuang` |
| 梨园 | `cctvliyuan` |
| 汽摩 | `cctvqimo` |
| 中国3D电视试验频道 | `cctv3d` |
| 天元围棋 | `tianyuanweiqi` |
| 茶频道 | `xianfengjilu` |
| 现代女性 | `xiandainvxing` |
| 英语辅导 | `yingyufudao` |
| 游戏竞技 | `youxijingji` |
| 环球奇观 | `huanqiuqiguan` |
| 书画 | `shuhua` |
| DV生活 | `dvshenghuo` |
| 彩民在线 | `caimingzaixian` |
| 高尔夫 | `gaoerfu` |
| 早期教育 | `zaoqijiaoyu` |
| 宝贝家 | `baobeijia` |
| 留学世界 | `liuxueshijie` |
| 摄影 | `sheyingpindao` |
| 国学频道 | `shuowenjiezi` |
| 文物宝库 | `wenwubaoku` |
| 武术世界 | `wushushijie` |
| 快乐垂钓 | `kuailechuidiao` |
| 卫生健康 | `wsjk` |

### 原创

| 频道 | scraper id |
| --- | --- |
| 熊猫频道 | `ipanda` |
| 中国功夫频道 | `cntvgongfu` |
| 中国美食频道 | `cntvmeishi` |
| 人文历史频道 | `cntvlishi` |
| 中国旅游频道 | `cntvtravel` |

### 其他

| 频道 | scraper id |
| --- | --- |
| CCTV 外语节目单 | `cctvwaiyu` |
| 大型活动部网络春晚 | `wlchunwan` |

## tvmao 刮削器（tvmao.com 电视猫）

覆盖各省卫视，可作为 cctv 刮削器的备选数据源。只能获取本周（周一到周日）范围内的节目表。

| 频道 | scraper id |
| --- | --- |
| 北京卫视 | `BTV1` |
| 卡酷少儿 | `BTV10` |
| 重庆卫视 | `CCQTV1` |
| 东南卫视 | `FJTV2` |
| 厦门卫视 | `XMTV5` |
| 甘肃卫视 | `GSTV1` |
| 广东卫视 | `GDTV1` |
| 深圳卫视 | `SZTV1` |
| 南方卫视（上星版）* | `NANFANG2` |
| 广西卫视 | `GUANXI1` |
| 贵州卫视 | `GUIZOUTV1` |
| 海南卫视 | `TCTC1` |
| 河北卫视 | `HEBEI1` |
| 黑龙江卫视 | `HLJTV1` |
| 河南卫视 | `HNTV1` |
| 湖北卫视 | `HUBEI1` |
| 湖南卫视 | `HUNANTV1` |
| 湖南金鹰卡通频道 | `HUNANTV2` |
| 江苏卫视 | `JSTV1` |
| 江西卫视 | `JXTV1` |
| 吉林卫视 | `JILIN1` |
| 辽宁卫视 | `LNTV1` |
| 内蒙卫视 | `NMGTV1` |
| 宁夏卫视 | `NXTV2` |
| 山西卫视 | `SXTV1` |
| 山东卫视 | `SDTV1` |
| 东方卫视 | `DONGFANG1` |
| 哈哈炫动 | `TOONMAX1` |
| 陕西卫视 | `SHXITV1` |
| 四川卫视 | `SCTV1` |
| 天津卫视 | `TJTV1` |
| 新疆卫视 | `XJTV1` |
| 云南卫视 | `YNTV1` |
| 浙江卫视 | `ZJTV1` |
| 青海卫视 | `QHTV1` |
| 西藏卫视(藏语) | `XIZANGTV1` |
| 西藏卫视 | `XIZANGTV2` |
| 延边卫视 | `YANBIAN1` |
| 兵团卫视 | `BINGTUAN` |
| 海峡卫视 | `HXTV` |
| 黄河卫视 | `HHWS` |
| 康巴卫视 | `KAMBA-TV` |
| 三沙卫视 | `SANSHATV` |
| 安徽卫视 | `AHTV1` |

## 其它刮削器

以下数据源没有内置的完整频道清单，可在能访问对应网站的机器上运行
`python scripts/list_channels.py <刮削器名> --save` 自动探测并保存到
`/reference`，然后重新运行本生成脚本，就会在下方生成对照表。

### cztv（cztv.com 浙江广电）

scraper id 为 cztv 接口中的 station id，例如：

```yaml
zhejiangtv:
  name:
    - 浙江卫视
  scraper:
    cztv: 31
```

### tvsou（tvsou.com 搜视网）

scraper id 为搜视网 URL `https://www.tvsou.com/epg/<id>/` 中的路径段。只能获取本周范围内的节目表。

搜视网没有公开的频道 id 清单，且 id 格式不统一——部分频道是 8 位十六进制哈希（如杭州综合是 `630175b5`），
部分是可读名称（如江苏卫视是 `JSTV-1`），无法批量推导。查找方法：

1. 在 [tvsou.com](https://www.tvsou.com/) 搜索频道名，进入该频道的节目表页面
2. 复制地址栏 `https://www.tvsou.com/epg/<id>/` 中的 `<id>` 部分

```yaml
htv:
  name:
    - 杭州综合
  scraper:
    tvsou: 630175b5
```

搜视网覆盖了大量 cctv/tvmao 没有的地方频道和数字频道，适合作为查漏补缺的数据源。

### mytvsuper（mytvsuper.com，香港 TVB）

scraper id 为频道的 network code。官方频道列表接口为
`https://content-api.mytvsuper.com/v1/channel/list?platform=web`，
可用 `python scripts/list_channels.py mytvsuper --save` 一键获取。
在频道配置中可加 `lang: en` 输出英文节目名（默认繁体中文）。

```yaml
PhoenixChineseChannel.hk:
  name:
    - 凤凰卫视中文
  scraper:
    mytvsuper: PCC
```

### nowtv（nowplayer.now.com，香港 Now 宽频电视）

scraper id 为 Now 节目表接口中的 channelNo（如 Now 新闻台是 `332`）。
官方频道列表接口为 `https://nowplayer.now.com/tvguide/channellist`，
可用 `python scripts/list_channels.py nowtv --save` 一键获取。
在频道配置中可加 `lang: en` 输出英文节目名（默认中文）。
只能获取今天起 7 天内的节目表，无历史数据（recap 依赖 XML 复用）。

```yaml
NowNews.hk:
  name:
    - Now新闻台
  scraper:
    nowtv: 332
```

### discoverychannel_tw（discoverychannel.com.tw）

scraper id 为台湾探索频道排片接口的数字 channel 参数，例如探索频道亚洲是 `4`：

```yaml
DiscoveryChannelAsia.tw:
  name:
    - 探索频道亚洲
  scraper:
    discoverychannel_tw: 4
```

可用 `python scripts/list_channels.py discoverychannel_tw` 探测哪些 id 有效。

### astro（astro.com.my，马来西亚 Astro 卫星电视）

scraper id 为 Astro 频道的数字 ID（如 TV1 是 `711`）。
可用 `python scripts/list_channels.py astro --save` 一键获取全部频道列表。

```yaml
TV1:
  name:
    - TV1
  scraper:
    astro: 711
```

| 频道 | scraper id |
| --- | --- |
| TV1 | `711` |
| TV2 | `5027` |
| RIA | `1004` |
| PRIMA | `1000` |
| OASIS | `2505` |
| CITRA | `2700` |
| RANIA | `608` |
| AURA | `609` |
| TV ALHIJRAH | `1113` |
| COLORS | `2611` |
| Zee Cinema | `5106` |
| TVS | `5021` |
| TV OKEY | `5072` |
| VAANAVIL | `2309` |
| VINMEEN | `2105` |
| SUN TV | `2310` |
| SUN MUSIC | `5011` |
| ADITHYA | `915` |
| Sun News | `5087` |
| KTV | `5088` |
| Sun Life | `5089` |
| STAR VIJAY | `2707` |
| COLORS TAMIL | `2101` |
| ZEE TAMIL | `2311` |
| THANGATHIRAI | `2109` |
| iQIYI | `1006` |
| TVB CLASSIC | `5016` |
| AEC | `2400` |
| QJ | `2507` |
| CELESTIAL | `506` |
| TVBJ | `2600` |
| AOD | `2706` |
| CTI ASIA | `5017` |
| TVB E-NEWS | `5015` |
| TVB XING HE | `401` |
| TVBS ASIA | `402` |
| CCM | `100` |
| PHOENIX | `400` |
| PHOENIX NEWS | `5009` |
| HUA HEE DAI | `2308` |
| CCTV4 | `403` |
| KBSW | `2306` |
| Astro Daebak | `5211` |
| tvN | `1001` |
| KPLUS | `9983` |
| HITS MOVIES | `2305` |
| BOO | `2407` |
| Astro Showtime | `5145` |
| Astro FAM Time | `5186` |
| SHOWCASE | `5054` |
| Rock Action | `5143` |
| Rock X Stream | `5144` |
| tvN Movies | `2406` |
| AWANI | `5025` |
| Bernama TV | `1114` |
| CGTN | `5019` |
| Berita RTM | `5213` |
| CNN | `2503` |
| BBC News | `1008` |
| AL JAZEERA | `2110` |
| CNA | `605` |
| CNBC | `900` |
| BLOOMBERG  TV | `5020` |
| ABC AUSTRALIA | `5075` |
| DW | `9984` |
| FRANCE24 | `9985` |
| Love Nature | `5096` |
| DISCOVERY | `2510` |
| DISCOVERY ASIA | `501` |
| BBC Earth | `5051` |
| HISTORY | `604` |
| CGTN Documentary | `5119` |
| TUTOR TV | `5071` |
| CERIA | `2606` |
| CARTOON NTWK | `509` |
| NICKELODEON | `2511` |
| NICK JR | `9982` |
| Moonbug Kids | `5067` |
| Blippi & Friends | `5175` |
| AXN | `2303` |
| HITS NOW | `5110` |
| Lifetime | `5052` |
| HITS | `606` |
| TLC | `2709` |
| AFN | `500` |
| CI | `2111` |
| HGTV | `2502` |
| ARENA | `2604` |
| ARENA 2 | `5057` |
| ARENA BOLA | `5099` |
| ARENA BOLA 2 | `5100` |
| Sukan+ | `5212` |
| Astro Grandstand | `2701` |
| Astro Premier League | `601` |
| Astro Premier League 2 | `2104` |
| Astro Football | `2506` |
| Astro Badminton | `5170` |
| Astro Sports Plus | `5171` |
| Astro Tennis | `5210` |
| beIN SPORTS | `408` |
| beIN SPORTS 2 | `5066` |
| bEIN SPORTS 3 | `2705` |
| W-Sport | `5060` |
| GOLF CHANNEL | `1003` |
| Cricbuzz | `2504` |
| Premier Sports | `2601` |

### xmltv（任意远程 XMLTV 文件）

把别处生成的 xmltv 文件作为数据源，两种写法：

```yaml
somechannel:
  name:
    - 某频道
  scraper:
    # 远程文件中的频道 id 与本频道 id 相同时，直接写 URL：
    xmltv: https://example.com/epg.xml
    # 频道 id 不同时，用 远程id@URL 的形式映射：
    # xmltv: remote_id@https://example.com/epg.xml
```

同一个 URL 在一次更新中只会下载一次（进程内缓存），多个频道共用同一来源不会重复抓取。
