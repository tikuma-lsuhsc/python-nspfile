import pytest

from nspfile import read, NSPHeaderDict


def test():
    testfile = "test/addf8.nsp"
    fs, x, hdr, note = read(testfile, return_header=True, return_note=True)
    assert isinstance(fs, int)
    assert len(x) == hdr["length"]

    fs, x, hdr = read(testfile, return_header=True)

    fs, x, note = read(testfile, return_note=True)
    assert not isinstance(note, dict)

    fs, x = read(testfile)

def test_channels():
    testfile = "test/addf8.nsp"
    read(testfile, channels=0)
    read(testfile, channels='a')
    with pytest.raises(ValueError):
        read(testfile, channels=1)
        read(testfile, channels=2)


def test_just_header():
    testfile = "test/addf8.nsp"
    hdr = read(testfile, just_header=True)
    assert set(hdr) == set(NSPHeaderDict.__annotations__)
