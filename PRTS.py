#!/usr/bin/env python3
"""
DON'T BE EVIL
"""

import json

from aadict import aadict
from mitmproxy.http import HTTPFlow
from mitmproxy.tools.main import mitmdump

from battle_drops import battle_drops
from penguin_stats_report import penguin_stats_report


class PRTS:
    @staticmethod
    def response(flow: HTTPFlow):
        if flow.request.host == 'ak-gs.hypergryph.com':
            if flow.request.path == '/quest/battleFinish':
                try:
                    response = aadict.d2ar(json.loads(flow.response.text))
                    battle_drops(response)
                    penguin_stats_report(response)
                except AttributeError:
                    pass


addons = [PRTS()]

if __name__ == '__main__':
    import logging


    def main():
        logging.basicConfig(level=logging.DEBUG, format='%(name)s %(message)s')
        mitmdump(('--quiet', '--scripts', __file__))


    main()
