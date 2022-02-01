from tkinter.messagebox import NO
import qrcode
import sys


def main():
    fout = None
    get = None
    for i in sys.argv:
        if '--out=' in i:
            fout = i.split('=', 1)[1]
        if '--in=' in i:
            get = i.split('=', 1)[1]
    if fout is None or get is None:
        return
    q = qrcode.QRCode()
    q.add_data(get)
    q.make()
    i = q.make_image()
    with open(fout, 'wb') as f:
        i.save(f)


if __name__ == '__main__':
    main()
