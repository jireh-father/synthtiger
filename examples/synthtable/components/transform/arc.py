"""
SynthTIGER
Copyright (c) 2021-present NAVER Corp.
MIT license
"""

import numpy as np

from synthtiger.components.component import Component
from wand.image import Image
import uuid
class Arc(Component):
    def __init__(self, angles=None):
        super().__init__()
        self.angles = angles

    def sample(self, meta=None):
        if meta is None:
            meta = {}

        angle = meta.get("angle", np.random.randint(self.angles[0], self.angles[1] + 1))

        meta = {
            "angle": angle
        }

        return meta

    def apply(self, layers, meta=None):
        meta = self.sample(meta)
        angle = meta["angle"]

        for layer in layers:
            im = Image.from_array(layer.image)
            filename = str(uuid.uuid4())
            im.save(filename=filename + "_before.png")
            im.virtual_pixel = 'transparent'
            im.distort('arc', (angle,))
            im.save(filename=filename + "_after.png")
            layer.image = np.array(im)

        return meta

    def apply_image(self, image):
        meta = self.sample(None)
        angle = meta["angle"]

        im = Image.from_array(image)
        filename = str(uuid.uuid4())
        im.save(filename=filename + "_before.png")
        im.virtual_pixel = 'transparent'
        im.distort('arc', (angle,))
        im.save(filename=filename + "_after.png")

        return np.array(im)
