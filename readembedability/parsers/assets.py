import heapq
import operator
import asyncio

from fastimage import detect
from bs4 import BeautifulSoup

from readembedability.utils import unique

from readembedability.parsers.base import BaseParser


class ImageTypeParser(BaseParser):
    """
    If the url was an image, create content.
    """
    async def enrich(self, result):
        if self.response.isImage():
            result.set('content', "<img src='%s' />" % self.url, 3)
            result.set('primary_image', self.url, 3)
            result.set('summary', "", 3)
            result.set('keywords', [], 3)
            result.set('embed', True, 3)
        return result


class PDFTypeParser(BaseParser):
    """
    If the url was an image, create content.
    """
    async def enrich(self, result):
        if self.response.content_type == "application/pdf":
            content = """
            <object data='%s' type='application/pdf'><p>PDF could not be displayed.
            Visit <a href='%s'>%s</a> to download directly.</p></object>
            """
            result.set('content', content % (self.url, self.url, self.url), 3)
            result.set('primary_image', self.url, 3)
            result.set('summary', "", 3)
            result.set('keywords', [], 3)
        return result


class LastDitchMedia(BaseParser):
    def validSource(self, url):
        try:
            host = url.split('//')[1].split('/')[0]
            host = ".".join(host.split('.')[-2:])
            return host.lower() in ['youtube.com', 'vimeo.com', 'youtube-nocookie.com']
        except:
            return False

    async def enrich(self, result):
        if result.get('content') is None or result.get('content').strip() == "" or self.bs is None:
            return result

        # Add in iframes if they're for video
        for iframe in self.bs.find_all('iframe'):
            if 'src' in iframe.attrs and self.validSource(iframe['src']) and not iframe['src'] in result.get('content'):
                result.set('content', str(iframe) + result.get('content'), 3)

        # Take out primary image if present
        if result.get('primary_image') is not None:
            self.bs.delete('img', src=result.get('primary_image'))

        return result


class ImagesParser(BaseParser):
    def __init__(self, response):
        BaseParser.__init__(self, response)
        self.soup = BeautifulSoup(self.content, 'lxml')
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
        if not all([width, height]):
            return False
        
        valid = width >= self.img_min_width and height >= self.img_min_height
        valid = valid and (float(width) / float(height)) < self.img_min_ratio
        return valid and (float(height) / float(width)) < self.img_min_ratio

    async def enrich(self, result):
        # get all images, sort by likelihood of usefulness, then filter by constraints
        images = self.soup.find_all('img', src=True)
        images = self.filterBadChildren(images)
        sources = [self.absoluteify(img['src']) for img in images]
        sources += result.get('_candidate_images', [])
        sources = unique(self.getSocialImageSources() + sources)
        urlsizes = await asyncio.gather(*[self.getImageSize(src) for src in sources])

        images = []
        for url, size in urlsizes:
            if size is not None and self.validImageDims(size[0], size[1]):
                adjsize = 0 if "logo" in url.lower() else (size[0] * size[1])
                heapq.heappush(images, (adjsize, url))
        imgs = map(operator.itemgetter(1), heapq.nlargest(5, images))
        imgs = unique(imgs)
        if len(imgs) > 0:
            result.set('primary_image', imgs[0])
            secondaries = result.get('secondary_images') + imgs[1:]
            # make sure we don't include primary in the secondary
            secondaries = [img for img in secondaries if img != result.get('primary_image')]
            result.set('secondary_images', secondaries)
        return result
        
    def getSocialImageSources(self):
        metas = self.soup.find_all("meta", property="og:image", content=True)
        images = [m['content'] for m in metas]
        for meta in self.soup.find_all("meta", content=True):
            if meta.get('name') is not None and meta['name'].startswith("twitter:image"):
                images.append(meta['content'])
        return [ self.absoluteify(image) for image in images ]

    async def getImageSize(self, url):
        size = await detect.get_size(url)
        return (url, size)
