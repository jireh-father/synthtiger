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
import argparse
import re
from utils import html_util


class SynthTable(templates.Template):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}

        self.html_output = config.get("html_output")
        self.quality = config.get("quality", [50, 95])
        self.save_meta = config.get("save_meta", False)
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

    def _filter_html(self, html):
        if self.html_output["remove_tag_in_content"]:
            html = html_util.remove_tag_in_table_cell(html)

        if self.html_output["remove_thead_tbody"]:
            html = html_util.remove_thead_tbody_tag(html)

        if self.html_output["remove_close_tag"]:
            html = html_util.remove_close_tags(html)

        return html

    def generate(self):
        # todo:
        '''
        synth structure

        synth contents

        meta 넣어서 static 이미지 만들기
        
        # meta data 보고 버그없는지 디버깅
         - 폰트때문에 텍스트 깨지는거 있는지 확인
        '''

        table_layer, bg_size = self.document.generate()

        bg_layer, bg_image_meta, bg_effect_meta = self.background.generate(bg_size)
        table_layer.meta['bg_image'] = bg_image_meta
        table_layer.meta['bg_effect'] = bg_effect_meta

        # todo: remove etc tag in td cell(ex: <td><b>contents</b></td>)
        table_html = self._filter_html(table_layer.html)

        document_space = np.clip(bg_size - table_layer.size, 0, None)
        table_layer.left = np.random.randint(document_space[0] + 1)
        table_layer.top = np.random.randint(document_space[1] + 1)
        roi = np.array(table_layer.quad, dtype=int)

        layer = layers.Group([table_layer, bg_layer]).merge()
        effect_meta = self.effect.apply([layer])

        table_layer.meta['template_effect'] = effect_meta

        image = layer.output(bbox=[0, 0, *bg_size])
        quality = np.random.randint(self.quality[0], self.quality[1] + 1)
        table_layer.meta['quality'] = quality
        data = {
            "image": image,
            "label": table_html,
            "quality": quality,
            "roi": roi,
            "meta": table_layer.meta,
            "save_meta": self.save_meta
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
        meta = data["meta"]
        save_meta = data['save_meta']

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

        # save meta json file
        if save_meta:
            meta_filename = f"image_{file_idx}_meta.json"
            meta_filepath = os.path.join(output_dirpath, meta_filename)
            json.dump(meta, open(meta_filepath, "w+", encoding='utf-8'))

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--model_path', type=str, default=None)
    parser.add_argument('--csv_file', type=str, default=None)
    parser.add_argument('--model_name', type=str, default='efficientnet-b2')
    parser.add_argument('--input_size', type=int, default=260)
    parser.add_argument('--line_width', type=int, default=1)
    parser.add_argument('--use_cuda', action='store_true', default=False)

    synth_table = SynthTable()
    synth_table.generate_static(config)
