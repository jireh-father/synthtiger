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
    else:
        return Selector(values)


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
    return ";".join(styles), meta


class SynthTable(Component):
    def __init__(self, config_selectors):
        super().__init__()
        self.config_selectors = config_selectors
        self.html_path_selector = PathSelector(config_selectors['html']['paths'].values,
                                               config_selectors['html']['weights'].values, exts=['.json'])

        # styles
        # todo: select parser or other backgrounds
        for background_config in config_selectors['style']['global']['absolute']['background'].values:
            if isinstance(background_config, dict):
                if 'paper' in background_config:
                    paper_params = {
                        'paths': background_config['paper']['paths'].values,
                        'weights': background_config['paper']['weights'].values,
                        'alpha': background_config['paper']['alpha'].values,
                        'grayscale': background_config['paper']['grayscale'].select(),
                        'crop': background_config['paper']['crop'].select()
                    }
                    self.paper = Paper(paper_params)
                elif 'gradient' in background_config:
                    self.gradient_bg = background_config['gradient']
                elif 'striped' in background_config:
                    self.striped_bg = background_config['striped']

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
        self.tmp_path = config_selectors['html']['tmp_path'].select()
        os.makedirs(self.tmp_path, exist_ok=True)

    def _sample_global_color_mode(self):
        return self.global_color_mode.select()

    def _sample_dark_color(self):
        return self.dark_colors.select()

    def _sample_light_color(self):
        return self.light_colors.select()

    def _sample_background(self, global_style, meta):
        # background
        background_config = self.config_selectors['style']['global']['absolute']['background'].select()
        if isinstance(background_config, dict):
            meta['background_config'] = next(iter(background_config))
        else:
            meta['background_config'] = background_config

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
        # background
        border_config = self.config_selectors['style']['global']['absolute']['border'].select()
        border_type = next(iter(border_config))
        meta['border_config'] = border_type
        border_css = border_config[border_type]

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

    def sample_global_styles(self, meta):
        # static style
        global_style = defaultdict(dict)
        global_style['#table_wrapper']["display"] = "inline-block"
        global_style['table']["border-collapse"] = "collapse"

        # absolutes
        meta['color_mode'] = self._sample_global_color_mode()

        self._sample_background(global_style, meta)

        self._sample_thead(global_style, meta)

        self._sample_table_outline(global_style, meta)

        self._sample_border(global_style, meta)

        # css
        css_selectors = self.config_selectors['style']['global']['css']
        self._set_css_to_global_style(css_selectors, global_style, meta)

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
                meta[css_selector + '_' + css_key] = value

    def _set_local_css_styles(self, global_style, config_key, css_selector_name):
        local_config = self.config_selectors['style']['local'].get()
        if local_config['css'][config_key].on():
            selectors = local_config['css'][config_key].get()
            for css_selector in selectors:
                css_val = selectors[css_selector]
                val = css_val.select()
                if val is None:
                    continue
                global_style[css_selector_name][css_selector] = val

    def sample_local_styles(self, global_style, meta):
        if not self.config_selectors['style']['local'].on():
            return

        self._set_local_css_styles(global_style, 'thead', 'thead')
        self._set_local_css_styles(global_style, 'tbody', 'tbody')

        for row_idx in range(1, meta['nums_row'] + 1):
            self._set_local_css_styles(global_style, 'tr', "tr:nth-child({})".format(row_idx))
            for col_idx in range(1, meta['nums_col'] + 1):
                self._set_local_css_styles(global_style, 'td',
                                           "tr:nth-child({}) td:nth-child({})".format(row_idx, col_idx))

    def sample(self, meta=None):
        if meta is None:
            meta = {}
        synth_structure = self.config_selectors['html']['synth_structure'].on()
        synth_content = self.config_selectors['html']['synth_content'].on()
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

        # global styles
        meta['global_style'] = self.sample_global_styles(meta)

        # local styles
        # meta['html_with_local_style'] = self.sample_local_styles(meta['html'], meta)

        # global relative styles
        relative_style = defaultdict(dict)
        relative_style_config = self.config_selectors['style']['global']['relative']
        for selector in relative_style_config:
            for key in relative_style_config[selector]:
                relative_style[selector][key] = relative_style_config[selector][key].select()

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
        global_style = meta['global_style']

        if meta['background_config'] == 'paper':
            paper = self.paper
            global_style["table"]["color"] = self._sample_dark_color()
        else:
            paper = None

        # todo: thead use !important;
        # rendering
        for layer in layers:
            # todo : remove tag in cell
            layer.html = html
            layer.global_style = global_style
            layer.render_table(tmp_path=self.tmp_path, paper=paper, meta=meta)
