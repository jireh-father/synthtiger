"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from utils.switch import BoolSwitch
import sys

sys.setrecursionlimit(10 ** 6)


class Selector:
    def __init__(self, components_or_names, weights=None, postfix=None, prob=None):
        if isinstance(components_or_names, list):
            if len(components_or_names) == 2 and all(isinstance(c, float) for c in components_or_names):
                self.components_or_names = {'low': components_or_names[0], 'high': components_or_names[1]}
            elif len(components_or_names) == 2 and all(isinstance(c, int) for c in components_or_names):
                self.components_or_names = list(range(components_or_names[0], components_or_names[1] + 1))
            else:
                self.components_or_names = components_or_names
        else:
            self.components_or_names = [components_or_names]
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
                return str(self.components_or_names[idx]) + self.postfix
            return self.components_or_names[idx]


def parse_config(config):
    config_selector = {}
    for key in config:
        val = config[key]
        if isinstance(val, dict):
            if 'prob' in val:
                if 'values' in val:
                    config_selector[key] = Selector(**val)
                else:
                    if len(val) > 1:
                        config_selector[key] = BoolSwitch(prob=val['prob'], data=parse_config(
                            {sub_key: val for sub_key in val if sub_key != 'prob'}))
                    else:
                        config_selector[key] = BoolSwitch(prob=val['prob'])
            elif 'weight' in val:
                weights = []
                components = []
                for k in config:
                    v = config[k]
                    weights.append(v['weight'])
                    if len(v) > 1:
                        components.append({k: parse_config({sub_key: v for sub_key in v if sub_key != 'weight'})})
                    else:
                        components.append(k)

                return Selector(components, weights)
            elif 'values' in val:
                config_selector[key] = Selector(**val)
            else:
                config_selector[key] = parse_config(val)
        # elif isinstance(val, list):
        #     pass
        else:
            if not val:
                config_selector[key] = val
            else:
                config_selector[key] = Selector(val)
    return config_selector
