import os
import traceback
import json
from synthtiger.components.component import Component
from utils.switch import BoolSwitch
from utils.path_selector import PathSelector
from PIL import Image
from utils.selector import Selector
from elements.paper import Paper
from collections import defaultdict
from utils.switch import BoolSwitch
import numpy as np
from bs4 import BeautifulSoup


def parse_html_style_values_dict(dict_values):
    weights = dict_values['weights'] if 'weights' in dict_values else None
    postfix = dict_values['postfix'] if 'postfix' in dict_values else None
    prob = dict_values['prob'] if 'prob' in dict_values else None

    return dict_values['values'], weights, postfix, prob


def parse_html_style_values(values):
    if isinstance(values, list):
        return Selector(values)
    elif isinstance(values, dict):
        return Selector(*parse_html_style_values_dict(values))


def parse_html_style(config):
    selectors = {}
    for k in config:
        if k == "prob":
            continue
        v = config[k]
        selectors[k] = parse_html_style_values(v)
    return selectors


def make_style_attribute(selectors, tag_name):
    meta = {}
    styles = []
    for css_key in selectors:
        selector = selectors[css_key]
        css_val = selector.select()
        if css_val is None:
            continue
        styles.append("{}: {}".format(css_key, css_val))
        meta['local_{}_{}'.format(tag_name, css_key)] = css_val
    return ";".join(styles)


class SynthTable(Component):
    def __init__(self, html, style, common, **kwargs):
        super().__init__()
        self.html_path_selector = PathSelector(html["paths"], html["weights"], exts=['.json'])

        # styles
        # todo: select parer or other backgrounds
        if 'weight' in style["global"]["background"]["paper"]:
            del style["global"]["background"]["paper"]['weight']
        self.paper = Paper(style["global"]["background"]["paper"])
        self.margin_switch = BoolSwitch(style["global"]["table"]["margin"]["prob"])
        self.margin_selector = Selector(style["global"]["table"]["margin"]["values"])

        self.local_style_switch = BoolSwitch(style["local"]["prob"])
        self.local_css_selectors = {}
        local_css_configs = style["local"]['css']
        for css_selector in local_css_configs:
            prob = local_css_configs[css_selector]['prob']
            self.local_css_selectors[css_selector] = BoolSwitch(prob, parse_html_style(local_css_configs[css_selector]))

        self.relative_style = {}
        for key in style["global"]["relative"]:
            self.relative_style[key] = Selector(style["global"]["relative"][key])

        css_configs = style["global"]['css']
        self.css_selectors = {}
        for css_selector in css_configs:
            self.css_selectors[css_selector] = parse_html_style(css_configs[css_selector])

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

    def sample_global_styles(self):
        # synth style
        global_style = defaultdict(dict)
        global_style['#table_wrapper']["display"] = "inline-block"
        # text styles
        meta = {}
        for css_selector in self.css_selectors:
            for css_key in self.css_selectors[css_selector]:
                selector = self.css_selectors[css_selector][css_key]
                value = selector.select()
                if value is None:
                    continue
                global_style[css_selector][css_key] = value
                meta[css_selector + '_' + css_key] = value

        if self.margin_switch.on():
            margin_left = self.margin_selector.select()
            margin_right = self.margin_selector.select()
            margin_top = self.margin_selector.select()
            margin_bottom = self.margin_selector.select()
            global_style['table']['margin-left'] = str(margin_left) + "px"
            global_style['table']['margin-right'] = str(margin_right) + "px"
            global_style['table']['margin-top'] = str(margin_top) + "px"
            global_style['table']['margin-bottom'] = str(margin_bottom) + "px"
            meta['margin_width'] = margin_left + margin_right
            meta['margin_height'] = margin_top + margin_bottom
        else:
            meta['margin_width'] = 0
            meta['margin_height'] = 0

        return global_style, meta

    def sample_local_styles(self, html):
        meta = {}
        if not self.local_style_switch.on():
            return html, meta

        bs = BeautifulSoup(html, 'html.parser')

        for tr in bs.find_all('tr'):
            if self.local_css_selectors['tr'].on():
                selectors = self.local_css_selectors['tr'].get()
                style_attr, tr_meta = make_style_attribute(selectors, "tr")
                tr['style'] = style_attr
                meta.update(tr_meta)
            for td in tr.find_all("td"):
                if self.local_css_selectors['td'].on():
                    selectors = self.local_css_selectors['td'].get()
                    style_attr, td_meta = make_style_attribute(selectors, "td")
                    td['style'] = style_attr
                    meta.update(td)
        return str(bs), meta

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

        meta['global_style'], global_style_meta = self.sample_global_styles()
        meta.update(global_style_meta)
        meta['html_with_local_style'], local_style_meta = self.sample_local_styles(meta['html'])
        meta.update(local_style_meta)

        relative_style = {}
        for key in self.relative_style:
            relative_style[key] = self.relative_style[key].select()

        meta['relative_style'] = relative_style
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

        # rendering
        for layer in layers:
            layer.plain_html = html
            layer.plain_html_with_styles = meta['html_with_local_style']
            print(layer.plain_html_with_styles)
            layer.global_style = meta['global_style']
            layer.render_table(tmp_path=self.tmp_path, paper=self.paper, meta=meta)
