from collections import Counter
from glob import glob
from itertools import product
import math

def read_dictionary(filename='AllQueryTerms'):
    with open(filename,'r') as f:
        lines = f.readlines()
        lines = map(lambda l : l.rstrip(), lines)
        lines.sort()
        word_id = 0
        dictionary = dict()
        for w in lines:
            dictionary[w] = word_id
            word_id += 1
        return dictionary

def read_corpus(glob_path = 'data/*/*'):
    term_counts = Counter()
    doc_counts = 0
    length = 0
    for filename in glob(glob_path):
        doc_words = set()
        with open(filename,'r') as f:
            doc_counts += 1
            l = f.readline().rstrip()
            length += len(l.split())
            for t in l.split():
                if t not in doc_words:
                    term_counts[t] += 1
                    doc_words.add(t)
                
    term_counts["#TOTAL#"] = doc_counts
    term_counts["#AVGLEN"] = float(length)/doc_counts    
    return term_counts

def parse_query(query, dictionary, corpus):
    qv = [0] * len(dictionary)
    total = corpus["#TOTAL#"]
    for t in query.split():
        if t in dictionary:
            t_idx = dictionary[t]
            qv[t_idx] = math.log((total + 1.0) / (corpus[t] + 1.0))
        else:
            qv[t_idx] = math.log((total + 1.0) / 1.0)
    return qv

def normalized_raw_term_scores(prepared_doc, dictionary):
    term_counts, length = prepared_doc
    term_scores = [0] * len(dictionary)
    for t in term_counts:
        term_scores[dictionary[t]] = term_counts[t]
    if length == 0:
        return term_scores
    else:
        return map(lambda v : v/float(length), term_scores)           


def sublinear_term_scores(prepared_doc, dictionary):
    term_counts, length = prepared_doc
    term_scores = [0] * len(dictionary)
    for t in term_counts:
        term_scores[dictionary[t]] = math.log(term_counts[t]) + 1
    return term_scores

def filter_array(arr, low, up):
    res = []
    for a in arr:
        if a >= low and a <= up:
            res.append(a)
    return res
class Query():
    def __init__(self):
        # query
        self.query_terms = ""
        # URL objects go here
        self.query_results = []
class URL():
    def __init__(self):
        self.url = ""
        self.title = ""
        # [["term", loc1, loc2, ...], ...]
        self.body_hits = []
        self.body_length = 0
        # ["anchor1", "anchor2", ...]
        self.anchor_text = []
        # [anchor1_count, anchor2_count, ...]
        self.anchor_counts = []    
    def prepare_title(self, dictionary):
        term_counts = Counter()
        for w in self.title.split():
            if w in dictionary:
                term_counts[w] += 1
        return (term_counts, len(self.title.split()))
    def prepare_anchors(self, dictionary):
        term_counts = Counter()
        word_count = 0
        for (anchor,c) in zip(self.anchor_text, self.anchor_counts):
            for w in anchor.split():
                word_count += c
                if w in dictionary:
                    term_counts[w] += c
        return (term_counts, word_count)
    def prepare_body(self, dictionary):
        term_counts = Counter()
        for hit in self.body_hits:
            # this should always be the case, but whatever
            if hit[0] in dictionary:
                term_counts[hit[0]] += len(hit) - 1
        return (term_counts, self.body_length)
    def minimum_title_window(self, query):
        return self.minimum_window(query, self.title)
    def minimum_anchor_window(self, query):
        minimum_window_size = float("inf")
        for a in self.anchor_text:
            minimum_window_size = min(minimum_window_size, self.minimum_window(query, a))
        return minimum_window_size

    def minimum_window(self, query, text):
        query = set(query.split())
        text = text.split()
        if not all(map( lambda w : w in text, query)):
            return float("inf")
        window = float("inf")
        for i in range(len(text)):
            for j in range(i + 1,len(text) + 1):
                if all(map( lambda w : w in text[i:j], query)):                    
                    window = min(window, j - i )
        return window

    def minimum_body_window(self, query):
        query = set(query.split())
        locs = []
        for hit in self.body_hits:
            if hit[0] in query:
                locs.append(hit[1:])
        min_window = float("inf")
        if len(locs) < len(query):
            return min_window
        # if the distance is > 1k this effect is marginal anyways
        # this code runs faster and requires less thinking
        MAX_WINDOW_CONSIDERED = 2000
        low = 0
        up = MAX_WINDOW_CONSIDERED
        while low < self.body_length:
            locs_filtered = []
            for l in locs:
                locs_filtered.append(filter_array(l,low,up))
            for cand in product(*locs_filtered):
                window_size = abs(min(cand) - max(cand))
                min_window = min(min_window, window_size)
            low += MAX_WINDOW_CONSIDERED/2
            up += MAX_WINDOW_CONSIDERED/2
        # we add one to account for the number of entries in the window
        # as opposed to the difference in indexes between the top and bottom
        return min_window + 1
            
def mul(c,a):
    return map(lambda v : v*c, a)
def add(a, b):
    return map(lambda (x,y) : x + y, zip(a,b))
def dot(a,b):
    assert(len(a)==len(b))
    return sum(map(lambda (a,b) : a*b,  zip(a,b)))
def l1_normalize(v):
    s = sum(v)
    if s > 0:
        return map(lambda x : x / float(s), v)
    else:
        return v

def read_train_data(filename='queryDocTrainData'):
    with open(filename,'r') as f:
        lines = f.readlines()
        lines = map(lambda l : l.rstrip(), lines)
        queries = []
        while len(lines) > 0:
            if "query:" in lines[0]:
                queries.append(Query())
                queries[-1].query_terms = lines[0].split(": ")[-1]
            elif "url:" in lines[0]:
                queries[-1].query_results.append(URL())
                queries[-1].query_results[-1].url = lines[0].split(": ")[-1]
            elif "title:" in lines[0]:
                queries[-1].query_results[-1].title = lines[0].split(": ")[-1]
            elif "body_hits:" in lines[0]:
                hits = lines[0].split(": ")[-1].split()
                hits[1:] = map(lambda v : int(v), hits[1:]) 
                queries[-1].query_results[-1].body_hits.append(hits)
            elif "body_length:" in lines[0]:
                queries[-1].query_results[-1].body_length = int(lines[0].split(": ")[-1])
            elif "anchor_text:" in lines[0]:
                queries[-1].query_results[-1].anchor_text.append(lines[0].split(": ")[-1])
            elif "stanford_anchor_count:" in lines[0]:
                queries[-1].query_results[-1].anchor_counts.append(int(lines[0].split(": ")[-1]))
            lines.pop(0)
        return queries


