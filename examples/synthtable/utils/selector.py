"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np


class Selector:
    def __init__(self, components_or_names, weights=None):
        self.components_or_names = components_or_names
        if weights is None:
            weights = [1] * len(components_or_names)
        self._probs = np.array(weights) / sum(weights)

    def apply(self, layers, meta=None):
        idx = np.random.choice(len(self.components_or_names), replace=False, p=self._probs)
        return self.components_or_names[idx].apply(layers, meta)

    def select(self):
        idx = np.random.choice(len(self._probs), replace=False, p=self._probs)
        return self.components_or_names[idx]
