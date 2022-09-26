"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from utils.switch import BoolSwitch


class Selector:
    def __init__(self, components_or_names, weights=None, postfix=None, prob=None):
        if len(components_or_names) == 2 and all(isinstance(c, float) for c in components_or_names):
            self.components_or_names = {'low': components_or_names[0], 'high': components_or_names[1]}
        elif len(components_or_names) == 2 and all(isinstance(c, int) for c in components_or_names):
            self.components_or_names = list(range(components_or_names[0], components_or_names[1] + 1))
        else:
            self.components_or_names = components_or_names
        if weights is None:
            weights = [1] * len(self.components_or_names)
        self._probs = np.array(weights) / sum(weights)
        self.postfix = postfix
        if prob:
            self.bool_switch = BoolSwitch(prob)
        else:
            self.bool_switch = None

    def apply(self, layers, meta=None):
        assert isinstance(self.components_or_names, list)
        idx = np.random.choice(len(self.components_or_names), replace=False, p=self._probs)
        return self.components_or_names[idx].apply(layers, meta)

    def select(self):
        if self.bool_switch and not self.bool_switch.on():
            return None

        if isinstance(self.components_or_names, dict):
            return np.random.uniform(**self.components_or_names)
        else:
            idx = np.random.choice(len(self._probs), replace=False, p=self._probs)
            if self.postfix:
                str(self.components_or_names[idx]) + self.postfix
            return self.components_or_names[idx]
