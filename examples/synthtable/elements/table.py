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
        # table의 구성성분
        # table template
        # simple
        # bg colors: white
        # header colors : [blakc, gray, red, blue, orange, navy]
        # border color
        # border types(probs, switchs) : [nothing, header line, table border, header line+table border, row lines, col lines, only header line(first),  total]
        # dark simple
        # stride

        # random
        # table styles
        # elements
        # table
        # thead
        # tbody
        # row
        # cell

        # border (border-width: )
        # color
        # width(with 0)
        # ( table에 border-collapse: collapse; 적용, td에 전체 border 적용)
        # text
        # color
        # font
        # size
        # text-align
        # vertical-align
        # multi-line
        # font-weight
        # spaces between chars
        # 부분 효과
        # color, font, size, font-weight
        # bg
        # bg color
        # bg gradient
        # bg image
        # padding
        # td에 적용해야 전체 적용됨
        # size
        # width, height
        # margin table
        # round

        self.table_selector = parse_config(config)
        print(self.table_selector)

        # self.static = comps.StaticTable(**{k: config["static"][k] for k in config["static"] if k != 'weight'})
        # self.synth = comps.SynthTable(**{k: config["synth"][k] for k in config["synth"] if k != 'weight'})
        for selector_dict in self.table_selector.components_or_names:
            for k in selector_dict:
                assert k in ['static', 'synth']
                if k == 'static':
                    self.static = comps.StaticTable(selector_dict[k])
                else:
                    self.synth = comps.SynthTable(selector_dict[k])
                break
        # self.static = comps.StaticTable(self.selector)
        # self.synth = comps.SynthTable(**{k: config["synth"][k] for k in config["synth"] if k != 'weight'})

        # weights = [config["static"]["weight"], config["synth"]["weight"]]
        # self.table_selector = Selector(["static", "synth"], weights)

    def generate(self, size, max_size):
        table_layer = TableLayer(size)

        # table_creator = self.table_selector.select()
        table_config = self.table_selector.select()
        try:
            for table_type in table_config:
                if table_type == "static":
                    self.static.apply([table_layer], {'size': size})
                elif table_type == "synth":
                    self.synth.apply([table_layer])
                break
        except:
            traceback.print_exc()
            return self.generate(size, max_size)

        return table_layer
