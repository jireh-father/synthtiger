"""
SynthTIGER
Copyright (c) 2021-present NAVER Corp.
MIT license
"""

import io
import sys

import numpy as np
import os
import json

from bs4 import BeautifulSoup

from synthtiger import utils
from synthtiger.components.component import Component


def search_files(root, names=None, exts=None):
    paths = []

    for dir_path, _, file_names in os.walk(root, followlinks=True):
        for file_name in file_names:
            file_path = os.path.join(dir_path, file_name)
            file_ext = os.path.splitext(file_name)[1]

            if names is not None and file_name not in names:
                continue
            if exts is not None and file_ext.lower() not in exts:
                continue

            paths.append(file_path)

    return paths


class TableCorpus(Component):
    def __init__(
            self,
            paths=(),
            weights=(),
            min_length=None,
            max_length=None,
            charset=None,
            textcase=None,
    ):
        super().__init__()
        self.paths = paths
        self.weights = weights
        self.min_length = min_length
        self.max_length = max_length
        self.charset = charset
        self.textcase = textcase
        self._contents_thead = []
        self._offsets_thead = []
        self._counts_thead = []
        self._contents_tbody = []
        self._offsets_tbody = []
        self._counts_tbody = []
        self._probs = np.array(self.weights) / sum(self.weights)
        self._charset = set()
        self._update_charset()
        self._update_contents()

    def sample(self, meta=None):
        if meta is None:
            meta = {}

        if len(self.paths) == 0:
            raise RuntimeError("Corpus path is not specified")
        if len(self.paths) != len(self.weights):
            raise RuntimeError(
                "The number of weights does not match the number of corpus paths"
            )

        if "thead_or_tbody" in meta:
            thead_or_tbody = meta["thead_or_tbody"]
        else:
            idx = np.random.choice(2, replace=False)
            thead_or_tbody = ["tbody", "thead"][idx]

        text = self._sample_text(thead_or_tbody)
        text = self._random_textcase(text)
        text = meta.get("text", text)

        meta = {
            "text": text,
        }

        return meta

    def data(self, meta):
        text = meta["text"]
        return text

    def _update_charset(self):
        self._charset = set()
        if self.charset is not None:
            self._charset = utils.read_charset(self.charset)

    def _update_contents(self):
        self._contents_thead = []
        self._offsets_thead = []
        self._counts_thead = []
        self._contents_tbody = []
        self._offsets_tbody = []
        self._counts_tbody = []
        print(self.paths)
        for path in self.paths:
            print(path)
            offset_thead = 0
            count_thead = 0
            contents_thead = io.StringIO()
            offsets_thead = io.BytesIO()
            offsets_thead.write(offset_thead.to_bytes(4, sys.byteorder, signed=False))
            offset_tbody = 0
            count_tbody = 0
            contents_tbody = io.StringIO()
            offsets_tbody = io.BytesIO()
            offsets_tbody.write(offset_tbody.to_bytes(4, sys.byteorder, signed=False))

            paths = [path]
            if os.path.isdir(path):
                paths = search_files(path, exts=['.json'])

            for json_path in paths:
                print(json_path)
                data = json.load(open(json_path, encoding="utf-8"))
                html = data['html'].strip()
                bs = BeautifulSoup(html, 'html.parser')
                thead = bs.find("thead")
                if thead:
                    for td in thead.find_all("td"):
                        text = td.string.text.strip()
                        if not self._check_length(text):
                            continue
                        if not self._check_charset(text):
                            continue

                        contents_thead.write(text)
                        offset_thead += len(text)
                        offsets_thead.write(offset_thead.to_bytes(4, sys.byteorder, signed=False))
                        count_thead += 1
                    thead.extract()
                tbody = bs.find("table")
                for td in tbody.find_all("td"):
                    text = td.string.text.strip()
                    if not self._check_length(text):
                        continue
                    if not self._check_charset(text):
                        continue

                    contents_tbody.write(text)
                    offset_tbody += len(text)
                    offsets_tbody.write(offset_tbody.to_bytes(4, sys.byteorder, signed=False))
                    count_tbody += 1

            self._contents_thead.append(contents_thead.getvalue())
            self._offsets_thead.append(np.frombuffer(offsets_thead.getvalue(), dtype=np.uint32))
            self._counts_thead.append(count_thead)
            self._contents_tbody.append(contents_tbody.getvalue())
            self._offsets_tbody.append(np.frombuffer(offsets_tbody.getvalue(), dtype=np.uint32))
            self._counts_tbody.append(count_tbody)
            print(self._counts_thead)
            print(self._counts_tbody)
            sys.exit()

            contents_thead.close()
            offsets_thead.close()
            contents_tbody.close()
            offsets_tbody.close()

    def _check_length(self, text):
        if self.min_length is not None and len(text) < self.min_length:
            return False
        if self.max_length is not None and len(text) > self.max_length:
            return False
        return True

    def _check_charset(self, text):
        if self.charset is not None:
            if len(set(text) - self._charset) > 0:
                return False
        return True

    def _get_text(self, key, idx, thead_or_tbody):
        if thead_or_tbody == "thead":
            start = self._offsets_thead[key][idx]
            end = self._offsets_thead[key][idx + 1]
            text = self._contents_thead[key][start:end]
        else:
            start = self._offsets_tbody[key][idx]
            end = self._offsets_tbody[key][idx + 1]
            text = self._contents_tbody[key][start:end]
        return text

    def _sample_text(self, thead_or_tbody):
        key = np.random.choice(len(self.paths), p=self._probs)
        if thead_or_tbody == "thead" and self._counts_thead[key] == 0:
            # raise RuntimeError(f"There is no text: {self.paths[key]}")
            thead_or_tbody = "tbody"
        if thead_or_tbody == "tbody" and self._counts_tbody[key] == 0:
            raise RuntimeError(f"There is no text: {self.paths[key]}")

        idx = np.random.randint(self._counts_thead[key] if thead_or_tbody == "thead" else self._counts_tbody[key])

        text = self._get_text(key, idx, thead_or_tbody)
        return text

    def _random_textcase(self, text):
        if self.textcase is None:
            return text

        textcase = self.textcase[np.random.randint(len(self.textcase))]

        if textcase == "lower":
            text = text.lower()
        if textcase == "upper":
            text = text.upper()
        if textcase == "capitalize":
            text = text.capitalize()

        return text
