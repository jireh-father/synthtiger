"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import traceback

import components as comps
from layers import *
from utils.selector import Selector, parse_config


class Table():
    def __init__(self, config):
        self.table_selector = parse_config(config)

        for selector_dict in self.table_selector.values:
            for k in selector_dict:
                assert k in ['static', 'synth']
                if k == 'static':
                    self.static = comps.StaticTable(selector_dict[k])
                else:
                    self.synth = comps.SynthTable(selector_dict[k])
                break

    def generate(self, size, max_size):
        table_layer = TableLayer(size)

        table_config = self.table_selector.select()
        try:
            for table_type in table_config:
                if table_type == "static":
                    self.static.apply([table_layer], {'size': size})
                elif table_type == "synth":
                    self.synth.apply([table_layer])
                table_layer.meta['table_type'] = table_type
                break
        except:
            traceback.print_exc()
            return self.generate(size, max_size)

        return table_layer
