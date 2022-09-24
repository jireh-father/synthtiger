from utils.selector import Selector


def add_styles(target_styles, new_styles):
    for selector in new_styles:
        for style_key in new_styles[selector]:
            target_styles[selector][style_key] = new_styles[selector][style_key]


def parse_html_style_values_list(list_values):
    list(range(list_values[0], list_values[1] + 1)), [1] * len(list_values)


def parse_html_style_values_dict(dict_values):
    weights = dict_values['weights'] if 'weights' in dict_values else [1] * len(dict_values['values'])
    postfix = dict_values['postfix'] if 'postfix' in dict_values else None

    return dict_values['values'], weights, postfix


def parse_html_style_values(values):
    if isinstance(values, list):
        if len(values) == 2 and all(isinstance(v, int) for v in values):
            return Selector(*parse_html_style_values_list(values))
        else:
            return Selector(values, [1] * len(values))
    elif isinstance(values, dict):
        return Selector(*parse_html_style_values_dict(values))


def parse_html_style(config):
    selectors = {}
    for k in config:
        v = config[k]
        selectors[k] = parse_html_style_values(v)
