import os
import traceback
import json
from synthtiger.components.component import Component
from utils.switch import BoolSwitch
from utils.path_selector import PathSelector
from PIL import Image
from utils import image_util
from elements.paper import Paper

class SynthTable(Component):
    def __init__(self, html, style, common, **kwargs):
        super().__init__()
        self.html_path_selector = PathSelector(html["paths"], html["weights"], exts=['.json'])

        self.style = style

        self.paper = Paper(style["global"]["background"]["paper"])

        self.synth_structure_prob = BoolSwitch(html['synth_structure_prob'])
        self.synth_content_prob = BoolSwitch(html['synth_content_prob'])

        self.min_rows = common['rows'][0]
        self.max_rows = common['rows'][1]
        self.min_cols = common['cols'][0]
        self.max_cols = common['cols'][1]
        self.has_span = BoolSwitch(common['has_span'])
        self.has_col_span = BoolSwitch(common['has_col_span'])
        self.has_row_span = BoolSwitch(common['has_row_span'])
        self.tmp_path = common['tmp_path']
        os.makedirs(self.tmp_path, exist_ok=True)

    def sample(self, meta=None):
        if meta is None:
            meta = {}
        synth_structure = self.synth_structure_prob.on()
        synth_content = self.synth_content_prob.on()
        if synth_structure:
            pass
        else:
            html_path, html_json = self._sample_html_path()
            meta['html_path'] = html_path
            meta['html'] = html_json['html']
            meta['html_json'] = html_json
            meta['nums_col'] = html_json['nums_col']
            meta['nums_row'] = html_json['nums_row']
        meta['synth_structure'] = synth_structure
        meta['synth_content'] = synth_content

        return meta

    def _sample_html_path(self):
        while True:
            html_json_path, _, _ = self.html_path_selector.select()
            html_json = json.load(open(html_json_path), encoding='utf-8')
            if self.min_cols > html_json['nums_col'] or self.max_cols < html_json['nums_col']:
                continue
            if self.min_rows > html_json['nums_row'] or self.max_rows < html_json['nums_row']:
                continue
            has_span = self.has_span.on()
            if has_span != html_json['has_span']:
                continue

            if has_span:
                if self.has_row_span.on() and not html_json['has_row_span']:
                    continue
                if self.has_col_span.on() and not html_json['has_col_span']:
                    continue

            return html_json_path, html_json

    def apply(self, layers, meta=None):
        target_size = meta['size']
        max_size = meta['max_size']

        meta = self.sample(meta)
        if meta['synth_structure']:
            # meta['nums_col'] = html_json['nums_col']
            # meta['nums_row'] = html_json['nums_row']
            pass
        else:
            html = meta['html']


        if meta['synth_content']:
            pass
        else:
            pass

        # synth style
        # todo: font_size를 col, row갯수와 target_size 에 맞게 조절
        # todo: 글자 큰거 한글자당 font_size 대비 셀의 높이와 너비 계산
        # meta['nums_col']
        # meta['nums_row']

        # rendering
        for layer in layers:
            layer.plain_html = html
            layer.plain_html_with_styles = html
            layer.global_style = {
                # "#table_wrapper":{
                #     "width"
                # }
                "table": {
                    "width": str(target_size[0]) + "px",
                    "height": str(target_size[1]) + "px",
                },
                "#table_wrapper": {
                    "display": "inline-block"
                }

            }
            layer.render_table(tmp_path=self.tmp_path, size=target_size, paper=self.paper, max_size=max_size)
