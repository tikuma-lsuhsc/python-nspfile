"""NSP file reader (eventually I/O) module"""

from __future__ import annotations

from typing import Sequence, TypedDict
from numpy.typing import NDArray

from datetime import datetime
import numpy as np

__version__ = "0.2.0"
__all__ = ["read", "NSPHeaderDict"]


class NSPHeaderDict(TypedDict):
    date: datetime
    """recording date/time"""
    rate: int
    """sampling rate in samples/second
    """
    length: int
    """data length in samples
    """
    max_abs_values: NDArray
    """maximum absolute values of channels
    """


def read(
    filename: str,
    channels: str | int | Sequence[str | int] | None = None,
    return_header: bool = False,
    return_note: bool = False,
    just_header: bool = False,
) -> tuple[int, NDArray, NSPHeaderDict | None, str | None] | NSPHeaderDict:
    """read an NSP file

    Return the sample rate (in samples/sec) and data from an KayPENTAX CSL NSP audio file.

    :param filename: Input NSP file
    :param channels: Specify channels to return ('a', 'b', 0-8, or a sequence thereof), defaults to None
    :param return_header: True to return header data, defaults to False
    :param return_note: True to return note, defaults to False
    :return rate: Sample rate of NSP file (if ``just_header=False``).
    :return data: Data read from NSP file (if ``just_header=False``). Data is 1-D for 1-channel NSP (only A channel), or 2-D
                   of shape (Nsamples, Nchannels) otherwise. If any channel is missing zeros
                   are returned for that channel.
    :return header: Header data of NSP file with fields: date, rate, length, and max_abs_values, only returned
                    if ``return_header=True``.
    :return note: Attached note of NSP file, only returned if ``return_note=True`` and ``just_header=False``.
    """

    # MARKER CHUNKS?
    # case {'MKA_', 'MKB_', 'MKAB'}
    # 	block.length = fread(fid, 1, 'uint32');
    # 	block.pos = fread(fid, 1, 'uint32');
    # 	block.text = char(fread(fid, [1 ceil((block.length - 4) / 2) * 2], 'char'));

    chans: list[int] = []
    if channels is not None:
        if isinstance(channels, (str, int)):
            channels = [channels]
        try:
            chans = [c if isinstance(c, int) else "ab".index(c) for c in channels]
            for c in chans:
                assert c >= 0 and c <= 8
        except (AssertionError, TypeError) as e:
            raise ValueError(
                'channels must be "a", "b", integer 0 - 8, or a sequence thereof.'
            ) from e

    nch = len(chans)

    # fmt:off
    subchunk_ids = 'HEDR','HDR8','NOTE','SDA_','SD_B','SDAB','SD_2','SD_3','SD_4','SD_5','SD_6','SD_7','SD_8'
    # fmt:on

    subchunks: dict[str, bytes] = {}

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
            subchunks[id] = f.read(ssz)
            if ssz % 2:
                f.seek(1, 1)
                ssz += 1
            n += 8 + ssz

            if just_header and id in ("HEDR", "HDR8"):
                # stop reading file if only header info is needed
                break

    hedr = subchunks.pop("HEDR", None) or subchunks.pop("HDR8", None)
    if hedr is None:
        raise RuntimeError(f'"{filename}" is missing the required HEDR/HDR8 subchunk.')

    fs = int.from_bytes(hedr[20:24], "little", signed=False)  # Sampling rate
    ndata = int.from_bytes(hedr[24:28], "little", signed=False)  # number of samples

    if return_header or just_header:
        header: NSPHeaderDict = {
            "date": datetime.strptime(
                hedr[:20].decode("utf-8"), "%b %d %H:%M:%S %Y"
            ),  # Date, e.g. May 26 23:57:43 1995
            "rate": fs,
            "length": ndata,
            "max_abs_values": np.frombuffer(
                hedr[28:], "<u2"
            ),  # Maximum absolute value for channels
        }

        if just_header:
            return header

    note = subchunks.pop("NOTE", b"").decode("utf-8")

    # remaining subchunks are all data

    chunk_chs: dict[str, int | list[int]] = {
        cid: (
            [0, 1]
            if cid == "SDAB"
            else 0 if cid == "SDA_" else 1 if cid == "SD_B" else int(cid[-1])
        )
        for cid in subchunks
    }

    if nch == 0:
        # all channels
        for cid, cch in chunk_chs.items():
            if isinstance(cch, list):  # cid == "SDAB"
                chans.extend(cch)
            else:
                chans.append(cch)
        chans = sorted(chans)
        nch = len(chans)
    else:
        # validate channels
        try:
            for c in chans:
                if c == 0:
                    assert "SDAB" in chunk_chs or "SDA_" in chunk_chs
                elif c == 1:
                    assert "SDAB" in chunk_chs or "SD_B" in chunk_chs
                else:
                    assert f"SD_{c}" in chunk_chs
        except AssertionError as e:
            raise ValueError("Invalid channels specified") from e

    x = np.empty((ndata, nch), "<i2")

    for cid, cch in chunk_chs.items():

        if isinstance(cch, list):  # cid == "SDAB"
            if 0 in chans or 1 in chans:
                data = np.frombuffer(subchunks[cid], "<i2").reshape(-1, 2)
                for i in (0, 1):
                    try:
                        col = chans.index(i)
                    except ValueError:
                        pass  # not requested
                    else:
                        x[:, col] = data[:, i]
        else:
            try:
                col = chans.index(cch)
            except ValueError:
                continue  # not requested
            else:
                x[:, col] = np.frombuffer(subchunks[cid], "<i2")

    out = [fs, x]

    if return_header:
        out.append(header)

    if return_note:
        out.append(note)

    return tuple(out)
