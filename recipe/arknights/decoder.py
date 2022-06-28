r"""
Handle objects
"""

def has_alpha_channel(a):
    from PIL.ImageChops import invert
    return invert(a.getchannel('A')).getbbox() is not None

def same_image(a, b, use_alpha=None):
    if a.size != b.size: return False
    if use_alpha is not None:
        def work(x):
            x = x.copy()
            x.putalpha(use_alpha)
            return x.convert('RGBa')
        a, b = work(a), work(b)
    from PIL.ImageChops import difference
    return difference(a, b).getbbox() is None

def decode_texture2d(obj):
    assert obj.type == 'Texture2D'
    data = obj.read()
    import texture2ddecoder as t2d
    # https://github.com/Perfare/AssetStudio/blob/master/AssetStudioUtility/Texture2DConverter.cs
    # https://github.com/K0lb3/texture2ddecoder
    fmt = type(data.format)
    if data.format == fmt.ETC_RGB4:
        decoded_data = t2d.decode_etc1(data.image_data, data.width, data.height)
    elif data.format == fmt.ETC2_RGBA8:
        decoded_data = t2d.decode_etc2a8(data.image_data, data.width, data.height)
    elif data.format == fmt.RGB24:
        decoded_data = []
        for i in range(data.width * data.height):
            decoded_data.append(data.image_data[i * 3 + 2]) # B
            decoded_data.append(data.image_data[i * 3 + 1]) # G
            decoded_data.append(data.image_data[i * 3 + 0]) # R
            decoded_data.append(255) # A
        decoded_data = bytes(decoded_data)
    else:
        raise NotImplementedError
    from PIL import Image
    return Image.frombytes("RGBA", (data.width, data.height), decoded_data, 'raw', ("BGRA"))

def mix_alpha(main, alpha):
    if alpha is None: return
    if alpha.size != main.size:
        for i in range(len(alpha.size)):
            assert alpha.size[i] < main.size[i]
        from PIL import Image
        alpha = alpha.resize(main.size, resample=Image.BILINEAR)
    main.putalpha(alpha.convert('L'))

def decode_material(obj):
    assert obj.type == 'Material'
    mat_data = obj.read()
    mat_prop = mat_data.saved_properties
    texenv = mat_prop['m_TexEnvs']
    def get_image(obj):
        assert obj['m_Scale']['x'] == 1.0
        assert obj['m_Scale']['y'] == 1.0
        assert obj['m_Offset']['x'] == 0.0
        assert obj['m_Offset']['y'] == 0.0
        pptr = obj['m_Texture']
        return pptr and decode_texture2d(pptr.object)
    main = get_image(texenv['_MainTex'])
    if main is None: return
    if '_AlphaTex' in texenv:
        mix_alpha(main, get_image(texenv['_AlphaTex']))
    assert texenv.get('_SoftMask', dict()).get('m_Texture') is None
    return main

def get_name(data):
    if hasattr(data, '_obj'):
        return data._obj.get('m_Name')
    if hasattr(data, 'name'):
        return data.name

def decode_sprite(obj, search_alpha=False):
    assert obj.type == 'Sprite'
    data = obj.read()
    assert not data._obj['m_IsPolygon']
    main = data.rd['texture'].object
    alpha = data.rd['alphaTexture']
    if alpha is not None:
        alpha = alpha.object
    elif search_alpha:
        # Search inside the asset bundle
        # This is a hack, but I really couldn't find
        # where the alpha texture is referenced
        res = []
        alpha_name = get_name(main.read()) + '[alpha]'
        for o in obj.asset.objects.values():
            t = o.read()
            if get_name(t) == alpha_name:
                res.append(o)
        assert len(res) <= 1
        if len(res) == 1:
            alpha, = res
    main = decode_texture2d(main)
    if alpha is not None:
        mix_alpha(main, decode_texture2d(alpha))
    rect = data.rd['textureRect']
    left, upper = rect['x'], rect['y']
    right, lower = left + rect['width'], upper + rect['height']
    main = main.crop((left, upper, right, lower))
    return main

def get_image_sprite(obj):
    assert obj.type == 'Image'
    data = obj.read()
    assert list(data['m_Color'].items()) == [('r', 1.0), ('g', 1.0), ('b', 1.0), ('a', 1.0)]
    if data.get('m_Sprite') is None: return
    return data['m_Sprite'].object

def decode_image(obj):
    assert obj.type == 'Image'
    data = obj.read()
    assert list(data['m_Color'].items()) == [('r', 1.0), ('g', 1.0), ('b', 1.0), ('a', 1.0)]
    sprite = data['m_Sprite'].object
    if sprite is not None:
        sprite_image = decode_sprite(sprite)
    if data['m_Material'] is not None:
        mat = data['m_Material'].object
        test = sprite.read().rd['texture'].object == mat.read().saved_properties['m_TexEnvs']['_MainTex']['m_Texture'].object
        mat_image = decode_material(mat)
        if not test:
            test = same_image(sprite_image, mat_image, mat_image.getchannel('A'))
        if not test:
            assert mat_image.size == (1024, 1024)
            assert sprite_image.size == (2048, 2048)
            mix_alpha(sprite_image, mat_image.getchannel('A'))
            return sprite_image
        assert test
        return mat_image
    return sprite_image

def decode_avg_char_sprite(obj):
    data = obj.read()
    assert data['m_Enabled'] == 1
    def d_face(f, oput):
        if f['alias'] != '':
            oput['suffix'] += '_' + f['alias'].replace('/', '-')
        oput['isWholeBody'] = bool(f['isWholeBody'])
        oput['sprite'] = f['sprite'].object
        main = decode_sprite(oput['sprite'])
        mix_alpha(main, decode_texture2d(f['alphaTex'].object))
        oput['image'] = main
        return oput
    def d_group(g, oput):
        ans = []
        for i, f in enumerate(g['sprites']):
            o = oput.copy()
            o['facePos'] = g.get('facePos') or g.get('FacePos')
            o['faceSize'] = g.get('faceSize') or g.get('FaceSize')
            o['suffix'] += f'_{i}'
            ans.append(d_face(f, o))
        return ans
    ret = []
    if obj.type == 'AVGCharacterSpriteHub':
        ret.append(d_group(data, {'suffix': ''}))
    elif obj.type == 'AVGCharacterSpriteHubGroup':
        for i, g in enumerate(data['spriteGroups']):
            ret.append(d_group(g, {'suffix': f'_g{i}'}))
    else:
        assert False
    return ret

def decode_image_special(obj):
    assert obj.type == 'Image'
    image_data = obj.read()
    assert list(image_data['m_Color'].items()) == [('r', 1.0), ('g', 1.0), ('b', 1.0), ('a', 1.0)]
    sprite = image_data['m_Sprite'].object
    from decoder import decode_sprite, decode_material
    sprite_image = decode_sprite(sprite)
    mat_image = decode_material(image_data['m_Material'].object)
    assert sprite_image.size == (2048, 2048)
    assert mat_image.size == (1024, 1024)
    from decoder import mix_alpha
    mix_alpha(sprite_image, mat_image.getchannel('A'))
    return sprite_image
