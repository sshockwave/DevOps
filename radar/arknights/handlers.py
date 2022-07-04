r"""
Handle containers
"""
from pathlib import Path

saver = None

def save_lossless(img, path):
    saver.save_lossless(img, path)

def flip(img):
    from PIL import Image
    return img.transpose(Image.FLIP_TOP_BOTTOM)

def handle_poster(name, obj):
    from decoder import decode_sprite
    save_lossless(flip(decode_sprite(obj)), name)

def handle_avg_char(name, obj):
    data = obj.read()
    assert len(data.component) == 4
    rect, hub, canvas, image = [v['component'].object for v in data.component]
    assert rect.type == 'RectTransform'
    assert canvas.type == 'CanvasRenderer'
    del canvas # useless
    from decoder import decode_avg_char_sprite
    info = decode_avg_char_sprite(hub)
    from decoder import get_image_sprite
    image_sprite = get_image_sprite(image)
    save_loc = Path(name).with_suffix('')
    for g in info:
        base = g[-1]
        base_name = f'face{base["suffix"]}.png'
        for v in g:
            if v['facePos']['x'] < 0 or v['image'].size == base['image'].size:
                assert v['image'].width >= 1024
                save_lossless(flip(v['image']), save_loc / f'face{v["suffix"]}.png')
            else:
                assert v['image'].width <= 400
                delta_name = f'delta/data{v["suffix"]}.png'
                save_lossless(flip(v['image']), save_loc / delta_name)
                with saver.open(save_loc / f'face{v["suffix"]}.svg', 'w') as f:
                    f.write(f'''<?xml version="1.0" standalone="no"?>
<svg viewBox="0 0 {base['image'].width} {base['image'].height}"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink">
    <image xlink:href="./{base_name}" x="0" y="0"
        width="{base['image'].width}"
        height="{base['image'].height}"
        />
    <image xlink:href="./{delta_name}"
        x="{v['facePos']['x']}"
        y="{v['facePos']['y']}"
        width="{v['faceSize']['x']}"
        height="{v['faceSize']['y']}"
        preserveAspectRatio="none"
        />
</svg>
''')
    if image_sprite is not None:
        from decoder import decode_sprite
        flag = False
        for g in info:
            if image_sprite is g[-1]['sprite']:
                flag = True
                break
        if not flag:
            for g in info:
                for v in g:
                    if image_sprite is v['sprite']:
                        flag = True
                        break
                if flag: break
        if not flag:
            image = decode_sprite(image_sprite, search_alpha=True)
            from PIL.ImageChops import invert
            has_alpha = invert(image.getchannel('A')).getbbox() is not None
            for g in info:
                for v in g:
                    cur = v['image']
                    if image.size != cur.size: continue
                    from PIL.ImageChops import difference
                    if has_alpha:
                        diff = difference(image, cur)
                    else:
                        tmp = image.copy()
                        tmp.putalpha(cur.getchannel('A'))
                        diff = difference(tmp.convert('RGBa'), cur.convert('RGBa'))
                    if diff.getbbox() is None:
                        flag = True
                        break
                if flag: break
        assert flag
        if not flag:
            save_lossless(flip(decode_sprite(image_sprite, search_alpha=True)), save_loc / 'image.png')
    else:
        assert hub.type == 'AVGCharacterSpriteHub'

def handle_illust2(name, obj):
    assert obj.type == 'GameObject'
    data = obj.read()
    assert 3 <= len(data.component) <= 5
    rect, canvas, image = [v['component'].object for v in data.component[:3]]
    assert rect.type == 'RectTransform'
    assert canvas.type == 'CanvasRenderer'
    assert image.type == 'Image'
    # Hack since this should be an inconsistency of the asset
    from decoder import decode_image
    image = decode_image(image)
    save_lossless(flip(image), name)

def handle_text(name, obj):
    assert obj.type == 'TextAsset'
    data = obj.read()
    save_loc = Path(name)
    assert save_loc.suffix == '.txt' or save_loc.suffix == '.json'
    with saver.open(name, 'w', encoding='UTF-8') as f:
        f.write(data.script)
