#!/usr/bin/env python3
"""
DON'T BE EVIL
"""

import json
import logging
import socket

import aadict
import mitmproxy.ctx
import mitmproxy.http
import mitmproxy.tools.main
import tornado.httpserver
import tornado.log
import tornado.web

from battle_drops import battle_drops
from penguin_stats_report import penguin_stats_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')


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

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.request.host == 'ak-gs.hypergryph.com':
            if flow.request.path == '/quest/battleFinish':
                response = aadict.aadict.d2ar(json.loads(flow.response.text))
                stage_id = self._get_stage_id(response)
                if stage_id:
                    try:
                        battle_drops(response, stage_id)
                        penguin_stats_report(response, stage_id)
                    except Exception:
                        self.logger.exception('')


addons = [PRTS()]


class ProxyAutoConfig(tornado.web.RequestHandler):
    __PAC__ = ('function FindProxyForURL(url, host) {\r\n'
               '  if (dnsDomainIs(host, "ak-gs.hypergryph.com")) {return __PROXY__;}\r\n'
               '  return "DIRECT";\r\n'
               '}')

    def get(self):
        self.set_header("Content-Type", "application/x-ns-proxy-autoconfig")
        proxy_host = socket.gethostbyname(socket.getfqdn())
        proxy_port = mitmproxy.ctx.options.listen_port
        self.write(self.__PAC__.replace('__PROXY__', f'"PROXY {proxy_host}:{proxy_port}"'))


def main():
    app = tornado.web.Application([(r"/pac", ProxyAutoConfig)])
    pac_server = tornado.httpserver.HTTPServer(app)
    pac_server.listen(8081)
    mitmproxy.tools.main.mitmdump(('--quiet', '--scripts', __file__))


if __name__ == '__main__':
    main()
