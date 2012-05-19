from util import *
def bm25_sim(q, weights, dictionary, corpus):
    pq = l1_normalize(parse_query(q.query_terms, dictionary, corpus))
    scored_urls = []
    for url in q.query_results:
        l_f = [0] * 3
        l_f[2] = url.prepare_anchors(dictionary)[1]
        l_f[1] = url.prepare_title(dictionary)[1]
        l_f[0] = url.prepare_body(dictionary)[1]
    l_f = [float(x)/len(q.query_results) for x in l_f]
    for url in q.query_results:
        print "For: " + url.title
        Bf = 1. # Some arbitrary constant
        K1 = 1. # another arbitrary constant
        Wf = [1., 1., 1.] # weights for [Title,Body,Anchor]
        # normalize weights
        Wf = [float(x)/dot(Wf,Wf)**.5 for x in Wf]
        
        tf = [0]*3
        l_df = [0] * 3
        tf[2], l_df[2] = url.prepare_anchors(dictionary)
        tf[1], l_df[1] = url.prepare_title(dictionary)
        tf[0], l_df[0] = url.prepare_body(dictionary)
        # do I need to account for capitalization nonesense?
        ftf = [dict(),dict(),dict()]
        w_td = dict()
        score = 0
        for term in q.query_terms.split():
            w_td[term] = 0
            for f in range(2):
                if l_f[f] != 0:
                    ftf[f][term] = tf[f][term]/(1+Bf*(l_df[f][term]/l_f[f]-1))
                else:
                    ftf[f][term] = 0
                w_td[term] += Wf[f]*ftf[f][term]
        
        	score += w_td[term]/(K1+w_td[term]) * idf[term] #What is idf?
        scored_urls.append((score, url))
    return scored_urls
if __name__ == "__main__":
    weights = [0.50, 0.30, 0.20]
    dictionary = read_dictionary()
    queries = read_train_data()
    corpus = read_corpus()
    for q in queries:
        scored_urls = bm25_sim(q, weights, dictionary, corpus)
        # output the urls in order
        print "query: " + q.query_terms
        scored_urls.sort(reverse=True)
        for (s,u) in scored_urls:
            print " url: " + u.url
    with open('Weights','w') as f:
        weights.reverse()
        f.write(" ".join(map(lambda n : str(n), weights)))
