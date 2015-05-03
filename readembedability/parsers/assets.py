import heapq
import operator

import fastimage
from bs4 import BeautifulSoup

from readembedability.utils import unique

from twisted.internet import defer

from readembedability.parsers.base import BaseParser


class ImageTypeParser(BaseParser):
    """
    If the url was an image, create content.
    """
    def enrich(self, result):
        if self.response.isImage():
            result.set('content', "<img src='%s' />" % self.url, lock=True)
            result.set('primary_image', self.url, lock=True)
            result.set('summary', "", lock=True)
            result.set('keywords', [], lock=True)
            result.set('embed', True, lock=True)
        return defer.succeed(result)


class PDFTypeParser(BaseParser):
    """
    If the url was an image, create content.
    """
    def enrich(self, result):
        if self.response.content_type == "application/pdf":
            content = """
            <object data='%s' type='application/pdf'><p><p>PDF could not be displayed.
            Visit <a href='%s'>%s</a> to download directly.</p></object>
            """
            result.set('content', content % (self.url, self.url, self.url), lock=True)
            result.set('primary_image', self.url, lock=True)
            result.set('summary', "", lock=True)
            result.set('keywords', [], lock=True)
        return defer.succeed(result)


class LastDitchMedia(BaseParser):
    def validSource(self, url):
        try:
            host = url.split('//')[1].split('/')[0]
            host = ".".join(host.split('.')[-2:])
            return host.lower() in ['youtube.com', 'vimeo.com', 'youtube-nocookie.com']
        except:
            return False

    def enrich(self, result):
        if result.get('content') is None or result.get('content').strip() == "" or self.bs is None:
            return result

        # Add in iframes if they're for video
        for iframe in self.bs.find_all('iframe'):
            if 'src' in iframe.attrs and self.validSource(iframe['src']) and not iframe['src'] in result.get('content'):
                result.set('content', str(iframe) + result.get('content'), overwrite=True)

        # Take out primary image if present
        if result.get('primary_image') is not None:
            self.bs.delete('img', src=result.get('primary_image'))

        return result


class ImagesParser(BaseParser):
    def __init__(self, response):
        BaseParser.__init__(self, response)
        self.soup = BeautifulSoup(self.content)
        self.img_min_height = 40
        self.img_min_width = 400
        self.img_min_ratio = 3.0

    def filterBadChildren(self, elems):
        images = []
        for image in elems:
            badids = [ "sidebar", "comment", "footer", "header" ]
            badparents = [ len(image.find_parents(id=id, limit=1)) for id in badids ]
            if sum(badparents) == 0 and len(image['src']) > 5:
                images.append(image)
        return images

    def validImageDims(self, width, height):
        valid = True
        valid = valid and width >= self.img_min_width and height >= self.img_min_height
        valid = valid and (float(width) / float(height)) < self.img_min_ratio
        return valid and (float(height) / float(width)) < self.img_min_ratio

    def filterSizeAttributes(self, elems):
        images = []
        for image in elems:
            if image.get('width') is not None and image.get('height') is not None:
                try:
                    if self.validImageDims(int(image['width']), int(image['height'])):
                        images.append(image)
                except:
                    pass
            else:
                images.append(image)
        return images

    def enrich(self, result):
        def handleSizes(urlssizes):
            images = []
            for url, size in urlssizes:
                if size is not None and self.validImageDims(size[0], size[1]):
                    adjsize = 0 if "logo" in url.lower() else (size[0] * size[1])
                    heapq.heappush(images, (adjsize, url))
            imgs = map(operator.itemgetter(1), heapq.nlargest(5, images))
            imgs = unique(imgs)
            if len(imgs) > 0:
                result.set('primary_image', imgs[0])
                result.set('secondary_images', result.get('secondary_images') + imgs[1:])
            return result

        # get all images, sort by likelihood of usefulness, then filter by constraints
        images = self.soup.find_all('img', src=True)
        images = self.filterBadChildren(images)
        images = self.filterSizeAttributes(images)
        sources = [ self.absoluteify(img['src']) for img in images ]
        sources = unique(self.getSocialImageSources() + sources)
        d = defer.gatherResults([self.getImageSize(src) for src in sources])
        return d.addCallback(handleSizes)

    def getSocialImageSources(self):
        metas = self.soup.find_all("meta", property="og:image", content=True)
        images = map(operator.itemgetter('content'), metas)
        for meta in self.soup.find_all("meta", content=True):
            if meta.get('name') is not None and meta['name'].startswith("twitter:image"):
                images.append(meta['content'])
        return [ self.absoluteify(image) for image in images ]

    def getImageSize(self, url):
        d = fastimage.get_size(url)
        return d.addCallback(lambda s: (url, s))
