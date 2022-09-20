from components.common.path import Path


class TableImageFile(Path):
    def __init__(self, paths=()):
        super().__init__(paths, weights=None, exts=['jpg', 'png'], path_var_name="image_path",
                         parent_path_var_name="html_path")
