

def readl(fpath):
    with open(fpath) as fh:
        lst = fh.read().splitlines()
    return lst