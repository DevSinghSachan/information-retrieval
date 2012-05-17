from util import *
from cosine_sim import cosine_sim

if __name__ == "__main__":
    cosine_sim_weights = [0.50, 0.30, 0.20]
    window_weight = 5
    window_function = (lambda v : 1.0 / v)
    dictionary = read_dictionary()
    queries = read_train_data()
    corpus = read_corpus()
    for q in queries:
        scored_urls = cosine_sim(q, cosine_sim_weights, dictionary, corpus)
        # output the urls in order
        print "query: " + q.query_terms
        boosted_urls = []
        for (s,u) in scored_urls:
            min_dist = u.minimum_body_window(q.query_terms)
            min_dist = min(min_dist, u.minimum_title_window(q.query_terms))
            min_dist = min(min_dist, u.minimum_anchor_window(q.query_terms))
            min_dist -= len(q.query_terms.split())
            min_dist += 1
            B = max(1.0, window_function(min_dist) * window_weight)
            boosted_urls.append((s * B, u))
        boosted_urls.sort(reverse=True)
        for (s,u) in boosted_urls:
            print " url: " + u.url
    with open('Weights','w') as f:
        cosine_sim_weights.reverse()
        cosine_sim_weights.append(window_weight)
        f.write(" ".join(map(lambda n : str(n), cosine_sim_weights)))
