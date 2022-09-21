"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from synthtiger import components

from elements.content import Content
from elements.paper import Paper

class Document:
    def __init__(self, config):
        self.fullscreen = config.get("fullscreen", 0.5)
        self.landscape = config.get("landscape", 0.5)
        self.short_size = config.get("short_size", [480, 1024])
        self.aspect_ratio = config.get("aspect_ratio", [1, 2])
        self.content = Content(config.get("content", {}))
        self.paper = Paper(config["document"]["paper"])
        self.effect = components.Iterator(
            [
                components.Switch(components.ElasticDistortion()),
                components.Switch(components.AdditiveGaussianNoise()),
                components.Switch(
                    components.Selector(
                        [
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                        ]
                    )
                ),
            ],
            **config.get("effect", {}),
        )

    def generate(self, size):
        width, height = size
        fullscreen = np.random.rand() < self.fullscreen

        if not fullscreen:
            landscape = np.random.rand() < self.landscape
            max_size = width if landscape else height
            short_size = np.random.randint(
                min(width, height, self.short_size[0]),
                min(width, height, self.short_size[1]) + 1,
            )
            aspect_ratio = np.random.uniform(
                min(max_size / short_size, self.aspect_ratio[0]),
                min(max_size / short_size, self.aspect_ratio[1]),
            )
            long_size = int(short_size * aspect_ratio)
            size = (long_size, short_size) if landscape else (short_size, long_size)

        table_layer = self.content.generate(size)

        table_size = table_layer.table_size
        if table_size[0] > size[0] or table_size[1] > size[1]:
            if table_size[0] > self.short_size[0] or table_size[1] > self.short_size[1]:
                print("research image file")
                return self.generate()
            else:
                new_width = table_size[0]
                new_height = table_size[1]
                if table_size[0] > size[0]:
                    new_width = np.random.randint(table_size[0], self.short_size[0] + 1)
                if table_size[1] > size[1]:
                    new_height = np.random.randint(table_size[1], self.short_size[1] + 1)

                size = (new_width, new_height)

        print("last size", size)
        paper_layer = self.paper.generate(size)

        self.effect.apply([table_layer, paper_layer])

        return table_layer, paper_layer
