import os


def readl(fpath):
    with open(fpath) as fh:
        lst = fh.read().splitlines()
    return lst


def writel(fpath, lst):
    with open(fpath, 'w') as fh:
        for e in lst:
            fh.write(f'{e}\n')


def getbname(fpath):
    return os.path.splitext(os.path.basename(fpath))[0]
