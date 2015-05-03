from pkg_resources import resource_string

from nltk.tokenize.regexp import WordPunctTokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer
from collections import Counter
from collections import deque
from operator import itemgetter
import heapq
import re

from readembedability.utils import most_common


# These are taken from MySQL - http://dev.mysql.com/tech-resources/articles/full-text-revealed.html
# NLTK's stopwords were a joke
STOPWORDS = resource_string('readembedability', 'data/stopwords.txt').strip().split("\n")


class Summarizer:
    def __init__(self, text, title):
        # clean up text a bit - if there are two blank lines consider it a sentence break
        # also, replace multiple newlines and spaces with a single space.
        self.text = re.sub("[\n\ ]+", " ", re.sub("\n\s*\n+", ". ", text))
        self.lower_text = self.text.lower()
        self.title = title
        self.summarize()


    def getCapitalization(self, word):
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
        return most_common(versions)[0]


    def getEntityFromSentence(self, originalcase, words):
        """
        Return array of words ready to join to make original entity - i.e.,
        ['Chief', 'Justice', 'Roberts']
        """
        index = words.index(originalcase)
        entity = deque([originalcase])

        lindex = index - 1
        while lindex > 0 and self.getCapitalization(words[lindex])[0].isupper():
            entity.appendleft(self.getCapitalization(words[lindex]))
            lindex -= 1

        rindex = index + 1
        while rindex < len(words) and self.getCapitalization(words[rindex])[0].isupper():
            entity.append(self.getCapitalization(words[rindex]))
            rindex += 1

        return entity


    def getEntity(self, word, originalcase):
        tokenizer = WordPunctTokenizer()
        for sentence in self.raw_sentences:
            words = tokenizer.tokenize(sentence.strip())
            if originalcase in words:
                entity = self.getEntityFromSentence(originalcase, words)
                if len(entity) > 1:
                    return " ".join(entity)
        return originalcase


    def keywords(self, count=5):
        results = []
        atomresults = []
        for word in map(itemgetter(0), self.boosted.most_common()):
            if word not in atomresults and word.isalnum():
                original = self.getCapitalization(word)
                if word != original:
                    original = self.getEntity(word, original)
                results.append(original)
                if len(results) == count:
                    return results
                atomresults += original.lower().split()
        return results

    def summary(self, max_sentence_count=4, sufficient_word_count=70):
        """
        Stop adding sentences when either max_sentence_count is reached or the # of words is >=
        to sufficient_word_count.
        """
        top = heapq.nlargest(max_sentence_count, self.sentences)
        ss = map(itemgetter(1), sorted(top, key=itemgetter(2)))
        if len(ss) == 0:
            return ""
        result = ss[0]
        for s in ss[1:]:
            if len(result.split(" ")) >= sufficient_word_count:
                return result
            result += " " + s
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
        for word, value in self.words.iteritems():
            self.boosted[word] = value
            if word in self.title_words:
                self.boosted[word] += titular_boost

        # now get a score per sentence, based on location and # of keywords
        freqwords = map(itemgetter(0), self.boosted.most_common(100))
        self.raw_sentences = PunktSentenceTokenizer().tokenize(self.text)
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
    def get_words(klass, text):
        tokenizer = WordPunctTokenizer()
        words = Counter()
        for word in tokenizer.tokenize(text):
            word = word.lower()
            if len(word) > 2 and word not in STOPWORDS:
                words[word] += 1
        return words
