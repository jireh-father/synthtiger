import traceback

from synthtiger.layers.layer import Layer
from PIL import Image
import uuid
import os
import sys
from selenium.webdriver.common.by import By
from selenium import webdriver
from utils import image_util


class TableLayer(Layer):
    def __init__(self, size):
        self.table_size = size
        self.html = {}
        self.plain_html = None
        self.plain_html_with_styles = None
        self.global_style = {}

    def _convert_global_style_to_css(self):
        # table {
        #   width: 600px;
        #   border-collapse: collapse;
        # }

        css_list = []
        for selector in self.global_style:
            styles = []
            for key in self.global_style[selector]:
                value = self.global_style[selector][key]
                styles.append("{}: {};".format(key, value))
            css_list.append("{} { {} }".format(selector, "".join(styles)))

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
            html_template.format(self._convert_global_style_to_css(), self.plain_html_with_styles)
            html_file.write(self.plain_html_with_styles)

    def _add_global_styles(self, styles):
        for selector in styles:
            if selector not in self.global_style:
                self.global_style[selector] = {}
            for style_key in styles[selector]:
                self.global_style[selector][style_key] = styles[selector][style_key]

    def _render_table_selenium(self, html_path, image_path, paper, max_size):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome('chromedriver', options=options)

        window_size = max_size * 2
        while True:
            self._write_html_file(html_path)
            driver.get("file:///{}".format(os.path.join(sys.path[0], html_path)))
            # original_size = driver.get_window_size()
            # required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
            # required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
            # required_width = 1280
            # bigger than table
            driver.set_window_size(window_size, window_size)

            div = driver.find_element(By.ID, 'table_wrapper')
            # todo: get div size and apply
            table_width = div.size['width']
            table_height = div.size['height']
            if table_width >= window_size or table_height >= window_size:
                window_size += max_size
            else:
                break

        paper_layer = paper.generate((table_width, table_height))
        base64_image = image_util.image_to_base64(paper_layer.image)

        self._add_global_styles(
            {'#table_wrapper': {"background-image": 'url("data:image/png;base64,{}")'.format(base64_image)}})
        self._write_html_file(html_path)

        driver.get("file:///{}".format(os.path.join(sys.path[0], html_path)))

        div.screenshot(image_path)
        driver.set_window_size(window_size, window_size)
        driver.close()

    def render_table(self, image=None, tmp_path=None, paper=None, max_size=None):
        if not image:
            image_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".jpg")
            html_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".html")

            try:
                self._render_table_selenium(html_path, image_path, paper, max_size)
            except Exception as e:
                if os.path.isfile(image_path):
                    os.unlink(image_path)
                if os.path.isfile(html_path):
                    os.unlink(html_path)
                raise e

            image = Image.open(image_path)
            os.unlink(image_path)
            os.unlink(html_path)

        super().__init__(image)

        height, width = self.image.shape[:2]
        self.table_size = (width, height)
