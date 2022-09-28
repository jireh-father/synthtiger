import os.path
import json
import traceback

from PIL import Image
from utils import image_util
from synthtiger.components.component import Component

from utils.path_selector import PathSelector


class StaticTable(Component):
    # def __init__(self, html_paths, image_paths, path_weights, lower_image_size_ratios, html, **kwargs):
    def __init__(self, config_selectors):

        super(StaticTable, self).__init__()
        self.html_path_selector = PathSelector(config_selectors['html']['paths'].values,
                                               config_selectors['html']['weights'].values, exts=['.json'])
        self.image_path_selector = PathSelector(config_selectors['image']['paths'].values, None,
                                                exts=['.jpg', '.png'])
        self.lower_image_size_ratios = config_selectors['image']['lower_image_size_ratios'].values

        self.config_selectors = config_selectors

        self.min_rows = config_selectors['html']['min_row'].select()
        self.max_rows = config_selectors['html']['max_row'].select()
        self.min_cols = config_selectors['html']['min_col'].select()
        self.max_cols = config_selectors['html']['max_row'].select()

        self.has_span = self.config_selectors['html']['has_span']
        self.has_col_span = self.config_selectors['html']['has_col_span']
        self.has_row_span = self.config_selectors['html']['has_row_span']

    def _get_image_path(self, html_path, key):
        html_file_name = os.path.splitext(os.path.basename(html_path))[0]
        image_path = self.image_path_selector.get_path(key)
        for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
            path = os.path.join(image_path, html_file_name) + "." + ext
            if os.path.isfile(path):
                return path
        return None

    def sample(self, meta=None):
        if meta is None:
            meta = {}

        html_path, key, idx = self.html_path_selector.select()
        image_path = self._get_image_path(html_path, key)
        if not image_path:
            raise Exception("not found image path.")

        meta["html_path"] = html_path
        meta["image_path"] = image_path
        meta["lower_image_size_ratio"] = self.lower_image_size_ratios[key]

        return meta

    def apply(self, layers, meta=None):
        target_size = meta['size']
        while True:
            try:
                meta = self.sample(meta)
            except Exception as e:
                traceback.print_exc()
                continue
            html_json_path = meta['html_path']
            html_json = json.load(open(html_json_path), encoding='utf-8')
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
            break

        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image, target_size = image_util.resize_keeping_aspect_ratio(image, target_size, Image.ANTIALIAS)
        for layer in layers:
            layer.plain_html = html
            layer.render_table(image=image)
