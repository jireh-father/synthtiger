import os

import numpy as np

from synthtiger import utils


class PathSelector:
    def __init__(self, paths=(), weights=(), exts=None, use_sort=True):
        super().__init__()
        self.paths = paths
        self.weights = weights if weights else [1] * len(paths)
        self.exts = exts
        self.use_sort = use_sort
        self._paths = []
        self._counts = []
        self._probs = np.array(self.weights) / sum(self.weights)
        self._update_paths()

    def select(self):
        return self._sample_path()

    def get(self, key, idx):
        return self._paths[key][idx]

    def get_path(self, key):
        return self.paths[key]

    def _update_paths(self):
        self._paths = []
        self._counts = []

        for path in self.paths:
            if not os.path.exists(path):
                continue

            paths = [path]
            if os.path.isdir(path):
                paths = utils.search_files(path, exts=self.exts)
            if self.use_sort:
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
