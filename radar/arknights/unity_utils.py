def find_obj(ab, obj_type):
    res = []
    for asset in ab.assets:
        for path_id, obj in asset.objects.items():
            if obj.type == obj_type:
                res.append(obj)
    return res

def find_one_obj(ab, obj_type):
    res = find_obj(ab, obj_type)
    assert len(res) == 1
    return res[0]

def get_ab_containers(bundle):
    ab = find_one_obj(bundle, 'AssetBundle')
    assert ab.path_id == 1
    ab_data = ab.read()
    return {name: val['asset'].object for name, val in ab_data['m_Container']}
