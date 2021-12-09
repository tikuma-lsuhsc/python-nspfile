"""NSP file reader (eventually I/O) module"""

from datetime import datetime
import numpy as np

__version__ = "0.1.1"


def read(filename, channels=None, return_header=False, return_note=False):
    """read an NSP file

    Return the sample rate (in samples/sec) and data from an KayPENTAX CSL NSP audio file.

    :param filename: Input NSP file
    :type filename: str
    :param channels: Specify channels to return ('a', 'b', 0-8, or a sequence thereof), defaults to None
    :type channels: str, int, sequence, optional
    :param return_header: True to return header data, defaults to False
    :type return_header: bool, optional
    :param return_note: True to return note, defaults to False
    :type return_note: bool, optional
    :return:
        - rate   - Sample rate of NSP file.
        - data   - Data read from NSP file. Data is 1-D for 1-channel NSP (only A channel), or 2-D
                   of shape (Nsamples, Nchannels) otherwise. If any channel is missing zeros
                   are returned for that channel. 
        - header - Header data of NSP file with fields: date, rate, length, and max_abs_values
        - note   - Note data of NSP file
    :rtype: (int, numpy.ndarray('i2')[, dict][, str])
    """

    # fmt:off
    subchunk_ids = 'HEDR','HDR8','NOTE','SDA_','SD_B','SDAB','SD_2','SD_3','SD_4','SD_5','SD_6','SD_7','SD_8'
    # fmt:on

    subchunks = {}

    with open(filename, "rb") as f:
        id = f.read(8).decode("utf-8")
        if id != "FORMDS16":
            raise ValueError("Specified file is not a valid .nsp file.")
        sz = int.from_bytes(f.read(4), "little", signed=False)

        n = 0
        while n < sz:
            id = f.read(4).decode("utf-8")
            if id not in subchunk_ids:
                raise ValueError(f"Specified file contains unknown subchunk: {id}")
            ssz = int.from_bytes(f.read(4), "little", signed=False)
            subchunks[id] = (
                np.fromfile(f, "<i2", ssz) if id.startswith("SD") else f.read(ssz)
            )
            if ssz % 2:
                f.seek(1, 1)
                ssz += 1
            n += 8 + ssz

    data = subchunks["HEDR"] or subchunks["HDR8"]

    fs = int.from_bytes(data[20:24], "little", signed=False)  # Sampling rate

    if "SDAB" in subchunks:
        x = subchunks["SDAB"].reshape(-1, 2)
    else:
        cdata = [subchunks[ch] if ch in subchunks else None for ch in ("SDA_", "SD_B")]
        if cdata[1] is None:
            x = cdata[0]
        else:
            z = np.zeros_like(cdata[1]) if cdata[0] is None else None
            cdata[0] = z if z is None else cdata[0]
            x = np.stack(cdata, -1)

    if "HDR8" in subchunks:
        cdata = [
            subchunks[ch] if ch in subchunks else None
            for ch in (f"SD_{ch}" for ch in range(2, 9))
        ]

        # truncate unused upper channels
        nch = next(c for c in range(7, -1, -1) if cdata[c] is not None) + 1

        if nch > 0:
            cdata = cdata[:nch]

            # if filler zeros are not defined, create one
            if z is None:
                z = np.zeros_like(
                    next(x for x in cdata if x is not None) if x is None else x[0]
                )

            y = np.stack([z if x is None else x for x in cdata], -1)

            if x is None:
                # give A & B channels zeros
                x = np.tile(z, (1, 2))
            elif x.ndim == 1:
                # no B channel, assign zeros to it
                x = np.stack((x, np.zeros_like), -1)

            x = np.concatenate((x, y), -1)

    if x is None:
        raise RuntimeError(f'"{filename}" does not contain any data.')

    if channels is not None:
        try:
            channels = [0 if c == "a" else 1 if c == "b" else int(c) for c in channels]
        except:
            try:
                channels = [
                    0 if channels == "a" else 1 if channels == "b" else int(channels)
                ]
            except:
                raise ValueError(
                    'channels must be "a", "b", integer 0 - 8, or a sequence thereof.'
                )

        try:
            if x.ndim > 1:
                x = x[:, channels]
            elif any(channels):
                raise
        except:
            raise ValueError("invalid channels requested.")

    out = [fs, x]

    if return_header:
        out.append(
            {
                "date": datetime.strptime(
                    data[:20].decode("utf-8"), "%b %d %H:%M:%S %Y"
                ),  # Date, e.g. May 26 23:57:43 1995
                "rate": fs,
                "length": int.from_bytes(
                    data[24:28], "little", signed=False
                ),  # Data length (bytes)
                "max_abs_values": np.frombuffer(
                    data[28:], "<u2"
                ),  # Maximum absolute value for channels
            }
        )

    if return_note:
        out.append(subchunks.get("NOTE", b"").decode("utf-8"))

    return tuple(out)
