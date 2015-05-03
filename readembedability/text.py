from nltk.tokenize.regexp import WordPunctTokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer
from collections import Counter
from collections import deque
from operator import itemgetter
import heapq
import re
import math

from utils import most_common


# These are taken from MySQL - http://dev.mysql.com/tech-resources/articles/full-text-revealed.html
# NLTK's stopwords were a joke
STOPWORDS = "a able about above according accordingly across actually after afterwards again against ain't all allow allows almost alone along already also although always am among amongst an and another any anybody anyhow anyone anything anyway anyways anywhere apart appear appreciate appropriate are aren't around as aside ask asking associated at available away awfully be became because become becomes becoming been before beforehand behind being believe below beside besides best better between beyond both brief but by c'mon c's came can can't cannot cant cause causes certain certainly changes clearly co com come comes concerning consequently consider considering contain containing contains corresponding could couldn't course currently definitely described despite did didn't different do does doesn't doing don't done down downwards during each edu eg eight either else elsewhere enough entirely especially et etc even ever every everybody everyone everything everywhere ex exactly example except far few fifth first five followed following follows for former formerly forth four from further furthermore get gets getting given gives go goes going gone got gotten greetings had hadn't happens hardly has hasn't have haven't having he he's hello help hence her here here's hereafter hereby herein hereupon hers herself hi him himself his hither hopefully how howbeit however i'd i'll i'm i've ie if ignored immediate in inasmuch inc indeed indicate indicated indicates inner insofar instead into inward is isn't it it'd it'll it's its itself just keep keeps kept know knows known last lately later latter latterly least less lest let let's like liked likely little look looking looks ltd mainly many may maybe me mean meanwhile merely might more moreover most mostly much must my myself name namely nd near nearly necessary need needs neither never nevertheless new next nine no nobody non none noone nor normally not nothing novel now nowhere obviously of off often oh ok okay old on once one ones only onto or other others otherwise ought our ours ourselves out outside over overall own particular particularly per perhaps placed please plus possible presumably probably provides que quite qv rather rd re really reasonably regarding regardless regards relatively respectively right said same saw say saying says second secondly see seeing seem seemed seeming seems seen self selves sensible sent serious seriously seven several shall she should shouldn't since six so some somebody somehow someone something sometime sometimes somewhat somewhere soon sorry specified specify specifying still sub such sup sure t's take taken tell tends th than thank thanks thanx that that's thats the their theirs them themselves then thence there there's thereafter thereby therefore therein theres thereupon these they they'd they'll they're they've think third this thorough thoroughly those though three through throughout thru thus to together too took toward towards tried tries truly try trying twice two un under unfortunately unless unlikely until unto up upon us use used useful uses using usually value various very via viz vs want wants was wasn't way we we'd we'll we're we've welcome well went were weren't what what's whatever when whence whenever where where's whereafter whereas whereby wherein whereupon wherever whether which while whither who who's whoever whole whom whose why will willing wish with within without won't wonder would would wouldn't yes yet you you'd you'll you're you've your yours yourself yourselves zero".split(' ')


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
            rindex +=1

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
            if len(word) > 2 and not word in STOPWORDS:
                words[word] += 1
        return words
