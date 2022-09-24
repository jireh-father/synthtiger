import os
import traceback
from utils.style import add_styles
import json
from synthtiger.components.component import Component
from utils.switch import BoolSwitch
from utils.path_selector import PathSelector
from PIL import Image
from utils.selector import Selector
from elements.paper import Paper
from collections import defaultdict
from utils import html_style


class SynthTable(Component):
    def __init__(self, html, style, common, **kwargs):
        super().__init__()
        self.html_path_selector = PathSelector(html["paths"], html["weights"], exts=['.json'])

        # styles
        self.paper = Paper(style["global"]["background"]["paper"])

        self.text_style_selectors = html_style.parse_html_style(style["global"]["text"])

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
        global_style = defaultdict(dict)
        global_style['#table_wrapper']["display"] = "inline-block"
        # text styles
        for k in self.text_style_selectors:
            selector = self.text_style_selectors[k]
            value = selector.select()
            global_style['table'][k] = value

        # rendering
        for layer in layers:
            layer.plain_html = html
            layer.plain_html_with_styles = html
            layer.global_style = global_style
            layer.render_table(tmp_path=self.tmp_path, paper=self.paper)
