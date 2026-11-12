"""Small, dependency-free, typed Java NBT reader/writer, including region files."""
import struct, gzip, zlib, io, time
from pathlib import Path

def B(v): return (1, v)
def S(v): return (2, v)
def I(v): return (3, v)
def L(v): return (4, v)
def F(v): return (5, v)
def D(v): return (6, v)
def BA(v): return (7, bytes(v))
def T(v): return (8, str(v))
def LS(kind, values): return (9, (kind, values))
def C(v): return (10, v)
def IA(v): return (11, list(v))
def LA(v): return (12, list(v))

def string(v):
    b = v.encode('utf-8'); return struct.pack('>H', len(b))+b

def payload(t, v):
    if t in (1,2,3,4,5,6): return struct.pack({1:'>b',2:'>h',3:'>i',4:'>q',5:'>f',6:'>d'}[t], v)
    if t == 7: return struct.pack('>i',len(v))+v
    if t == 8: return string(v)
    if t == 9:
        k, a=v; return bytes([k])+struct.pack('>i',len(a))+b''.join(payload(k,x) for x in a)
    if t == 10: return b''.join(bytes([k])+string(n)+payload(k,x) for n,(k,x) in v.items())+b'\0'
    if t == 11: return struct.pack('>i',len(v))+b''.join(struct.pack('>i',int(x)) for x in v)
    if t == 12: return struct.pack('>i',len(v))+b''.join(struct.pack('>Q',int(x)&((1<<64)-1)) for x in v)
    raise ValueError(t)

def dumps(root): return b'\x0a\0\0'+payload(10,root)
def save(path, root):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(gzip.compress(dumps(root),mtime=0))

def read_payload(f,t):
    def unpack(fmt): return struct.unpack(fmt,f.read(struct.calcsize(fmt)))[0]
    def st(): return f.read(unpack('>H')).decode('utf-8',errors='replace')
    if t in (1,2,3,4,5,6): return unpack({1:'>b',2:'>h',3:'>i',4:'>q',5:'>f',6:'>d'}[t])
    if t == 7: return f.read(unpack('>i'))
    if t == 8: return st()
    if t == 9:
        k=unpack('>b'); n=unpack('>i'); return k,[read_payload(f,k) for _ in range(n)]
    if t == 10:
        d={}
        while True:
            k=unpack('>b')
            if k==0: return d
            n=st(); d[n]=(k,read_payload(f,k))
    if t in (11,12):
        n=unpack('>i'); return [unpack('>i' if t==11 else '>q') for _ in range(n)]
    raise ValueError(t)

def loads(data):
    f=io.BytesIO(data); assert f.read(1)==b'\x0a'; n=struct.unpack('>H',f.read(2))[0]; f.read(n)
    d=read_payload(f,10); assert f.read()==b''; return d
def load(path): return loads(gzip.decompress(Path(path).read_bytes()))
def plain(v):
    t,v=v
    if t==10: return {k:plain(x) for k,x in v.items()}
    if t==9: return [plain((v[0],x)) for x in v[1]]
    if t==7: return f'<{len(v)} bytes>'
    return v

def read_region(path):
    data=Path(path).read_bytes()
    for idx in range(1024):
        start=int.from_bytes(data[idx*4:idx*4+3],'big')*4096
        count=data[idx*4+3]
        if not start: continue
        size=int.from_bytes(data[start:start+4],'big'); kind=data[start+4]
        assert count*4096>=size+4
        assert kind==2, kind
        yield idx,loads(zlib.decompress(data[start+5:start+4+size]))

def write_region(path, chunks):
    header=bytearray(8192); pieces=[]; offset=2
    for idx, root in sorted(chunks.items()):
        packed=zlib.compress(dumps(root),6); block=struct.pack('>I',len(packed)+1)+b'\x02'+packed
        count=(len(block)+4095)//4096; assert count<256
        header[idx*4:idx*4+4]=offset.to_bytes(3,'big')+bytes([count])
        header[4096+idx*4:4100+idx*4]=struct.pack('>I',int(time.time()))
        pieces.append(block+bytes(count*4096-len(block))); offset+=count
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_bytes(header+b''.join(pieces))
