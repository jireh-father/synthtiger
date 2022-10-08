import traceback
from synthtiger.layers.layer import Layer
from PIL import Image
import uuid
import os
import numpy as np
import sys
from selenium.webdriver.common.by import By
from selenium import webdriver
from utils import image_util
from utils.selector import parse_config
import components


class TableLayer(Layer):
    def __init__(self, size):
        self.table_size = size
        self.html = None
        self.meta = None
        self.global_style = {}

    def _convert_global_style_to_css(self):
        css_list = []
        for selector in self.global_style:
            if selector == '@font-face':
                for font_face_dict in self.global_style[selector]:
                    styles = []
                    for key in font_face_dict:
                        styles.append("{}: {};".format(key, font_face_dict[key]))
                    css_list.append(selector + " { " + "".join(styles) + " }")
            else:
                styles = []
                for key in self.global_style[selector]:
                    value = self.global_style[selector][key]
                    styles.append("{}: {};".format(key, value))

                css_list.append(selector + " { " + "".join(styles) + " }")

        return "\n".join(css_list)

    def _write_html_file(self, html_path):
        html_template = """
        <html>
        <head>
            <meta charset="UTF-8">
             <style>
             {}
            </style>
        </head>
        <body>
            <div id="table_wrapper">
                {}
            </div>
        </body>
        </html>
        """
        with open(html_path, "w+") as html_file:
            html = html_template.format(self._convert_global_style_to_css(), self.html)
            html_file.write(html)

    def _get_margin_vertical_and_horizontal(self):
        margin_vertical = 0
        margin_horizontal = 0
        if 'margin-left' in self.global_style['table']:
            margin_horizontal += int(self.global_style['table']['margin-left'].split("px")[0])
        elif 'margin' in self.global_style['table']:
            margin_horizontal += int(self.global_style['table']['margin'].split("px")[0]) / 2

        if 'margin-right' in self.global_style['table']:
            margin_horizontal += int(self.global_style['table']['margin-right'].split("px")[0])
        elif 'margin' in self.global_style['table']:
            margin_horizontal += int(self.global_style['table']['margin'].split("px")[0]) / 2

        if 'margin-top' in self.global_style['table']:
            margin_vertical += int(self.global_style['table']['margin-top'].split("px")[0])
        elif 'margin' in self.global_style['table']:
            margin_vertical += int(self.global_style['table']['margin'].split("px")[0]) / 2

        if 'margin-bottom' in self.global_style['table']:
            margin_vertical += int(self.global_style['table']['margin-bottom'].split("px")[0])
        elif 'margin' in self.global_style['table']:
            margin_vertical += int(self.global_style['table']['margin'].split("px")[0]) / 2
        return margin_horizontal, margin_vertical

    def _render_table_selenium(self, html_path, image_path, paper):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome('chromedriver', options=options)
        driver.implicitly_wait(0.5)

        self._write_html_file(html_path)
        driver.get("file:///{}".format(os.path.abspath(html_path)))
        required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        driver.set_window_size(required_width, required_height)

        table_element = driver.find_element(By.TAG_NAME, 'table')

        table_width = int(table_element.size['width'] * self.meta['relative_style']['table']['width_scale'])
        table_height = int(table_element.size['height'] * self.meta['relative_style']['table']['height_scale'])
        ar = table_width / table_height
        if self.meta['aspect_ratio'][0] > ar:
            table_width = int(table_height * self.meta['aspect_ratio'][0])
        elif self.meta['aspect_ratio'][1] < ar:
            table_height = int(table_width / self.meta['aspect_ratio'][1])

        # driver.close()
        margin_horizontal, margin_vertical = self._get_margin_vertical_and_horizontal()
        image_width = table_width + margin_horizontal  # meta['margin_width']
        image_height = table_height + margin_vertical  # meta['margin_height']

        self.global_style['table']['width'] = str(table_width) + "px"
        self.global_style['table']['height'] = str(table_height) + "px"

        self.meta['css'] = self._convert_global_style_to_css()

        if paper is not None:
            paper_layer = paper.generate((image_width, image_height))
            base64_image = image_util.image_to_base64(paper_layer.image)
            self.global_style['#table_wrapper']['background-image'] = 'url("data:image/png;base64,{}")'.format(
                base64_image)

        self._write_html_file(html_path)

        driver.get("file:///{}".format(os.path.abspath(html_path)))
        driver.set_window_size(int(image_width * 1.2), int(image_height * 1.2))
        div_element = driver.find_element(By.ID, 'table_wrapper')
        div_element.screenshot(image_path)
        driver.close()

    def effect(self, image):
        selectors = parse_config(self.meta["effect_config"])
        if not selectors["distort"].on():
            self.meta["distort"] = False
            return image

        image = np.array(image)

        self.meta["distort"] = True

        effect_config = selectors["distort"].get().select()
        self.meta['table_effect'] = effect_config['name']
        if effect_config['name'] == "arc":
            arc = components.Arc(self.meta["effect_config"]["distort"]["arc"]["angles"], self.meta["effect_config"]["distort"]["arc"]["reverse"]["prob"])
            image = arc.apply_image(image)
        elif effect_config['name'] == "polynomial":
            polynomial = components.Polynomial(self.meta["effect_config"]["distort"]["polynomial"]["dest_coord_ratios"],
                                               self.meta["effect_config"]["distort"]["polynomial"]["move_prob"])
            image = polynomial.apply_image(image)
        return image

    def render_table(self, image=None, paper=None, meta=None):
        self.meta = meta
        self.html = meta['html']

        if not image:
            tmp_path = meta['tmp_path']
            image_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".png")
            html_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".html")

            try:
                self.global_style = meta['global_style']
                self._render_table_selenium(html_path, image_path, paper)
            except Exception as e:
                if os.path.isfile(image_path):
                    os.unlink(image_path)
                if os.path.isfile(html_path):
                    os.unlink(html_path)
                raise e

            image = Image.open(image_path)
            os.unlink(image_path)
            os.unlink(html_path)

        image = self.effect(image)

        super().__init__(image)

        height, width = self.image.shape[:2]
        self.table_size = (width, height)
