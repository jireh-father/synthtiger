def add_styles(target_styles, new_styles):
    for selector in new_styles:
        for style_key in new_styles[selector]:
            target_styles[selector][style_key] = new_styles[selector][style_key]
