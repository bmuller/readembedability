import json
from bs4 import BeautifulSoup

from readembedability.parsers.base import BaseParser
from readembedability.io import get_page


class OEmbedParser(BaseParser):
    async def enrich(self, result):
        if self.soup is None:
            return result

        oembed = await get_embed_from_content(self.response.body)
        if oembed is None:
            return result

        if 'author_name' in oembed:
            result.set('authors', [oembed['author_name']], 3)

        result.set_if('title', oembed.get('title'))
        result.set_if('primary_image', oembed.get('thumbnail_url'))

        # Don't trust oembed articles because they're probably crap, like
        # NYTimes oembeded articles that are just iframes
        isarticle = oembed.get('asset_type', '').lower() != 'article'
        if 'html' in oembed and isarticle:
            # if this is a wordpress embed, then let's not call it
            # embedded and use the actual content
            if "Embedded WordPress Post" not in oembed['html']:
                result.set('embed', True)
                # only lock if the html field actually contains html
                lock = ">" in oembed['html'] and "<" in oembed['html']
                conf = 3 if lock else 2
                result.set('content', oembed['html'], conf)

        elif 'url' in oembed and oembed['type'] == 'photo':
            result.set('embed', True)
            result.set('content', "<img src='%s' />" % oembed['url'], 3)
            result.set('title', oembed.get('title', result.get('title')))
            result.set('primary_image', oembed['url'], 3)

        return result


def _parse_xml(xml):
    result = {}
    # bs4 can't handle a html child elem
    xml = xml.replace('<html>', '<content>')
    xml = xml.replace('</html>', '</content>')
    doc = BeautifulSoup(xml, "html.parser")
    for kid in doc.oembed.children:
        name = kid.name if kid.name != 'content' else 'html'
        result[name] = kid.text
    return result


def _parse_json(jsonstr):
    try:
        return json.loads(jsonstr)
    except ValueError:
        return None


async def get_embed_from_content(page):
    if page is None or len(page) < 10:
        return None
    soup = BeautifulSoup(page, "html.parser")
    types = ('application/json+oembed', 'text/xml+oembed')
    link = soup.find('link', type=types, href=True)
    if link and link['type'] == 'application/json+oembed':
        parser = _parse_json
    elif link:
        parser = _parse_xml
    else:
        return None
    page = await get_page(link['href'])
    return parser(page.body) if page else None
