"""
SynthTIGER
Copyright (c) 2021-present NAVER Corp.
MIT license
"""

from synthtiger import utils
from synthtiger.components.component import Component


class Border(Component):
    def __init__(self, color, top, bottom, left, right, width, same_width=0.5):
        super().__init__()
        self.color = color
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.same_width = same_width

    def sample(self, meta=None):
        color = meta.get("color", [] if self.color_range else [0, 0, 0, 255])
        width = meta.get("width", [] if self.color_range else 1)
        meta = {
            'color': color,
            'width': width
        }
        return meta

    def apply(self, layers, meta=None):
        meta = self.sample(meta)

        for layer in layers:
            image = utils.grayscale_image(layer.image)
            layer.image = image

        return meta
