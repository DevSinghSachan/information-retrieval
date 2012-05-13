def read_dictionary(filename='AllQueryTerms'):
    with open(filename,'r') as f:
        lines = f.readlines()
        lines = map(lambda l : l.rstrip(), lines)
        return set(lines)

class Query():
    # array of queries
    query_terms = []
    # URL objects go here
    query_results = []
class URL():
    url = ""
    title = ""
    # [["term", loc1, loc2, ...], ...]
    body_hits = []
    body_length = 0
    # ["anchor1", "anchor2", ...]
    anchor_text = []
    # [anchor1_count, anchor2_count, ...]
    anchor_counts = []

def read_train_data(filename='queryDocTrainData'):
    with open(filename,'r') as f:
        lines = f.readlines()
        lines = map(lambda l : l.rstrip(), lines)
        queries = []
        while len(lines) > 0:
            if "query:" in lines[0]:
                queries.append(Query())
                queries[-1].query_terms = lines[0].split(": ")[-1].split()
            elif "url:" in lines[0]:
                queries[-1].query_results.append(URL())                
                queries[-1].query_results[-1].url = lines[0].split(": ")[-1]
            elif "title:" in lines[0]:
                queries[-1].query_results[-1].title = lines[0].split(": ")[-1]
            elif "body_hits:" in lines[0]:
                queries[-1].query_results[-1].body_hits.append(lines[0].split(": ")[-1].split())
                queries[-1].query_results[-1].body_hits[-1][1:] = map(lambda v : int(v), queries[-1].query_results[-1].body_hits[-1][1:])
            elif "body_length:" in lines[0]:
                queries[-1].query_results[-1].body_length = int(lines[0].split(": ")[-1])
            elif "anchor_text:" in lines[0]:
                queries[-1].query_results[-1].anchor_text.append(lines[0].split(": ")[-1])
            elif "stanford_anchor_count:" in lines[0]:
                queries[-1].query_results[-1].anchor_counts.append(lines[0].split(": ")[-1])
            lines.pop(0)
        return queries
read_train_data()
