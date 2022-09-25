import traceback
from utils.html_style import add_styles
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
                <table>
                {}
                </table>
            </div>
        </body>
        </html>
        """
        with open(html_path, "w+") as html_file:
            html = html_template.format(self._convert_global_style_to_css(), self.plain_html_with_styles)
            html_file.write(html)

    def _render_table_selenium(self, html_path, image_path, paper, meta):
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
        # todo: get div size and apply
        print("ori table", table_element.size['width'], table_element.size['height'])
        table_width = int(table_element.size['width'] * meta['table_width'])
        table_height = int(table_element.size['height'] * meta['table_height'])
        print("table expand", meta['table_width'], meta['table_height'])
        print("aft table", table_width, table_height)

        print("margin_width", meta['margin_width'])
        print("margin_height", meta['margin_height'])

        # driver.close()
        image_width = table_width + meta['margin_width']
        image_height = table_height + meta['margin_height']
        print("image", image_width, image_height)

        paper_layer = paper.generate((image_width, image_height))
        base64_image = image_util.image_to_base64(paper_layer.image)

        # driver = webdriver.Chrome('chromedriver', options=options)
        # driver.implicitly_wait(0.5)

        add_styles(self.global_style,
                   {'table': {"width": str(table_width) + "px", "height": str(table_height) + "px", }})
        print("global style", self.global_style)
        add_styles(self.global_style,
                   {'#table_wrapper': {"background-image": 'url("data:image/png;base64,{}")'.format(base64_image)}})

        self._write_html_file(html_path)
        print(self.plain_html_with_styles)

        driver.get("file:///{}".format(os.path.abspath(html_path)))
        driver.set_window_size(image_width, image_height)
        div_element = driver.find_element(By.ID, 'table_wrapper')
        div_element.screenshot(image_path)
        # driver.set_window_size(table_width, table_height)
        driver.close()

    def render_table(self, image=None, tmp_path=None, paper=None, meta=None):
        if not image:
            image_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".png")
            html_path = os.path.join(tmp_path, str(uuid.uuid4()) + ".html")

            try:
                self._render_table_selenium(html_path, image_path, paper, meta)
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
