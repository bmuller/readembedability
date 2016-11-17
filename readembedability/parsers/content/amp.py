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

        href = self.absoluteify(links[0]['href'])
        response = await get_page(href, mobile=True)
        if not response:
            return result
        return AMPParser(response).amp_enrich(result)

    def amp_enrich(self, result):
        if not self.soup:
            return result

        elems = self.soup.find_all('amp-img', src=True)
        imgs = [self.absoluteify(i['src']) for i in elems]
        if imgs:
            # amp images are really good recommendations
            result.set('_candidate_images', imgs, 2)
        # it's possible that an amp article could appear in sections
        # other than these. ideally, should allow any elems, maybe use
        # newspaper parser over the full html
        elems = self.soup.find_all('article') + self.soup.find_all('section')
        content = " ".join(map(str, elems)).strip()
        if content:
            result.set('content', sanitize_html(content), 1)
        return result
