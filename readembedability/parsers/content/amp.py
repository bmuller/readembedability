from readembedability.parsers.html import sanitize_html
from readembedability.parsers.base import BaseParser
from readembedability.io import get_page


class AMPParser(BaseParser):
    async def enrich(self, result):
        if not self.soup:
            return result

        links = self.soup.find_all("link", rel="amphtml", href=True)
        if not links:
            return result

        response = await get_page(links[0]['href'], mobile=True)
        return AMPParser(response).amp_enrich(result)

    def amp_enrich(self, result):
        if not self.soup:
            return result

        elems = self.soup.find_all('amp-img', src=True)
        imgs = [self.absoluteify(i['src']) for i in elems]
        if imgs:
            # amp images are really good recommendations
            result.set('_candidate_images', imgs, 2)
        articles = self.soup.find_all('article')
        if articles:
            result.set('content', sanitize_html(str(articles[0])), 2)
        return result
