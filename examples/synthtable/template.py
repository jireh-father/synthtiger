"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import json
import os
import re
import uuid
from typing import Any, List

import numpy as np
from elements import Background, Document
from PIL import Image
from synthtiger import components, layers, templates



class SynthTable(templates.Template):
    def __init__(self, config=None, split_ratio: List[float] = [0.8, 0.1, 0.1]):
        super().__init__(config)
        if config is None:
            config = {}

        self.quality = config.get("quality", [50, 95])
        self.background = Background(config.get("background", {}))
        self.document = Document(config.get("document", {}))
        self.effect = components.Iterator(
            [
                components.Switch(components.RGB()),
                components.Switch(components.Shadow()),
                components.Switch(components.Contrast()),
                components.Switch(components.Brightness()),
                components.Switch(components.MotionBlur()),
                components.Switch(components.GaussianBlur()),
            ],
            **config.get("effect", {}),
        )

        # config for splits (output_filename, split_ratio etc)
        # self.splits = ["train", "validation", "test"]
        # self.split_indexes = [0, 0, 0]
        # self.split_ratio = [sum(split_ratio[: i + 1]) for i in range(0, len(split_ratio))]

    def generate(self):
        table_layer, bg_size = self.document.generate()

        bg_layer = self.background.generate(bg_size)
        table_html = table_layer.plain_html

        document_space = np.clip(bg_size - table_layer.size, 0, None)
        table_layer.left = np.random.randint(document_space[0] + 1)
        table_layer.top = np.random.randint(document_space[1] + 1)
        roi = np.array(table_layer.quad, dtype=int)

        layer = layers.Group([table_layer, bg_layer]).merge()
        self.effect.apply([layer])

        image = layer.output(bbox=[0, 0, *bg_size])
        quality = np.random.randint(self.quality[0], self.quality[1] + 1)

        data = {
            "image": image,
            "label": table_html,
            "quality": quality,
            "roi": roi,
        }

        return data

    def init_save(self, root):
        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)

    def save(self, root, data, idx):
        image = data["image"]
        label = data["label"]
        quality = data["quality"]
        roi = data["roi"]

        # split
        # output_dirpath = os.path.join(root, "train")
        output_dirpath = root

        file_idx = idx

        # split_prob = np.random.rand()
        # for _idx, (split, ratio) in enumerate(zip(self.splits, self.split_ratio)):
        #     if split_prob < ratio:
        #         output_dirpath = os.path.join(root, split)
        #         file_idx = self.split_indexes[_idx]
        #         self.split_indexes[_idx] += 1
        #         break

        # save image
        image_filename = f"image_{file_idx}.jpg"
        image_filepath = os.path.join(output_dirpath, image_filename)
        os.makedirs(os.path.dirname(image_filepath), exist_ok=True)
        image = Image.fromarray(image[..., :3].astype(np.uint8))
        image.save(image_filepath, quality=quality)

        # save metadata (gt_json)
        metadata_filename = "metadata.jsonl"
        metadata_filepath = os.path.join(output_dirpath, metadata_filename)
        os.makedirs(os.path.dirname(metadata_filepath), exist_ok=True)

        metadata = self.format_metadata(image_filename=image_filename, keys=["text_sequence"], values=[label])
        with open(metadata_filepath, "a") as fp:
            json.dump(metadata, fp, ensure_ascii=False)
            fp.write("\n")

    def end_save(self, root):
        pass

    def format_metadata(self, image_filename: str, keys: List[str], values: List[Any]):
        """
        Fit gt_parse contents to huggingface dataset's format
        keys and values, whose lengths are equal, are used to constrcut 'gt_parse' field in 'ground_truth' field
        Args:
            keys: List of task_name
            values: List of actual gt data corresponding to each task_name
        """
        assert len(keys) == len(values), "Length does not match: keys({}), values({})".format(len(keys), len(values))

        _gt_parse_v = dict()
        for k, v in zip(keys, values):
            _gt_parse_v[k] = v
        gt_parse = {"gt_parse": _gt_parse_v}
        gt_parse_str = json.dumps(gt_parse, ensure_ascii=False)
        metadata = {"file_name": image_filename, "ground_truth": gt_parse_str}
        return metadata
