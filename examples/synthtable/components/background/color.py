"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
from synthtiger import components, layers
from elements.paper import Paper
from elements.htl import Html

class Table:
    def __init__(self, config):
        self.html = Html(config.get("html", {}))
        self.image = components.BaseTexture(**config.get("image", {}))

    def generate(self, size):
        # render table to image
        paper_layer = layers.RectLayer(size, (255, 255, 255, 255))
        self.image.apply([paper_layer])

        return paper_layer
