import os
import traceback
import math
import json
import uuid
import numpy
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
import re
from utils import html_util
from synthtiger import components
import components as comps
import random
from utils.html_util import remove_tags
from utils.charset import Charset
from html import unescape


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
    else:
        return Selector(values)


def convert_bs_to_html_string(bs):
    if "<" in bs.text or ">" in bs.text:
        html = str(bs)
        return unescape(html)
    else:
        return str(bs)


def parse_html_style(config):
    selectors = {}
    for k in config:
        if k == "prob":
            continue
        v = config[k]
        selectors[k] = parse_html_style_values(v)
    return selectors


class SynthTable(Component):
    def __init__(self, config_selectors, config):
        super().__init__()
        self.config = config
        self.config_selectors = config_selectors
        self.html_path_selector = PathSelector(config_selectors['html']['paths'].values,
                                               config_selectors['html']['weights'].values, exts=['.json'])

        self.html_charset = None
        if 'charset' in config_selectors['html']:
            self.html_charset = Charset(config_selectors['html']['charset'])

        # styles
        for background_config in config_selectors['style']['global']['absolute']['background'].values:
            name = background_config['name']

            if name == 'paper':
                paper_config = config["style"]["global"]["absolute"]["background"]["paper"]
                self.paper = Paper({k: paper_config[k] for k in paper_config if k != "weight"})
            elif name == 'gradient':
                self.gradient_bg = background_config['config']
            elif name == 'striped':
                self.striped_bg = background_config['config']

        # color set
        self.dark_colors = config_selectors['style']['color_set']['dark']
        self.light_colors = config_selectors['style']['color_set']['light']
        self.global_color_mode = config_selectors['style']['global']['absolute']['table']['color_mode']

        # global absolute thead
        self.absolute_style = defaultdict(dict)

        # common styles
        self.min_rows = config_selectors['html']['min_row'].select()
        self.max_rows = config_selectors['html']['max_row'].select()
        self.min_cols = config_selectors['html']['min_col'].select()
        self.max_cols = config_selectors['html']['max_row'].select()

        self.has_span = config_selectors['html']['has_span']
        self.has_col_span = config_selectors['html']['has_col_span']
        self.has_row_span = config_selectors['html']['has_row_span']
        tmp_path = config_selectors['html']['tmp_path'].select()
        os.makedirs(tmp_path, exist_ok=True)

        self.font = components.BaseFont(**config["style"].get("font", {}))

        if config["html"]["structure"]["synth_structure"]["weight"] > 0 or config["html"]["synth_content"]["prob"] > 0:
            self.synth_structure_config = None
            corpus_dict = defaultdict(dict)
            for thead_or_tbody in ["thead", "tbody"]:
                for corpus_type in config["html"]["synth_content"]["corpus"][thead_or_tbody].keys():
                    corpus_config = config["html"]["synth_content"]["corpus"][thead_or_tbody][corpus_type]
                    if corpus_type == "length_augmentable":
                        corpus = components.LengthAugmentableCorpus(
                            **{k: corpus_config[k] for k in corpus_config if k != "weight"})
                    elif corpus_type == "char_augmentable":
                        corpus = self.thead_char_aug_corpus = components.CharAugmentableCorpus(
                            **{k: corpus_config[k] for k in corpus_config if k != "weight"})
                    elif corpus_type == "base":
                        corpus = components.BaseCorpus(
                            **{k: corpus_config[k] for k in corpus_config if k != "weight"})
                    corpus_dict[thead_or_tbody][corpus_type] = corpus
            self.corpus_dict = corpus_dict

            self.thead_corpus_selector = config_selectors['html']['synth_content'].get()['corpus']['thead']
            self.tbody_corpus_selector = config_selectors['html']['synth_content'].get()['corpus']['tbody']
            self.empty_cell_switch = config_selectors['html']['synth_content'].get()['empty_cell']
            self.thead_bold_switch = config_selectors['html']['synth_content'].get()['thead_bold']
            self.synth_cell_switch = config_selectors['html']['synth_content'].get()['synth_cell']
            self.shuffle_cells_switch = config_selectors['html']['synth_content'].get()['shuffle_cells']
            self.shuffle_cells_portion_selector = \
                config_selectors['html']['synth_content'].get()['shuffle_cells'].get()["portion"]
            self.mix_thead_tbody_switch = config_selectors['html']['synth_content'].get()['corpus']['mix_thead_tbody']

    def _sample_cell_text(self, thead_or_tbody='tbody', mix_thead_tbody=False):
        if mix_thead_tbody:
            thead_or_tbody = ["tbody", "thead"][np.random.randint(0, 2)]
        corpus_type = self.thead_corpus_selector.select()['name']
        corpus = self.corpus_dict[thead_or_tbody][corpus_type]
        return corpus.sample()['text']

    def _sample_global_color_mode(self):
        return self.global_color_mode.select()

    def _sample_dark_color(self):
        return self.dark_colors.select()

    def _sample_light_color(self):
        return self.light_colors.select()

    def _sample_background(self, global_style, meta):
        # background
        background_config = self.config_selectors['style']['global']['absolute']['background'].select()
        meta['background_config'] = background_config['name']

        color_mode = meta['color_mode']

        if meta['background_config'] == 'paper':
            meta['color_mode'] = "light"
            global_style["table"]["color"] = self._sample_dark_color()
        elif meta['background_config'] == 'gradient':
            gradient_type = self.gradient_bg['type'].select()
            angle = self.gradient_bg['angle'].select()
            num_colors = self.gradient_bg['num_colors'].select()
            # use_random_stop_position = self.gradient_bg['use_random_stop_position'].on()

            gd_colors = []
            for i in range(num_colors):
                if color_mode == "dark":
                    gd_color = self._sample_dark_color()
                else:
                    gd_color = self._sample_light_color()
                gd_colors.append(gd_color)

            global_style["#table_wrapper"]["background"] = "{}-gradient({}deg, {})".format(gradient_type, angle,
                                                                                           ", ".join(gd_colors))
            if color_mode == "dark":
                global_style["table"]["color"] = self._sample_light_color()
            else:
                global_style["table"]["color"] = self._sample_dark_color()
        elif meta['background_config'] == 'empty':
            if color_mode == "dark":
                global_style["#table_wrapper"]["background-color"] = 'black'
                global_style["table"]["color"] = 'white'
            else:
                global_style["#table_wrapper"]["background-color"] = 'white'
                global_style["table"]["color"] = 'black'
        elif meta['background_config'] == 'solid':
            if color_mode == "dark":
                global_style["#table_wrapper"]["background-color"] = self._sample_dark_color()
                global_style["table"]["color"] = self._sample_light_color()
            else:
                global_style["#table_wrapper"]["background-color"] = self._sample_light_color()
                global_style["table"]["color"] = self._sample_dark_color()
        elif meta['background_config'] == 'striped':
            dark_line = self.striped_bg['dark_line'].select()
            light_line = "even" if dark_line == "odd" else "odd"
            dark_color = self._sample_dark_color()
            light_color = self._sample_light_color()
            global_style["tbody tr:nth-child({})".format(dark_line)]["background-color"] = dark_color
            global_style["tbody tr:nth-child({})".format(dark_line)]["color"] = light_color
            global_style["tbody tr:nth-child({})".format(light_line)]["background-color"] = light_color
            global_style["tbody tr:nth-child({})".format(light_line)]["color"] = dark_color
        elif meta['background_config'] == 'striped_all_dark':
            if color_mode == "dark":
                bg_color_odd = self._sample_dark_color()
                bg_color_even = self._sample_dark_color()
                font_color = self._sample_light_color()
            else:
                bg_color_odd = self._sample_light_color()
                bg_color_even = self._sample_light_color()
                font_color = self._sample_dark_color()
            global_style["tbody tr:nth-child(odd)"]["background-color"] = bg_color_odd
            global_style["tbody tr:nth-child(even)"]["background-color"] = bg_color_even
            global_style["table"]["color"] = font_color
        elif meta['background_config'] == 'multi_color':
            dark_color = self._sample_dark_color()
            light_color = self._sample_light_color()
            for i in range(meta['nums_row'] - 1):
                if color_mode == "dark":
                    global_style["tbody tr:nth-child({})".format(i + 1)][
                        "background-color"] = self._sample_dark_color()
                    global_style["tbody tr:nth-child({})".format(i + 1)]["color"] = light_color
                else:
                    global_style["tbody tr:nth-child({})".format(i + 1)][
                        "background-color"] = self._sample_light_color()
                    global_style["tbody tr:nth-child({})".format(i + 1)]["color"] = dark_color

    def _sample_border(self, global_style, meta):
        border_config = self.config_selectors['style']['global']['absolute']['border'].select()
        border_type = border_config['name']
        meta['border_config'] = border_type
        border_css = border_config['config']

        self._set_css_to_global_style(border_css, global_style, meta)

        color_mode = meta['color_mode']
        if color_mode == "dark":
            border_color = self._sample_light_color()
        else:
            border_color = self._sample_dark_color()

        if border_type == 'inside':
            global_style["td"]["border-color"] = border_color
        elif border_type == 'all':
            global_style["td"]["border-color"] = border_color
        elif border_type == 'row':
            global_style["tr"]["border-bottom-color"] = border_color
        elif border_type == 'col':
            global_style["td"]["border-right-color"] = border_color
        elif border_type == 'outline':
            global_style["table"]["border-color"] = border_color

    def _sample_thead(self, global_style, meta):
        if meta['background_config'] != 'paper':
            color_mode = self.config_selectors['style']['global']['absolute']['thead']['color_mode'].select()
            meta['thead_color_mode'] = color_mode
            light_color = self._sample_light_color()
            dark_color = self._sample_dark_color()

            if color_mode == "dark":
                global_style['thead tr']['background-color'] = dark_color
                global_style['thead tr']['color'] = light_color
            else:
                global_style['thead tr']['background-color'] = light_color
                global_style['thead tr']['color'] = dark_color
        else:
            meta['thead_color_mode'] = 'light'
            global_style['thead tr']['color'] = self._sample_dark_color()

        font_size_scale = self.config_selectors['style']['global']['relative']['thead']['font_size'].select()

        head_font_size = int(round(float(global_style['table']['font-size'].split("px")[0]) * font_size_scale))
        global_style['thead tr']['font-size'] = str(head_font_size) + "px"

        if self.config_selectors['style']['global']['absolute']['thead']['font'].on():
            self._sample_font(global_style, meta, 'thead tr')

    def _sample_table_outline(self, global_style, meta):
        if meta['background_config'] != 'paper':
            color_mode = meta['color_mode']
        else:
            color_mode = 'light'
        thead_color_mode = meta['thead_color_mode']
        border_type = self.config_selectors['style']['global']['absolute']['table_outline']['border_type'].select()

        border_width = self.config_selectors['style']['global']['absolute']['table_outline']['border_width'].select()

        if border_type == "empty":
            thead_border_type = self.config_selectors['style']['global']['absolute']['table_outline'][
                'empty_thead_border_type'].select()
            if thead_color_mode == "dark":
                border_color = self._sample_light_color()
            else:
                border_color = self._sample_dark_color()
            if thead_border_type == "all":
                global_style['thead']['border'] = "{}px solid {}".format(border_width, border_color)
            elif thead_border_type == "top_bottom":
                global_style['thead']['border-top'] = "{}px solid {}".format(border_width, border_color)
                global_style['thead']['border-bottom'] = "{}px solid {}".format(border_width, border_color)
            elif thead_border_type == "bottom":
                global_style['thead']['border-bottom'] = "{}px solid {}".format(border_width, border_color)
        else:
            thead_border_type = self.config_selectors['style']['global']['absolute']['table_outline'][
                'etc_thead_border_type'].select()
            if color_mode == "dark":
                border_color = self._sample_light_color()
            else:
                border_color = self._sample_dark_color()
            if border_type == "all":
                global_style['table']['border'] = "{}px solid {}".format(border_width, border_color)
            elif border_type == "top_bottom":
                global_style['table']['border-top'] = "{}px solid {}".format(border_width, border_color)
                global_style['table']['border-bottom'] = "{}px solid {}".format(border_width, border_color)
            elif border_type == "left_right":
                global_style['table']['border-left'] = "{}px solid {}".format(border_width, border_color)
                global_style['table']['border-right'] = "{}px solid {}".format(border_width, border_color)
            if thead_border_type == "bottom":
                global_style['thead']['border-bottom'] = "{}px solid {}".format(border_width, border_color)

            if self.config_selectors['style']['global']['absolute']['table_outline']['round'].on():
                round_config = self.config_selectors['style']['global']['absolute']['table_outline']['round'].get()
                global_style['table']['border-collapse'] = round_config['border-collapse'].select()
                global_style['table']['border-radius'] = round_config['border-radius'].select()
                meta['table_outline_round'] = True
                meta['table_outline_radius'] = global_style['table']['border-radius']
        meta['table_border_type'] = border_type
        meta['table_border_width'] = border_width
        meta['thead_border_type'] = thead_border_type

    def _sample_font(self, global_style, meta, selector):
        font_path = os.path.abspath(self.font.sample()["path"])
        font_family = str(uuid.uuid4())
        font_face = {
            'font-family': font_family,
            'src': 'url("{}") format("truetype")'.format(font_path),
            'font-weight': 'normal'
        }
        if '@font-face' not in global_style:
            global_style['@font-face'] = []
        global_style['@font-face'].append(font_face)
        global_style[selector]['font-family'] = font_face['font-family']
        meta['{}_font'.format(selector)] = font_face['src']

    def sample_styles(self, meta):
        # static style
        global_style = defaultdict(dict)
        global_style['#table_wrapper']["display"] = "inline-block"
        global_style['table']["border-collapse"] = "collapse"

        # absolutes
        meta['color_mode'] = self._sample_global_color_mode()

        # font
        self._sample_font(global_style, meta, 'table')

        # css
        css_selectors = self.config_selectors['style']['global']['css']
        self._set_css_to_global_style(css_selectors, global_style, meta)

        self._sample_background(global_style, meta)

        self._sample_thead(global_style, meta)

        self._sample_table_outline(global_style, meta)

        self._sample_border(global_style, meta)

        # local style
        self.sample_local_styles(global_style, meta)

        return global_style

    def _set_css_to_global_style(self, css_selectors, global_style, meta):
        for css_selector in css_selectors:
            for css_key in css_selectors[css_selector]:
                selector = css_selectors[css_selector][css_key]
                value = selector.select()
                if value is None:
                    continue
                global_style[css_selector][css_key] = value

    def _set_text_style(self, bs, bs_element, text, global_style, meta, text_config, color_mode):
        local_config = self.config_selectors['style']['local'].get()
        text_id = str(uuid.uuid4())
        span_tag = bs.new_tag("span", id="text_{}".format(text_id))
        span_tag.append(text)
        bs_element.append(span_tag)
        selectors = local_config['css']['td'].get()
        global_style_key = "#text_{}".format(text_id)
        for css_selector in selectors:
            if css_selector.startswith("border"):
                continue
            css_val = selectors[css_selector]
            val = css_val.select()
            if val is None:
                continue
            global_style[global_style_key][css_selector] = val

        use_bg = text_config['config']['background_color'].on()
        # color
        if color_mode == "dark":
            global_style[global_style_key]['color'] = self._sample_light_color()
            if use_bg and meta['background_config'] != 'paper':
                global_style[global_style_key]['background-color'] = self._sample_dark_color()
        else:
            global_style[global_style_key]['color'] = self._sample_dark_color()
            if use_bg and meta['background_config'] != 'paper':
                global_style[global_style_key]['background-color'] = self._sample_light_color()

        # font
        if local_config['absolute']['td']['font'].on():
            self._sample_font(global_style, meta, global_style_key)

        # font-size
        if local_config['relative']['td'].on():
            font_size_scale = local_config['relative']['td'].get()['font_size'].select()
            font_size = int(
                round(float(global_style['table']['font-size'].split("px")[0]) * font_size_scale))
            global_style[global_style_key]['font-size'] = str(font_size) + "px"

    def _set_local_text_styles(self, global_style, meta, bs_element, color_mode):
        local_config = self.config_selectors['style']['local'].get()
        text_config = local_config['absolute']['text'].get().select()
        word_or_char = text_config['name']
        bs = meta['html_bs']
        text = remove_tags("".join([str(tag) for tag in bs_element.contents])).strip()
        bs_element.clear()

        if color_mode is None:
            color_mode = local_config['absolute']['td']['color_mode'].select()
        if word_or_char == 'word':
            words = text.split(" ")
            change_word_ratio = text_config['config']['words'].select()
            change_word_cnt = math.ceil(len(words) * change_word_ratio)
            if change_word_cnt > len(words):
                change_word_cnt = len(words)
            change_word_indexes = random.sample(list(range(len(words))), change_word_cnt)
            for i, word in enumerate(words):
                if i > 0:
                    bs_element.append(" ")
                if i in change_word_indexes:
                    self._set_text_style(bs, bs_element, word, global_style, meta, text_config, color_mode)
                else:
                    bs_element.append(word)
                if i < len(words):
                    bs_element.append(" ")
        elif word_or_char == "char":
            char_length_ratio = text_config['config']['length'].select()
            char_length = math.ceil(len(text) * char_length_ratio)
            if char_length > len(text):
                char_length = len(text)
            start_idx = np.random.randint(0, len(text) - char_length + 1)
            if start_idx > 0:
                bs_element.append(text[:start_idx])
            self._set_text_style(bs, bs_element, text[start_idx:start_idx + char_length], global_style, meta,
                                 text_config, color_mode)
            if start_idx + char_length < len(text):
                bs_element.append(text[start_idx + char_length:])

    def _set_local_css_styles(self, global_style, config_key, css_selector_name, meta, bs_element=None):
        local_config = self.config_selectors['style']['local'].get()
        use_absolute = config_key in local_config['absolute']
        use_relative = config_key in local_config['relative']

        color_mode = None
        if local_config['css'][config_key].on():
            if use_absolute:
                color_mode = local_config['absolute'][config_key]['color_mode'].select()
                use_font = local_config['absolute'][config_key]['font'].on()
                if config_key == "td":
                    use_text_vertical = local_config['absolute'][config_key]['text_vertical'].on()
                    if use_text_vertical:
                        max_text_length = local_config['absolute'][config_key]['text_vertical'].get()[
                            "max_text_length"].select()
                        if len(bs_element.text) > max_text_length:
                            use_text_vertical = False
                    if use_text_vertical:
                        ignore_number = local_config['absolute'][config_key]['text_vertical'].get()[
                            "ignore_number"].select()
                        if ignore_number and any(c.isdigit() for c in bs_element.text):
                            use_text_vertical = False
            font_size_scale = None
            if use_relative and local_config['relative'][config_key].on():
                font_size_scale = local_config['relative'][config_key].get()['font_size'].select()

            selectors = local_config['css'][config_key].get()
            for css_selector in selectors:
                css_val = selectors[css_selector]
                val = css_val.select()
                if val is None:
                    continue
                global_style[css_selector_name][css_selector] = val
                if font_size_scale:
                    font_size = int(round(float(global_style['table']['font-size'].split("px")[0]) * font_size_scale))
                    global_style[css_selector_name]['font-size'] = str(font_size) + "px"
                    meta[css_selector_name + "_font_size_scale"] = font_size_scale
                    meta[css_selector_name + "_font_size"] = font_size
                if use_absolute:
                    if use_font:
                        self._sample_font(global_style, meta, css_selector_name)
                    if config_key == "td" and use_text_vertical:
                        global_style[css_selector_name]['text-orientation'] = 'upright'
                        global_style[css_selector_name]['writing-mode'] = 'vertical-rl'
                    meta[css_selector_name + "_color_mode"] = color_mode
                    if color_mode == "dark":
                        global_style[css_selector_name]['color'] = self._sample_light_color()
                        if meta['background_config'] != 'paper':
                            global_style[css_selector_name]['background-color'] = self._sample_dark_color()
                        border_color = self._sample_light_color()
                        global_style[css_selector_name]['border-color'] = border_color
                        global_style[css_selector_name]['border-top-color'] = border_color
                        global_style[css_selector_name]['border-left-color'] = border_color
                        global_style[css_selector_name]['border-right-color'] = border_color
                        global_style[css_selector_name]['border-bottom-color'] = border_color
                    else:
                        global_style[css_selector_name]['color'] = self._sample_dark_color()
                        if meta['background_config'] != 'paper':
                            global_style[css_selector_name]['background-color'] = self._sample_light_color()
                        border_color = self._sample_dark_color()
                        global_style[css_selector_name]['border-color'] = border_color
                        global_style[css_selector_name]['border-top-color'] = border_color
                        global_style[css_selector_name]['border-left-color'] = border_color
                        global_style[css_selector_name]['border-right-color'] = border_color
                        global_style[css_selector_name]['border-bottom-color'] = border_color

        if config_key == "td" and local_config['absolute']['text'].on():
            self._set_local_text_styles(global_style, meta, bs_element, color_mode)

    def sample_local_styles(self, global_style, meta):
        if not self.config_selectors['style']['local'].on():
            return

        self._set_local_css_styles(global_style, 'thead', 'thead', meta)
        self._set_local_css_styles(global_style, 'tbody', 'tbody', meta)

        if 'html_bs' not in meta:
            meta['html_bs'] = BeautifulSoup(meta['html'], 'html.parser')
        for row_idx, tr_tag in enumerate(meta['html_bs'].find_all("tr")):
            # for row_idx in range(1, meta['nums_row'] + 1):
            self._set_local_css_styles(global_style, 'tr', "tr:nth-child({})".format(row_idx + 1), meta, tr_tag)
            for col_idx, td_tag in enumerate(tr_tag.find_all("td")):
                # for col_idx in range(1, meta['nums_col'] + 1):
                self._set_local_css_styles(global_style, 'td',
                                           "tr:nth-child({}) td:nth-child({})".format(row_idx + 1, col_idx + 1), meta,
                                           td_tag)

        meta['html'] = convert_bs_to_html_string(meta['html_bs'])

    def sample(self, meta=None):
        if meta is None:
            meta = {}
        structure_config = self.config_selectors['html']['structure'].select()
        synth_structure = structure_config['name'] == 'synth_structure'
        synth_content = self.config_selectors['html']['synth_content'].on()

        if synth_structure:
            synth_structure_config = structure_config['config']
            self.synth_structure_config = synth_structure_config
            meta['nums_row'] = synth_structure_config['nums_row'].select()
            meta['nums_col'] = synth_structure_config['nums_col'].select()

            meta['span'] = synth_structure_config['span'].on()
            meta['add_thead'] = synth_structure_config['thead'].on()
            if meta['add_thead']:
                meta['thead_rows'] = synth_structure_config['thead'].get()['rows'].select()
            meta['mix_thead_tbody'] = self.mix_thead_tbody_switch.on()
            self._synth_structure_and_content(meta)
        else:
            html_path, html_json = self._sample_html_path(meta)
            meta['html_path'] = html_path
            html = html_json['html'].strip()
            # insert tbody
            html = html_util.insert_tbody_tag(html)
            meta['html'] = html
            meta['original_html'] = html
            meta['nums_col'] = html_json['nums_col']
            meta['nums_row'] = html_json['nums_row']
        meta['structure_type'] = structure_config['name']
        meta['synth_content'] = False if synth_structure else synth_content

        if meta['synth_content']:
            meta['shuffle_cells'] = self.shuffle_cells_switch.on()
            meta['mix_thead_tbody'] = self.mix_thead_tbody_switch.on()
            self._synth_content(meta)

        # global absolute and css styles
        meta['global_style'] = self.sample_styles(meta)

        # if 'html_bs' in meta:
        #     meta['html'] = str(meta['html_bs'])

        # global relative styles
        relative_style = defaultdict(dict)
        relative_style_config = self.config_selectors['style']['global']['relative']
        for selector in relative_style_config:
            for key in relative_style_config[selector]:
                relative_style[selector][key] = relative_style_config[selector][key].select()

        meta['relative_style'] = relative_style

        meta['tmp_path'] = self.config_selectors['html']['tmp_path'].select()
        meta['aspect_ratio'] = self.config["style"]["aspect_ratio"]

        return meta

    def _sample_html_path(self, meta):
        while True:
            html_json_path, _, _ = self.html_path_selector.select()

            html_json = json.load(open(html_json_path), encoding='utf-8')
            if self.html_charset:
                bs = BeautifulSoup(html_json['html'], 'html.parser')
                meta['html_bs'] = bs
                if not self.html_charset.check_charset(bs.text):
                    continue
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

    def _synth_structure_and_content(self, meta):
        if meta['span']:
            span_table = np.full((meta['nums_row'], meta['nums_col']), False)

        tags = ["<table>"]
        add_thead = meta['add_thead']
        if add_thead:
            thead_rows = meta['thead_rows']
        for row in range(meta['nums_row']):
            if add_thead:
                if row == 0:
                    tags.append("<thead>")
                elif row == thead_rows:
                    tags.append("<tbody>")
                is_head = row < thead_rows
            else:
                if row == 0:
                    tags.append("<tbody>")
                is_head = False
            tags.append("<tr>")
            for col in range(meta['nums_col']):
                if meta['span']:
                    if span_table[row][col]:
                        continue
                    spans = []
                    if self.synth_structure_config['span'].get()['row_span'].on():
                        if is_head:
                            max_row_span = thead_rows - row
                        else:
                            max_row_span = meta['nums_row'] - row

                        if max_row_span > 1:
                            row_span = np.random.randint(2, max_row_span + 1)
                            spans.append(' rowspan="{}"'.format(row_span))
                            span_table[row:row + row_span, col] = True
                    if self.synth_structure_config['span'].get()['col_span'].on():
                        max_col_span = meta['nums_col'] - col
                        if max_col_span > 1:
                            col_span = np.random.randint(2, max_col_span + 1)
                            spans.append(' colspan="{}"'.format(col_span))
                            span_table[row, col:col + col_span] = True
                    span_attr = "".join(spans)
                    tags.append("<td{}>".format(span_attr))
                else:
                    tags.append("<td>")
                if not self.empty_cell_switch.on():
                    tags.append(self._sample_cell_text("thead" if is_head else "tbody", meta['mix_thead_tbody']))
                tags.append("</td>")
            tags.append("</tr>")
            if add_thead and thead_rows == row + 1:
                tags.append("</thead>")
            if row == meta['nums_row'] - 1:
                tags.append("</tbody>")
        tags.append("</table>")
        meta['html'] = "".join(tags)

    def _swap_cells(self, bs, first_td_tag, second_td_tag, bold=False, meta={}, idx=None):
        first_text = "".join([str(tag) for tag in first_td_tag.contents])
        second_text = "".join([str(tag) for tag in second_td_tag.contents])
        first_text = remove_tags(first_text).strip()
        second_text = remove_tags(second_text).strip()
        meta["swap_cell_{}".format(idx)] = {
            "first_text": first_text,
            "second_text": second_text,
        }
        if bold:
            first_btag = bs.new_tag("b")
            first_btag.string = first_text
            second_btag = bs.new_tag("b")
            second_btag.string = second_text
            first_td_tag.clear()
            second_td_tag.clear()
            first_td_tag.append(second_btag)
            second_td_tag.append(first_btag)
        else:
            first_td_tag.string = second_text
            second_td_tag.string = first_text

    def _shuffle_cells(self, bs, element, meta, is_thead=False):
        td_tags = element.find_all("td")
        swap_cnt = math.ceil(len(td_tags) * self.shuffle_cells_portion_selector.select())
        if swap_cnt % 2 != 0:
            swap_cnt += 1
        if len(td_tags) < swap_cnt:
            swap_cnt -= 2
        if swap_cnt < 1:
            return

        shuffle_td_tags = random.sample(td_tags, swap_cnt)

        if is_thead:
            is_bold = self.thead_bold_switch.on()
            meta['shuffle_thead_is_bold'] = is_bold
            meta['shuffle_thead_swap_cnt'] = swap_cnt
        else:
            is_bold = False
            meta['shuffle_swap_cnt'] = swap_cnt
        for i in range(0, len(shuffle_td_tags), 2):
            self._swap_cells(bs, shuffle_td_tags[i], shuffle_td_tags[i + 1], is_bold, meta,
                             ("thead" if is_thead else "") + str(i))

    def _synth_content(self, meta):
        if 'html_bs' not in meta:
            bs = BeautifulSoup(meta['html'], 'html.parser')
            meta['html_bs'] = bs
        if meta['shuffle_cells']:
            if meta['mix_thead_tbody']:
                self._shuffle_cells(bs, bs, meta)
            else:
                thead_element = bs.find("thead")
                if thead_element:
                    self._shuffle_cells(bs, thead_element, meta, True)

                tbody_element = bs.find("tbody")
                if tbody_element:
                    self._shuffle_cells(bs, tbody_element, meta)
        else:
            thead_bold = self.thead_bold_switch.on()
            meta['synth_content_thead_bold'] = thead_bold
            for thead_or_tbody in ["thead", "tbody"]:
                if not thead_or_tbody:
                    continue
                thead_or_tbody_tag = bs.find(thead_or_tbody)
                for td in thead_or_tbody_tag.find_all("td"):
                    if self.synth_cell_switch.on():
                        if self.empty_cell_switch.on():
                            td.string = ""
                        else:
                            cell_text = self._sample_cell_text(thead_or_tbody, meta['mix_thead_tbody'])
                            if thead_or_tbody == "thead" and thead_bold:
                                btag = bs.new_tag("b")
                                btag.string = cell_text
                                td.clear()
                                td.append(btag)
                            else:
                                td.string = cell_text
        meta['html'] = convert_bs_to_html_string(bs)

    def apply(self, layers, meta=None):
        meta = self.sample(meta)

        if meta['background_config'] == 'paper':
            paper = self.paper
            meta['global_style']["table"]["color"] = self._sample_dark_color()
        else:
            paper = None

        meta["effect_config"] = self.config['effect']
        for layer in layers:
            # rendering
            layer.render_table(paper=paper, meta=meta)
