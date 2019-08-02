#!/usr/bin/env python3
"""
DON'T BE EVIL
"""

import json
import logging
import socket

from aadict import aadict
from mitmproxy.http import HTTPFlow
from mitmproxy.tools.main import mitmdump

from battle_drops import battle_drops
from penguin_stats_report import penguin_stats_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')

IP_ADDRESS = (socket.gethostbyname('ak-gs.hypergryph.com'), 8443)


class PRTS:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_stage_id(self, response):
        _modified = response.playerDataDelta.modified
        if _modified.dungeon and _modified.dungeon.stages:
            for stage in _modified.dungeon.stages.values():
                if stage.completeTimes > 0:
                    self.logger.debug(f'get stageId from response:{stage.stageId}')
                    return stage.stageId

    def response(self, flow: HTTPFlow):
        if flow.server_conn.ip_address == IP_ADDRESS:
            if flow.request.path == '/quest/battleFinish':
                response = aadict.d2ar(json.loads(flow.response.text))
                stage_id = self._get_stage_id(response)
                if stage_id:
                    # noinspection PyBroadException
                    try:
                        battle_drops(response, stage_id)
                        penguin_stats_report(response, stage_id)
                    except Exception:
                        self.logger.exception('')


addons = [PRTS()]

if __name__ == '__main__':
    def main():
        mitmdump(('--quiet', '--scripts', __file__))
        # mitmdump(('--verbose', '--flow-detail', '2', '--scripts', __file__))


    main()
