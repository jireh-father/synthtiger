import io
import sys
import json

import numpy as np

from synthtiger import utils
from synthtiger.components.component import Component
from synthtiger import components

import components as comps
from utils.selector import Selector, ValueSelector
from utils.switch import BoolSwitch
from utils.path_selector import PathSelector
from PIL import Image

class StaticTable(Component):
    def __init__(self, html_paths, image_paths, path_weights, lower_image_size_ratios, common):
        super(StaticTable, self).__init__()
        self.html_path_selector = PathSelector(html_paths, path_weights, exts=['json'])
        self.image_path_selector = PathSelector(image_paths, path_weights, exts=['jpg', 'png'])
        self.lower_image_size_ratios = lower_image_size_ratios

        self.min_rows = common['rows'][0]
        self.max_rows = common['rows'][1]
        self.min_cols = common['cols'][0]
        self.max_cols = common['cols'][1]
        self.has_span = BoolSwitch(common['has_span'])
        self.has_col_span = BoolSwitch(common['has_col_span'])
        self.has_row_span = BoolSwitch(common['has_row_span'])

        bg_config = config.get("background", {})
        self.bg_components = components.Selector(
            [
                comps.Color(bg_config.get("color", {})),
                comps.Gradient(bg_config.get("gradient", {})),
                comps.Image(bg_config.get("image", {})),
                comps.Paper(bg_config.get("paper", {})),
            ],
            bg_config.get("weights", None)
        )

        html_config = config.get("html", {})
        self.paths = html_config['paths']
        self.weights = html_config['weights']
        self.html_path_component = comps.Path(paths=html_config.get("paths"), weights=html_config.get("weights", None),
                                              exts="html")

        self.weights = weights
        self.min_length = min_length
        self.max_length = max_length
        self.charset = charset
        self.textcase = textcase
        self._contents = []
        self._offsets = []
        self._counts = []
        self._probs = np.array(self.weights) / sum(self.weights)
        self._charset = set()
        self._update_charset()
        self._update_contents()

    def sample(self, meta=None):
        if meta is None:
            meta = {}

        html_path, key, idx = self.html_path_selector.select()
        image_path = self.image_path_selector.get(key, idx)

        meta["html_path"] = html_path
        meta["image_path"] = image_path
        meta["lower_image_size_ratio"] = self.lower_image_size_ratios[key]

        return meta

    def apply(self, layers, meta=None):
        target_size = meta['size']
        while True:
            meta = self.sample(meta)
            html_json_path = meta['html_path']
            html_json = json.load(open(html_json_path), encodings='utf-8')
            if self.min_cols > html_json['nums_col'] or self.max_cols < html_json['nums_col']:
                continue
            if self.min_rows > html_json['nums_row'] or self.max_rows < html_json['nums_row']:
                continue
            has_span = self.has_span.on()
            if has_span != html_json['has_span']:
                continue

            width_limit = html_json['width'] * meta["lower_image_size_ratio"]
            height_limit = html_json['height'] * meta["lower_image_size_ratio"]

            target_width, target_height = target_size

            if width_limit > target_width or height_limit > target_height:
                continue

            if has_span:
                if self.has_row_span.on() and not html_json['has_row_span']:
                    continue
                if self.has_col_span.on() and not html_json['has_col_span']:
                    continue

            html = html_json['html']
            image_path = meta['image_path']
            utils.resize_image()
            break

        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
            image.thumbnail()

        for layer in layers:
            layer.plain_html = html
            layer.render_table(image_path)
