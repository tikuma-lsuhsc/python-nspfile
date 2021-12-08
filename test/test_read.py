from nspfile import read

def test():
    nspfile = "test/addf8.nsp"

    fs, x, hdr, note = read(nspfile, return_header=True, return_note=True)

    print(fs, hdr, note)

    # from matplotlib import pyplot as plt

    # plt.plot(x)
    # plt.show()
