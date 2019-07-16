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
    @staticmethod
    def response(flow: HTTPFlow):
        if flow.server_conn.ip_address == IP_ADDRESS:
            if flow.request.path == '/quest/battleFinish':
                try:
                    response = aadict.d2ar(json.loads(flow.response.text))
                    battle_drops(response)
                    penguin_stats_report(response)
                except (AttributeError, AssertionError):
                    pass


addons = [PRTS()]

if __name__ == '__main__':
    def main():
        mitmdump(('--quiet', '--scripts', __file__))
        # mitmdump(('--verbose', '--flow-detail', '2', '--scripts', __file__))


    main()
