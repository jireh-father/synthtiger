"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
from collections import OrderedDict

import numpy as np

from elements.table import Table

class TextReader:
    def __init__(self, path, cache_size=2 ** 28, block_size=2 ** 20):
        self.fp = open(path, "r", encoding="utf-8")
        self.length = 0
        self.offsets = [0]
        self.cache = OrderedDict()
        self.cache_size = cache_size
        self.block_size = block_size
        self.bucket_size = cache_size // block_size
        self.idx = 0

        while True:
            text = self.fp.read(self.block_size)
            if not text:
                break
            self.length += len(text)
            self.offsets.append(self.fp.tell())

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        char = self.get()
        self.next()
        return char

    def move(self, idx):
        self.idx = idx

    def next(self):
        self.idx = (self.idx + 1) % self.length

    def prev(self):
        self.idx = (self.idx - 1) % self.length

    def get(self):
        key = self.idx // self.block_size

        if key in self.cache:
            text = self.cache[key]
        else:
            if len(self.cache) >= self.bucket_size:
                self.cache.popitem(last=False)

            offset = self.offsets[key]
            self.fp.seek(offset, 0)
            text = self.fp.read(self.block_size)
            self.cache[key] = text

        self.cache.move_to_end(key)
        char = text[self.idx % self.block_size]
        return char


class Content:
    def __init__(self, config):
        self.margin = config.get("margin", [0, 0.1])
        # self.reader = TextReader(**config.get("text", {}))

        self.table = Table(config.get("table", {}))

        # self.font = components.BaseFont(**config.get("font", {}))
        # self.layout = GridStack(config.get("layout", {}))
        # self.textbox = TextBox(config.get("textbox", {}))
        # self.textbox_color = components.Switch(components.Gray(), **config.get("textbox_color", {}))
        # self.content_color = components.Switch(components.Gray(), **config.get("content_color", {}))

    def generate(self, size, selenium_driver):#, max_size):
        # width, height = size
        #
        # layout_left = width * np.random.uniform(self.margin[0], self.margin[1])
        # layout_top = height * np.random.uniform(self.margin[0], self.margin[1])
        # layout_width = max(width - layout_left * 2, 0)
        # layout_height = max(height - layout_top * 2, 0)
        # layout_bbox = [layout_left, layout_top, layout_width, layout_height]

        table_layer = self.table.generate(size, selenium_driver)#, max_size)
        return table_layer
