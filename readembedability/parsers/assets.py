import heapq
import asyncio

from fastimage import detect

from readembedability.utils import unique, URL
from readembedability.parsers.base import BaseParser

VIDEO_HOSTS = ['youtube.com', 'vimeo.com', 'youtube-nocookie.com']
PDF_CONTENT = """
<object data='%s' type='application/pdf'><p>PDF could not be displayed.
Visit <a href='%s'>%s</a> to download directly.</p></object>
"""
MIN_IMG_HEIGHT = 40
MIN_IMG_WIDTH = 400
MIN_IMG_RATIO = 3.0


class ImageTypeParser(BaseParser):
    """
    If the url was an image, create content.
    """
    async def enrich(self, result):
        if self.response.is_image():
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
        if self.response.is_pdf():
            content = PDF_CONTENT % (self.url, self.url, self.url)
            result.set('content', content, 3)
            result.set('primary_image', self.url, 3)
            result.set('summary', "", 3)
            result.set('keywords', [], 3)
        return result


class LastDitchMedia(BaseParser):
    async def enrich(self, result):
        if not result.has('content') or self.soup is None:
            return result

        # Add in iframes if they're for video
        for iframe in self.soup.find_all('iframe'):
            if 'src' in iframe.attrs:
                valid_source = URL(iframe['src']).top_host in VIDEO_HOSTS
                if valid_source and not iframe['src'] in result.get('content'):
                    content = str(iframe) + result.get('content')
                    result.set('content', content, 3)

        # Take out primary image if present
        if result.get('primary_image') is not None:
            self.soup.delete('img', src=result.get('primary_image'))

        return result


class ImagesParser(BaseParser):
    def get_images(self):
        images = []
        for image in self.soup.find_all('img', src=True):
            badids = ["sidebar", "comment", "footer", "header"]
            badparents = [image.find_parents(id=id, limit=1) for id in badids]
            if sum(map(len, badparents)) == 0:
                url = image['src']
                if not url.startswith('data:image'):
                    url = self.absoluteify(url)
                    images.append(url)
        return images

    @classmethod
    def valid_dims(cls, width, height):
        if not all([width, height]):
            return False
        valid = width >= MIN_IMG_WIDTH and height >= MIN_IMG_HEIGHT
        valid = valid and (float(width) / float(height)) < MIN_IMG_RATIO
        return valid and (float(height) / float(width)) < MIN_IMG_RATIO

    async def enrich(self, result):
        """
        get all images, sort by likelihood of usefulness, then filter by
        constraints of size.
        """
        if self.soup is None:
            return result

        sources = self.get_images() + result.get('_candidate_images', [])
        social = self.get_social_images()
        sources += social
        largest = await self.get_best(unique(sources), 5)
        if not largest:
            return result

        # use good social image if present, else just use biggest
        bestsocial = list(set(social) & set(largest))
        primary = bestsocial[0] if bestsocial else largest[0]
        result.set('primary_image', primary)
        largest.remove(primary)
        secondaries = largest

        # make sure we don't include primary in the secondary
        prim = URL(result.get('primary_image')).basename
        seconds = [img for img in secondaries if URL(img).basename != prim]
        result.set('secondary_images', seconds)
        return result

    async def get_best(self, sources, count):
        """
        Get the best count images from list of sources.  If an image
        is in the bump list (i.e., the social images) then give it
        a boost.
        """
        # get first 100 images that don't have "pixel" in the url
        sources = [s for s in sources if 'pixel' not in s][:100]
        urlsizes = await asyncio.gather(*map(self.get_image_size, sources))
        images = []
        for url, size in urlsizes:
            if size is not None and ImagesParser.valid_dims(size[0], size[1]):
                # downgrade logos
                adjsize = 0 if "logo" in url.lower() else (size[0] * size[1])
                heapq.heappush(images, (adjsize, url))
        return [i[1] for i in heapq.nlargest(count, images)]

    def get_social_images(self):
        metas = self.soup.find_all("meta", property="og:image", content=True)
        images = [m['content'] for m in metas]
        for meta in self.soup.find_all("meta", content=True):
            mname = "" if meta.get('name') is None else meta['name']
            if mname.startswith("twitter:image"):
                images.append(meta['content'])
        return list(map(self.absoluteify, images))

    async def get_image_size(self, url):
        try:
            size = await detect.get_size(url)
        except detect.DownloadError:
            size = None
        return (url, size)
