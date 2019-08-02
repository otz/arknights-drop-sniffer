"""
Post battle drops data to Penguin Statistics

more info: https://penguin-stats.io
"""
__source__ = 'otz/arknights-drop-sniffer'
__version__ = '0.2.5'

import copy
import json
import logging
from collections import defaultdict
from http.cookiejar import LWPCookieJar
from multiprocessing import Process

import requests

logger = logging.getLogger(__name__)


class CookiesHelper:
    def __init__(self, filename='penguin_stats_cookies.txt'):
        self.filename = filename

    def load_cookies(self, cookies):
        try:
            _cookies = LWPCookieJar(self.filename)
            _cookies.load(ignore_discard=True)
            for cookie in _cookies:
                cookies.set_cookie(copy.copy(cookie))
        except OSError:
            pass

    def save_cookies(self, cookies):
        _cookies = LWPCookieJar(self.filename)
        for cookie in cookies:
            _cookies.set_cookie(copy.copy(cookie))
        _cookies.save(ignore_discard=True)


_penguin_stats_accept_stages = [
    'a001_01', 'a001_02', 'a001_03', 'a001_04', 'a001_05', 'a001_06',
    'main_00-01', 'main_00-02', 'main_00-03', 'main_00-04', 'main_00-05',
    'main_00-06', 'main_00-07', 'main_00-08', 'main_00-09', 'main_00-10', 'main_00-11',
    'main_01-01', 'main_01-03', 'main_01-04', 'main_01-05', 'main_01-06',
    'main_01-07', 'main_01-08', 'main_01-09', 'main_01-10', 'main_01-12',
    'main_02-01', 'main_02-02', 'main_02-03', 'main_02-04', 'main_02-05',
    'main_02-06', 'main_02-07', 'main_02-08', 'main_02-09', 'main_02-10',
    'sub_02-01', 'sub_02-02', 'sub_02-03', 'sub_02-04', 'sub_02-05', 'sub_02-06',
    'sub_02-07', 'sub_02-08', 'sub_02-09', 'sub_02-10', 'sub_02-11', 'sub_02-12',
    'main_03-01', 'main_03-02', 'main_03-03', 'main_03-04',
    'main_03-05', 'main_03-06', 'main_03-07', 'main_03-08',
    'sub_03-1-1', 'sub_03-1-2', 'sub_03-2-1', 'sub_03-2-2', 'sub_03-2-3',
    'main_04-01', 'main_04-02', 'main_04-03', 'main_04-04', 'main_04-05',
    'main_04-06', 'main_04-07', 'main_04-08', 'main_04-09', 'main_04-10',
    'sub_04-1-1', 'sub_04-1-2', 'sub_04-1-3', 'sub_04-2-1',
    'sub_04-2-2', 'sub_04-2-3', 'sub_04-3-1', 'sub_04-3-2', 'sub_04-3-3',
    'main_05-01', 'main_05-02', 'main_05-03', 'main_05-04', 'main_05-05',
    'main_05-06', 'main_05-07', 'main_05-08', 'main_05-09', 'main_05-10',
    'sub_05-1-1', 'sub_05-1-2', 'sub_05-2-1', 'sub_05-2-2', 'sub_05-3-1', 'sub_05-3-2',
    'wk_fly_1', 'wk_fly_2', 'wk_fly_3', 'wk_fly_4', 'wk_fly_5',
    'wk_armor_1', 'wk_armor_2', 'wk_armor_3', 'wk_armor_4', 'wk_armor_5'
]
_penguin_stats_accept_items = [
    '2004', '2003', '2002', '2001',  # 作战记录
    '30074', '30073',  # 醇
    '30084', '30083',  # 锰
    '30094', '30093',  # 研磨石
    '30104', '30103',  # RMA70
    '30014', '30013', '30012', '30011',  # 源岩
    '30064', '30063', '30062', '30061',  # 装置
    '30034', '30033', '30032', '30031',  # 酯
    '30024', '30023', '30022', '30021',  # 糖
    '30044', '30043', '30042', '30041',  # 铁
    '30054', '30053', '30052', '30051',  # 酮
    '3114', '3113', '3112',  # 碳
    '3303', '3302', '3301',  # 书
    '3003'  # 赤金
]
_penguin_stats_api_report = 'https://penguin-stats.io/PenguinStats/api/report'


def _do_post(data):
    session = requests.session()
    cookies_helper = CookiesHelper()
    cookies_helper.load_cookies(session.cookies)
    response = session.post(_penguin_stats_api_report,
                            data=data,
                            headers={'Content-Type': 'application/json'})
    if response.ok:
        logger.info('OK')
    for header in response.request.headers.items():
        logger.debug(f'request: {header}')
    for header in response.headers.items():
        logger.debug(f'response: {header}')
    if response.cookies or any(h.cookies for h in response.history):
        cookies_helper.save_cookies(session.cookies)


def penguin_stats_report(response, stage_id):
    if stage_id not in _penguin_stats_accept_stages:
        logger.debug(f'skip stage: {stage_id}')
        return

    drops = defaultdict(int)
    for rewards in (response.rewards,
                    response.unusualRewards,
                    response.additionalRewards):
        for _drop in rewards:
            if _drop.id in _penguin_stats_accept_items and _drop.count > 0:
                drops[_drop.id] += _drop.count
    drops = [{"itemId": item, "quantity": count} for item, count in drops.items()]
    furniture_num = sum(_drop.count for _drop in response.furnitureRewards)
    report_content = {
        "stageId": stage_id,
        "furnitureNum": furniture_num,
        "drops": drops,
        "source": __source__,
        "version": __version__
    }
    report_content = json.dumps(report_content, separators=(',', ':'))

    Process(target=_do_post, args=(report_content,)).start()
