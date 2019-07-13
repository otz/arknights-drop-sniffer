#!/usr/bin/env python3
"""
DON'T BE EVIL
"""

import json
from datetime import datetime
from pathlib import Path

from aadict import aadict
from mitmproxy.http import HTTPFlow
from mitmproxy.tools.main import mitmdump


class _ArknightsGameData:
    """
    References: Perfare's ArknightsGameData
    https://github.com/Perfare/ArknightsGameData
    """

    def __init__(self, repo='ArknightsGameData'):
        self._repo = Path(repo)
        self._databases = {}

    def database(self, name):
        if name not in self._databases:
            _path = self._repo.joinpath(name).with_suffix('.json')
            with open(_path, encoding='utf-8') as _fp:
                self._databases[name] = aadict.d2ar(json.load(_fp))
        return self._databases[name]

    @property
    def items(self):
        return self.database('excel/item_table')['items']

    @property
    def furnitures(self):
        return self.database('excel/building_data')['customData']['furnitures']

    @property
    def characters(self):
        return self.database('excel/character_table')

    @property
    def stages(self):
        return self.database('excel/stage_table')['stages']

    def get_name(self, _type, _id):
        if _type == 'FURN':
            return self.furnitures[_id]['name']
        if _type == 'CHAR':
            return self.characters[_id]['name']
        return self.items[_id]['name']


ark = _ArknightsGameData()


def _battle_rewards(rewards):
    return [f'{ark.get_name(_drop.type, _drop.id)},{_drop.count}' for _drop in rewards if _drop.count > 0]


def _battle_finish(text):
    response = aadict.d2ar(json.loads(text))
    stages = list(response.playerDataDelta.modified.dungeon.stages.values())
    assert len(stages) == 1
    now = datetime.now().isoformat(timespec='seconds')
    rewards = _battle_rewards(response.rewards)
    rewards += _battle_rewards(response.unusualRewards)
    rewards += _battle_rewards(response.additionalRewards)
    rewards += _battle_rewards(response.furnitureRewards)
    rewards = ','.join(rewards)
    rewards = (f'{now},'
               f'{ark.stages[stages[0].stageId].code},'
               f'{stages[0].completeTimes},'
               f'{rewards}')
    with open('battle_drops.txt', 'a', encoding='utf-8') as _fp:
        _fp.write(f'{rewards}\n')
    print(f'PRTS: {rewards}')


class PRTS:
    @staticmethod
    def response(flow: HTTPFlow):
        if flow.request.host == 'ak-gs.hypergryph.com':
            if flow.request.path == '/quest/battleFinish':
                try:
                    _battle_finish(flow.response.text)
                except AttributeError:
                    pass


addons = [PRTS()]

if __name__ == '__main__':
    def main():
        mitmdump(('--quiet', '--scripts', __file__))


    main()
