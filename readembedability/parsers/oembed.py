from debmeo import discover

from readembedability.parsers.base import BaseParser


class OEmbedParser(BaseParser):
    def enrich(self, result):
        d = discover.Fetcher(self.url).extract_link(self.response)
        return d.addCallback(self.handleParse, result)

    def handleParse(self, oembed, result):
        if oembed is None:
            return result

        if 'author_name' in oembed:
            result.set('author', oembed['author_name'], True)

        if 'html' in oembed:
            result.set('embed', True)
            # only lock if the html field actually contains html
            lock = ">" in oembed['html'] and "<" in oembed['html']
            result.set('content', oembed['html'], lock=lock)
            result.set('title', oembed.get('title', result.get('title')))
            if oembed.get('thumbnail_url', None) is not None:
                result.set('primary_image', oembed.get('thumbnail_url'))

        elif 'url' in oembed and oembed['type'] == 'photo':
            result.set('embed', True)
            result.set('content', "<img src='%s' />" % oembed['url'], lock=True)
            result.set('title', oembed.get('title', result.get('title')))
            result.set('primary_image', oembed['url'], lock=True)

        return result
