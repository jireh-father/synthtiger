from components.common.path import Path


class TableHtmlFile(Path):
    def __init__(self, paths=(), weights=()):
        super().__init__(paths, weights, exts=['json'], path_var_name="html_path")
