"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
from synthtiger import components, layers


class Html:
    def __init__(self, config):
        self.image = components.BaseTexture(**config.get("image", {}))
        self.paper = Paper(config.get("paper", {}))
        self.table_html = Html(config.get("html", {}))
        self.header_html = Html(config.get("html", {}))
        self.body_html = Html(config.get("html", {}))
        self.html = Html(config.get("html", {}))

    def generate(self, size):
        # todo: build html with css
        paper_layer = layers.RectLayer(size, (255, 255, 255, 255))
        self.image.apply([paper_layer])

        return html, html_with_css
