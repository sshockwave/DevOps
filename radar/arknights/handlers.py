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
        base = None
        for v in reversed(g):
            if base is None or v['facePos']['x'] < 0 or v['image'].size == base['image'].size:
                assert v['image'].width >= 1024
                save_lossless(flip(v['image']), save_loc / f'face{v["suffix"]}.jxl')
                base = v
                base_name = f'face{base["suffix"]}.jxl'
            else:
                assert v['image'].width <= 400
                delta_name = f'delta/data{v["suffix"]}.jxl'
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

def handle_dynchar(name, obj):
    name = Path(name)
    assert obj.type == 'GameObject'
    obj = [t['component'].object for t in obj.read().component]
    assert [
        'Transform',
        'MeshFilter',
        'MeshRenderer',
        'SkeletonAnimation',
        'DynIllust',
    ] == [v.type for v in obj]
    dynillust = obj[4].read()
    skel_ani = dynillust['_skeleton'].object
    assert skel_ani.type == 'SkeletonAnimation'
    skel_ani = skel_ani.read()['skeletonDataAsset'].object
    assert skel_ani.type == 'SkeletonDataAsset'
    skel_ani = skel_ani.read()
    skel_json = skel_ani['skeletonJSON'].object
    assert skel_json.type == 'TextAsset'
    skel_json = skel_json.read()
    with saver.open(name.with_name(skel_json.name), 'wb') as f:
        f.write(skel_json.script)
    atlas, = skel_ani['atlasAssets']
    atlas = atlas.object
    assert atlas.type == 'SpineAtlasAsset'
    atlas = atlas.read()
    atlas_file = atlas['atlasFile'].object
    assert atlas_file.type == 'TextAsset'
    atlas_file = atlas_file.read()
    with saver.open(name.with_name(atlas_file.name), 'w') as f:
        f.write(atlas_file.script)
    materials = atlas['materials']
    for v in materials:
        atlas_mat = v.object
        from decoder import decode_material
        img = decode_material(atlas_mat)
        tex = atlas_mat.read().saved_properties['m_TexEnvs']['_MainTex']['m_Texture'].object
        assert tex.type == 'Texture2D'
        img_path = name.with_name(tex.read().name).with_suffix('.png')
        # This is referenced from .atlas file so filename cannot be changed
        saver.save_lossless(flip(img), img_path, preserve_suffix=True)
