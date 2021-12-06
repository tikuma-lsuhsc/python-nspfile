from math import ceil
from datetime import datetime
import numpy as np

__version__ = "1.0.0"

nspfile = 'test/addf8.nsp'

with open(nspfile,'rb') as f:
    id = f.read(8).decode('utf-8')
    if id!="FORMDS16":
        raise ValueError("Specified file is not a valid .nsp file.")
    sz = int.from_bytes(f.read(4),'little',signed=False)
    data = f.read(sz)

subchunk_ids = 'HEDR','HDR8','NOTE','SDA_','SD_B','SDAB','SD_2','SD_3','SD_4','SD_5','SD_6','SD_7','SD_8'

subchunks = {}

n = 0
while n<sz:
    n1 = n+4
    id = data[n:n1].decode('utf-8')
    if id not in subchunk_ids:
        raise ValueError(f"Specified file contains unknown subchunk: {id}")
    n2 = n1 + 4
    ssz = int.from_bytes(data[n1:n2],'little',signed=False)
    subchunks[id] = data[n2:n2+ssz]
    n = n2 + int(ceil(ssz/2))*2

header = {}
data = subchunks['HEDR'] or subchunks["HDR8"]

mtime =datetime.strptime(data[:20].decode('utf-8'), '%b %d %H:%M:%S %Y') # Date, e.g. May 26 23:57:43 1995
fs = int.from_bytes(data[20:24],'little',signed=False)	#Sampling rate
len = int.from_bytes(data[24:28],'little',signed=False)	# Data length (bytes)

dtype = np.uint16.newbyteorder('<')
amax = np.frombuffer(data[28:],dtype) # Maximum absolute value for channels
amax[amax==65535] = np.nan

note = subchunks.get('NOTE',b"").decode('utf-8')

if 'SDAB' in subchunks:
    x = np.frombuffer(subchunks['SDAB'],dtype).reshape(-1,2)
else:
    cdata = [np.frombuffer(subchunks[ch],dtype) if ch in subchunks else None for ch in ('SDA_','SD_B')]
    if cdata[1] is None:
        x = cdata[0]
    else:
        cdata[0] = np.zeros_like(cdata[1]) if cdata[0] is None else cdata[0]
        x = np.stack(cdata)


# nch = len(amax)
# cdata = [np.frombuffer(subchunks[ch],dtype) if 'SDA_' in subchunks else None for ch in 'SD_2','SD_3','SD_4','SD_5','SD_6','SD_7','SD_8']


print(mtime,fs,len,amax,note)
