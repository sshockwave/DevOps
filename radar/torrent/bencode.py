from typing import List

class BTFailure(Exception):
    pass

def decode_int(x, f):
    f += 1
    newf = x.index(b'e', f)
    n = int(x[f:newf])
    if x[f] == ord('-'):
        if x[f + 1] == ord('0'):
            raise ValueError
    elif x[f] == ord('0') and newf != f+1:
        raise ValueError
    return (n, newf+1)

def decode_string(x, f):
    colon = x.index(b':', f)
    n = int(x[f:colon])
    if x[f] == ord('0') and colon != f+1:
        raise ValueError
    colon += 1
    def try_decode(s):
        try:
            return s.decode('utf-8')
        except:
            return s
    return (try_decode(x[colon:colon+n]), colon+n)

def decode_list(x, f):
    r, f = [], f + 1
    while x[f] != ord('e'):
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return (r, f + 1)

def decode_dict(x, f):
    r, f = {}, f+1
    while x[f] != ord('e'):
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return (r, f + 1)

decode_func = dict()
decode_func['l'] = decode_list
decode_func['d'] = decode_dict
decode_func['i'] = decode_int
decode_func.update({str(i): decode_string for i in range(10)})
decode_func = {ord(k): v for k, v in decode_func.items()}

def bdecode(x: bytes):
    r, l = decode_func[x[0]](x, 0)
    assert l == len(x), "invalid bencoded value (data after valid prefix)"
    return r

def encode_int(x: int, r: List[bytes]):
    r += b'i', str(x).encode('utf-8'), b'e'

def encode_bool(x: bool, r: List[bytes]):
    encode_int(int(x), r)

def encode_string(x: str, r: List[bytes]):
    encode_bytes(x.encode('utf-8'), r)

def encode_list(x: list, r: List[bytes]):
    r.append(b'l')
    for i in x:
        encode_any(i, r)
    r.append(b'e')

def encode_dict(x: dict, r: List[bytes]):
    r.append(b'd')
    ilist = list(x.items())
    ilist.sort()
    for k, v in ilist:
        encode_string(k, r)
        encode_any(v, r)
    r.append(b'e')

def encode_bytes(x: bytes, r: List[bytes]):
    r += str(len(x)).encode('utf-8'), b':', x

def encode_any(x, r: List[bytes]):
    encode_func[type(x)](x, r)

encode_func = {
    int: encode_int,
    str: encode_string,
    list: encode_list,
    tuple: encode_list,
    dict: encode_dict,
    bool: encode_bool,
    bytes: encode_bytes,
}

def bencode(x):
    r = []
    encode_any(x, r)
    return b''.join(r)
