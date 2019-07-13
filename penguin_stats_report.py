"""
Post battle drops data to Penguin Statistics

more info: https://penguin-stats.io
"""
import copy
import json
import logging
from collections import defaultdict
from http.cookiejar import LWPCookieJar
from multiprocessing import Process

import requests
from aadict import aadict

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
_penguin_stats_api_report = 'https://penguin-stats.io/PenguinStats/api/report'


def _do_post(data):
    session = requests.session()
    cookies_helper = CookiesHelper()
    cookies_helper.load_cookies(session.cookies)
    response = session.post(_penguin_stats_api_report,
                            data=data,
                            headers={'Content-Type': 'application/json'})
    for header in response.request.headers.items():
        logger.debug(f'request: {header}')
    for header in response.headers.items():
        logger.debug(f'response: {header}')
    if response.cookies:
        cookies_helper.save_cookies(session.cookies)


def penguin_stats_report(response):
    stages = list(response.playerDataDelta.modified.dungeon.stages.values())

    if stages[0].stageId not in _penguin_stats_accept_stages:
        logger.debug(f'skip stage: {stages[0].stageId}')
        return

    drops = defaultdict(int)
    for rewards in (response.rewards,
                    response.unusualRewards,
                    response.additionalRewards):
        for _drop in rewards:
            if _drop.id != '4001' and _drop.count > 0:
                drops[_drop.id] += _drop.count
    drops = [{"itemId": item, "quantity": count} for item, count in drops.items()]
    furniture_num = sum(_drop.count for _drop in response.furnitureRewards)
    report_content = aadict({
        "stageId": stages[0].stageId,
        "furnitureNum": furniture_num,
        "drops": drops,
        "source": "otz/arknights-drop-sniffer",
        "version": "v0.2.3"
    })
    report_content = json.dumps(report_content, separators=(',', ':'))

    # TODO: decide what to do when furnitureNum != 0
    if furniture_num != 0:
        logger.error(f'furnitureNum:{furniture_num}')
        return

    Process(target=_do_post, args=(report_content,)).start()
