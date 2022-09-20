"""
SynthTIGER
Copyright (c) 2021-present NAVER Corp.
MIT license
"""

import os

import numpy as np
from PIL import Image, ImageOps

from synthtiger import utils
from synthtiger.components.component import Component


class Path(Component):
    def __init__(self, paths=(), weights=(), exts=None, path_var_name='path', parent_path_var_name=None):
        super().__init__()
        self.paths = paths
        self.path_var_name = path_var_name
        self.parent_path_var_name = parent_path_var_name
        self.weights = weights if weights else [1] * len(paths)
        self.exts = exts
        self._paths = []
        self._counts = []
        self._probs = np.array(self.weights) / sum(self.weights)
        self._update_paths()

    def sample(self, meta=None):
        if meta is None:
            meta = {}
        meta["path"], meta["path_key"], meta["path_idx"] = self._sample_path()
        return meta

    def apply(self, layers, meta=None):
        meta = self.sample(meta)
        path, path_key, path_idx = self.data(meta)
        for layer in layers:
            if self.parent_path_var_name and hasattr(layer, self.parent_path_var_name):
                parent_key = getattr(layer, self.parent_path_var_name + "_key")
                parent_idx = getattr(layer, self.parent_path_var_name + "_idx")
                setattr(layer, self.path_var_name, self._paths[parent_key][parent_idx])
                setattr(layer, self.path_var_name + "_key", parent_key)
                setattr(layer, self.path_var_name + "_idx", parent_idx)
            else:
                setattr(layer, self.path_var_name, path)
                setattr(layer, self.path_var_name + "_key", path_key)
                setattr(layer, self.path_var_name + "_idx", path_idx)

    def data(self, meta):
        return meta['path'], meta['path_key'], meta['path_idx']

    def _update_paths(self):
        self._paths = []
        self._counts = []

        for path in self.paths:
            if not os.path.exists(path):
                continue

            paths = [path]
            if os.path.isdir(path):
                paths = utils.search_files(path, exts=self.exts)
            paths.sort()
            self._paths.append(paths)
            self._counts.append(len(paths))

    def _sample_path(self):
        key = np.random.choice(len(self.paths), p=self._probs)
        if self._counts[key] == 0:
            raise RuntimeError(f"There is no texture: {self.paths[key]}")

        idx = np.random.randint(len(self._paths[key]))
        path = self._paths[key][idx]
        return path, key, idx
