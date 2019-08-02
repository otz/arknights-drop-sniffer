"""
logging battle drops.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from aadict import aadict

logger = logging.getLogger(__name__)


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


_ARK = _ArknightsGameData()


def battle_drops(response, stage_id):
    if _ARK.stages[stage_id].apCost - _ARK.stages[stage_id].apFailReturn != 1:
        logger.debug(f'skip stage: {stage_id}')
        return

    now = datetime.now().isoformat(timespec='seconds')
    code = _ARK.stages[stage_id].code
    complete_times = response.playerDataDelta.modified.dungeon.stages[stage_id].completeTimes
    drops = defaultdict(int)
    for rewards in (response.rewards,
                    response.unusualRewards,
                    response.additionalRewards,
                    response.furnitureRewards):
        for _drop in rewards:
            if _drop.count > 0:
                name = _ARK.get_name(_drop.type, _drop.id)
                drops[name] += _drop.count
    drops = ','.join(f'{name},{count}' for name, count in drops.items())
    record = f'{now},{code},{complete_times},{drops}'
    with open('battle_drops.txt', 'a', encoding='utf-8') as _fp:
        _fp.write(f'{record}\n')
    logger.info(f'{record}')
