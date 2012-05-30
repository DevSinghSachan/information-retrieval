from util import *

def bm25_sim(q, weights, dictionary, corpus):
    idf = parse_query(q.query_terms, dictionary, corpus)
    scored_urls = []
    for url in q.query_results:
        tf = [0]*3
        l_df = [0] * 3
        tf[0], l_df[0] = url.prepare_title(dictionary)
        tf[1], l_df[1] = url.prepare_body(dictionary)
        tf[2], l_df[2] = url.prepare_anchors(dictionary)
        # do I need to account for capitalization nonesense?
        ftf = [dict(),dict(),dict()]
        w_td = dict()
        score = 0
        for term in q.query_terms.split():
            w_td[term] = 0
            for f in range(2):
                lf = l_f[f]
                if(f == 2):
                    lf *= len(url.anchor_counts)
                if l_f[f] != 0:
                    ftf[f][term] = tf[f][term]/(1+Bf[f]*(l_df[f]/lf-1))
                else:
                    ftf[f][term] = 0
                w_td[term] += Wf[f]*ftf[f][term]
        
        	score += w_td[term]/(K1+w_td[term]) * idf[dictionary[term]] #What is idf?
        scored_urls.append((score, url))
    return scored_urls

Wf = [6, 12, 16] # weights for [Title,Body,Anchor]
Bf = [.3, .5, .9] # Some arbitrary constant for [Title,Body,Anchor]
K1 = 60 # another arbitrary constant
weights = Wf+Bf+[K1]

if __name__ == "__main__":
    dictionary = read_dictionary()
    queries = read_train_data()
    corpus = read_corpus()
    l_f = [0] * 3
    num_anchors = 0
    num_titles = 0
    for q in queries:
        for url in q.query_results:
            for a in url.anchor_text:
                l_f[2] += len(a.split())
            num_anchors += len(url.anchor_counts)
            l_f[0] += url.prepare_title(dictionary)[1]
        num_titles += len(q.query_results)
    l_f[0] /= float(num_titles)
    l_f[1] = corpus["#AVGLEN"]
    l_f[2] /= float(num_anchors)
    for q in queries:
        scored_urls = bm25_sim(q, weights, dictionary, corpus)
        # output the urls in order
        print "query: " + q.query_terms
        scored_urls.sort(reverse=True)
        for (s,u) in scored_urls:
            print " url: " + u.url
    with open('Weights','w') as f:
        f.write(" ".join(map(lambda n : str(n), weights)))
