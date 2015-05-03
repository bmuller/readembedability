from readembedability.page import ReadabedPage

version_info = (0, 1)
version = '.'.join(map(str, version_info))


def getReadembedable(url):
    return ReadabedPage(url).fetch()
