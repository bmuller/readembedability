from collections import Counter
from collections import deque
from operator import itemgetter, methodcaller
import heapq
import re
from pkg_resources import resource_string, resource_filename

from nltk.tokenize.regexp import RegexpTokenizer
import nltk

from readembedability.utils import most_common, unique, longest_unique
from readembedability.parsers.base import BaseParser

# These are taken from MySQL (NLTK's stopwords were a joke):
# http://dev.mysql.com/tech-resources/articles/full-text-revealed.html
_RSTRING = resource_string('readembedability', 'data/stopwords.txt')
STOPWORDS = str(_RSTRING, 'utf-8').strip().split("\n")
_RFNAME = resource_filename('readembedability', 'data/english.pickle')
PUNKT = nltk.data.load(_RFNAME)


class WordPunctTokenizer(RegexpTokenizer):
    """
    Just like:
    http://www.nltk.org/api/nltk.tokenize.html#nltk.tokenize.regexp.WordPunctTokenizer
    except consider a '-' to join parts of a word (like 'Ben-Hur').
    """
    def __init__(self):
        RegexpTokenizer.__init__(self, r'\w+[-\w+]*|[^\w\s]+')


# pylint: disable=too-many-instance-attributes
class Summarizer:
    def __init__(self, text, title):
        # clean up text a bit - if there are two blank lines consider it a
        # sentence break. also, replace multiple newlines and spaces with
        # a single space.
        # pylint: disable=anomalous-backslash-in-string
        self.text = re.sub("[\n\ ]+", " ", re.sub("\n\s*\n+", ". ", text))
        self.lower_text = self.text.lower()
        self.title = title
        self.summarize()

    def common_cap(self, word):
        """
        Get the most common capitalization of this word.
        """
        word = word.lower()
        versions = []
        lindex = self.lower_text.find(word)
        while lindex > -1:
            rindex = lindex + len(word)
            versions.append(self.text[lindex:rindex])
            lindex = self.lower_text.find(word, rindex)
        # possible we've never seen it before
        if not versions:
            return word
        return most_common(versions)[0]

    def get_entity_from_sentence(self, originalcase, words):
        """
        Return array of words ready to join to make original entity - i.e.,
        ['Chief', 'Justice', 'Roberts']
        """
        index = words.index(originalcase)
        entity = deque([originalcase])

        lindex = index - 1
        while lindex > 0 and self.common_cap(words[lindex])[0].isupper():
            entity.appendleft(self.common_cap(words[lindex]))
            lindex -= 1

        rindex = index + 1
        size = len(words)
        while rindex < size and self.common_cap(words[rindex])[0].isupper():
            entity.append(self.common_cap(words[rindex]))
            rindex += 1

        return entity

    def get_entity(self, originalcase):
        tokenizer = WordPunctTokenizer()
        for sentence in self.raw_sentences:
            words = tokenizer.tokenize(sentence.strip())
            if originalcase in words:
                entity = self.get_entity_from_sentence(originalcase, words)
                if len(entity) > 1:
                    return " ".join(entity)
        return originalcase

    def keywords(self, count=5):
        results = []
        atomresults = []
        for word in map(itemgetter(0), self.boosted.most_common()):
            if word not in atomresults and Summarizer.is_word(word):
                original = self.common_cap(word)
                if word != original:
                    # this might actually be an entity
                    original = self.get_entity(original)
                atomresults.append(word)
                results.append(original)
                results = unique(results)
                if len(results) == count:
                    return results
        return results

    def summary(self, max_sentence_count=4, sufficient_word_count=70):
        """
        Stop adding sentences when either max_sentence_count is reached
        or the # of words is >= to sufficient_word_count.
        """
        top = heapq.nlargest(max_sentence_count, self.sentences)
        sentences = [s[1] for s in sorted(top, key=itemgetter(2))]
        if len(sentences) == 0:
            return ""
        result = sentences[0]
        for sentence in sentences[1:]:
            if len(result.split(" ")) >= sufficient_word_count:
                return result
            result += " " + sentence
        return result

    def summarize(self):
        self.sentences = []
        self.words = Summarizer.get_words(self.text)
        self.title_words = set(Summarizer.get_words(self.title).keys())
        self.boosted = Counter()
        if len(self.words) == 0:
            return

        # now boost words based on words in title
        titular_boost = self.words.most_common(1)[0][1] / 2.0
        for word, value in self.words.items():
            self.boosted[word] = value
            if word in self.title_words:
                self.boosted[word] += titular_boost

        # now get a score per sentence, based on location and # of keywords
        freqwords = list(map(itemgetter(0), self.boosted.most_common(100)))
        # pylint: disable=no-member
        self.raw_sentences = PUNKT.tokenize(self.text)
        for index, sentence in enumerate(self.raw_sentences):
            sentence = sentence.strip()
            words = Summarizer.get_words(sentence).keys()
            score = len([word for word in words if word in freqwords])

            # if there are at least 3 words in the sentence, and they're not
            # just a repeat of the title, then keep it around
            if score > 0 and set(words) != self.title_words and len(words) > 3:
                # score is penalized by position
                score -= index
                heapq.heappush(self.sentences, (score, sentence, index))

    @classmethod
    def get_words(cls, text):
        tokenizer = WordPunctTokenizer()
        words = Counter()
        if text is None:
            return words
        for word in tokenizer.tokenize(text):
            word = word.lower()
            if len(word) > 2 and word not in STOPWORDS:
                words[word] += 1
        return words

    @classmethod
    def is_word(cls, text):
        """
        If the text is alpha numeric (excluding '-' chars)
        then return True
        """
        return text.replace('-', '').isalpha()

    @classmethod
    def has_sentence(cls, text):
        text = text.strip()

        # more than one word
        if len(cls.get_words(text)) > 1:
            return True

        # or one word that ends in a period
        if len(text) > 0 and text[-1] in '?!:;.':
            return True

        return False


class SummarizingParser(BaseParser):
    async def enrich(self, result):
        if '_text' not in result:
            if not self.soup:
                return result
            result.set('_text', self.soup.all_text())

        sumzer = Summarizer(result.get('_text'), result.get('title'))
        result.set('wordcount', len(sumzer.words))
        # only set props if there are at least 2 sentances
        if len(sumzer.sentences) > 2:
            summary = sumzer.summary()
            if len(summary) > 0:
                result.set('summary', summary, 3)
            existing = map(sumzer.common_cap, result.get('keywords'))
            keywords = longest_unique(list(existing) + sumzer.keywords())
            result.set('keywords', keywords)
        return result


def parse_authors(value):
    """
    Return an array of author names.  Expect a string.
    """
    value = value.strip()
    if value.lower().startswith('by'):
        value = value[3:].strip()

    if not value:
        return []

    value = value.replace(' AND ', ' and ')
    return list(map(fix_name, value.split(' and ')))


def fix_name(name):
    name = name.strip()
    # if all upcase, then just capitalize
    if name in [name.upper(), name.lower()]:
        parts = map(methodcaller('capitalize'), name.split(' '))
        name = " ".join(parts)
    return name
