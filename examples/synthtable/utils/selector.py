"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np


class Selector:
    def __init__(self, components, weights):
        self.components = components
        self._probs = np.array(weights) / sum(weights)

    def apply(self, layers, meta=None):
        idx = np.random.choice(len(self.components), replace=False, p=self._probs)
        return self.components[idx].apply(layers, meta)


class ValueSelector:
    def __init__(self, weights, values=None):
        if not values:
            values = range(len(weights))
        self.values = values
        assert len(weights) == len(values)
        self._probs = np.array(weights) / sum(weights)

    def select(self):
        idx = np.random.choice(len(self._probs), replace=False, p=self._probs)
        return self.values[idx]
