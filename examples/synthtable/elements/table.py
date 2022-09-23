"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import traceback

import components as comps
from layers import *
from utils.selector import Selector


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
        # border
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
        self.static = comps.StaticTable(**config["static"], common=config["common"])
        self.synth = comps.SynthTable(**config["synth"], common=config["common"])

        weights = [config["static"]["weight"], config["synth"]["weight"]]
        self.table_selector = Selector(["static", "synth"], weights)

        # self.table_component = components.Selector([
        #     # use predefined html file and image file pairs
        #     comps.StaticHtmlAndImage,
        #     # synth htmls and styles
        #     components.Iterator([
        #         # table html
        #         components.Selector([
        #             # html file and change contents switch
        #             components.Iterator([
        #                 comps.TableHtmlFile(),
        #                 components.Switch(
        #                     components.Selector([
        #                         comps.Corpus,
        #                         comps.SynthText,
        #                         comps.KeyValueCorpus,
        #                     ]),
        #                 ),
        #             ]),
        #             # synth table structure and contents html
        #             components.Iterator([
        #                 comps.SynthTableStructureHtml(),
        #                 components.Selector([
        #                     comps.Corpus,
        #                     comps.SynthText,
        #                     comps.KeyValueCorpus,
        #                 ]),
        #             ])
        #         ]),
        #         # table styles
        #         components.Iterator([
        #             # table style selector(table globally)
        #             components.Selector([
        #                 # random synth style
        #                 components.Iterator([
        #                     # table
        #                     #   bg
        #                     #   padding
        #                     # thead
        #                     # tbody
        #                     # tr
        #                     # td
        #                 ]),
        #                 # striped rows
        #                 components.Iterator([
        #                     comps.StrongColor,
        #                     comps.WeakColor,
        #                 ])
        #                 # simple styles
        #             ]),
        #             # tr & th style iterator(tr individually)
        #             components.Switch(
        #                 components.Iterator([
        #                     # bg color
        #                     # border
        #                     # ...
        #                 ]),
        #             ),
        #             # td style iterator(td individually)
        #             components.Switch(
        #                 components.Iterator([
        #                     # bg color
        #                     # border
        #                     # ...
        #                 ]),
        #             )
        #         ])
        #     ])
        # ], **config)

    def generate(self, size, max_size):
        table_layer = TableLayer(size)

        table_creator = self.table_selector.select()
        try:
            if table_creator == "static":
                self.static.apply([table_layer], {'size': size})
            elif table_creator == "synth":
                self.synth.apply([table_layer], {'size': size, 'max_size': max_size})
        except:
            traceback.print_exc()
            return self.generate(size, max_size)

        return table_layer
