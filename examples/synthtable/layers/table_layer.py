from synthtiger.layers.layer import Layer
from PIL import Image


class TableLayer(Layer):
    def __init__(self, size):
        self.size = size
        self.html = {}
        self.plain_html = None
        self.plain_html_with_styles = None
        self.global_style = {}

    def render_table(self, image=None):
        if not image:
            pass
            # TODO: SELENIUM RENDERING

        super().__init__(image)

        height, width = self.image.shape[:2]
        self.size = (width, height)

