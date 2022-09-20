"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
from synthtiger.components.component import Component

class SynthTable(Component):
    def __init__(self, config):
        super().__init__()

        self.html = Html(config.get("html", {}))
        self.image = components.BaseTexture(**config.get("image", {}))

    def generate(self, size):
        # render table to image
        paper_layer = layers.RectLayer(size, (255, 255, 255, 255))
        self.image.apply([paper_layer])

        return paper_layer
