import sys
from models import *
import models

queries_loc = 'data/queries.txt'
gold_loc = 'data/gold.txt'
google_loc = 'data/google.txt'

alphabet = "abcdefghijklmnopqrstuvwxyz0123546789&$+_' "

def read_query_data():
  """
  all three files match with corresponding queries on each line
  """
  queries = []
  gold = []
  google = []
  with open(queries_loc) as f:
    for line in f:
      queries.append(line.rstrip())
  with open(gold_loc) as f:
    for line in f:
      gold.append(line.rstrip())
  with open(google_loc) as f:
    for line in f:
      google.append(line.rstrip())
  assert( len(queries) == len(gold) and len(gold) == len(google) )
  return (queries, gold, google)

SEP_CHAR = "|"
def kgrams(word,k):
  grams = []
  word = (SEP_CHAR * (k-1)) + word + (SEP_CHAR * (k-1)) 
  for i in range(len(word)):
    g = word[i:i+k]
    if len(g) < k:
      break
    grams.append(g)
  return grams

# this is stupidly slow
# then again it's python
def DamerauLevenshtein(str1,str2):
   d = {}
   ops = {}
   ops[-1,-1] = []
   for i in xrange(-1,len(str1)):
     d[(i,-1)] = i + 1
     if i >= 0:
       if i == 0:
         ops[i,-1] = ops[i-1,-1] + [('d',0,str1[i])]
       else:
         ops[i,-1] = ops[i-1,-1] + [('d',str1[i-1],str1[i])]
   for j in xrange(-1,len(str2)):
     d[(-1,j)] = j + 1
     if j >= 0:
       if j == 0:
         ops[-1,j] = ops[-1,j- 1] + [('i',0,str2[j])]
       else:
         ops[-1,j] = ops[-1,j- 1] + [('i',str2[j-1], str2[j])]
   for i in xrange(len(str1)):
     for j in xrange(len(str2)):
       if str1[i] == str2[j]:
         cost = 0
       else:
         cost = 1
       del_cost = d[(i-1,j)] + 1
       ins_cost = d[(i,j-1)] + 1
       subs_cost = d[(i-1,j-1)] + cost
       if i > 0 and j > 0 and str1[i] == str2[j-1] and str1[i-1] == str2[j]:
         trans_cost = d[(i-2,j-2)] + cost
       else:
         trans_cost = 1000000
       min_cost = min(del_cost, ins_cost, subs_cost, trans_cost)
       d[i,j] = min_cost
       # we need to recover the moves we made
       if del_cost == min_cost:
         if i == 0:
           ops[i,j] = ops[i-1,j] + [('d',0,str1[i])]
         else:
           ops[i,j] = ops[i-1,j] + [('d',str1[i-1],str1[i])]           
       elif subs_cost == min_cost and cost > 0:
         ops[i,j] = ops[i-1,j-1] + [('s',str1[i],str2[j])]
       elif ins_cost == min_cost:
         if j == 0:
           ops[i,j] = ops[i,j-1] + [('i',0,str2[j])]
         else:
           ops[i,j] = ops[i,j-1] + [('i', str1[i], str2[j])]
       elif trans_cost == min_cost and cost > 0:
         ops[i,j] = ops[i-2,j-2] + [('t',str1[i-1],str1[i])]
       else:
         ops[i,j] = ops[i-1,j-1]
   return ops[(len(str1) -1, len(str2)-1)]

CAND_CUTOFF = 2.0/3
def find_candidates_kgram(word, gram_dict, dictionary):
  grams = kgrams(word,3)
  word_counts = Counter()
  for g in grams:
    if g in gram_dict:
      for w in gram_dict[g]:
        word_counts[w] += 1
  cands = []
  for w in word_counts:
    if word_counts[w] / float(len(grams)) >= CAND_CUTOFF:
      if len(DamerauLevenshtein(dictionary[w],word)) <= 2:
        cands.append(w)

  return map(lambda w : dictionary[w], cands)

ed_prob = 0.06
def uniform_prob(w1,w2, ops=[], op_counts=[]):
  ed = len(DamerauLevenshtein(w1,w2))
  return math.log(ed_prob ** (ed + len(ops)))

def empirical_prob(w1,w2, ops=[], op_counts=[]):
  prob = 0
  #print "---"
  #print w1
  #print w2
  for op in ops:
    #print op
    #print op_counts[op]
    #print op_counts[op[1]]
    #print  (op_counts[op]+1) / float(op_counts[op[1]] + len(op_counts))
    prob += math.log( (op_counts[op]+1) / float(op_counts[op[1]] + len(op_counts)))
  return prob
  
def suggest_word(w, grams, dictionary):
  return find_candidates_kgram(w, grams, dictionary)

def merges(q):
  """ 
  the query w/ adjacent words merged at every 
  combination of spaces
  """
  boundaries = [(q[:i], q[i:]) for i in range(1,len(q))]
  merges = [a + b[1:] for a, b in boundaries if b and b[0] == ' ']
  # get rid of double spaces
  merges = map(lambda s : s.replace("  ", " "), merges)
  return set(merges)

def find_split(w, dictionary):
  """iterate over all splits and find ones that yield 2 real words"""
  splits = [(w[:i], w[i:]) for i in range(1,len(w))]
  valid_splits = filter(lambda (w1,w2) : w1 in dictionary and w2 in dictionary, splits)
  valid_phrases = map(lambda (w1,w2) : w1 + " " + w2, valid_splits)
  return valid_phrases

def flatten_possibilities(arr):
  """
  takes an array of sets and takes teh euclidean product
  of all the elements in each set to get all possible 
  may also be of interest  sentences formed by those candidate sets
  """
  poss = []
  if len(arr) == 1:
    return arr[0]
  else:
    for prefix in arr[0]:
      for suffix in flatten_possibilities(arr[1:]):
        poss.append(prefix + " " + suffix)
  return poss

def get_q_prob(candidate, q):  
  diff = DamerauLevenshtein(candidate, q)
  return prob(candidate, q, diff, op_counts) + log_P(candidate)            


if __name__ == '__main__':
  if len(sys.argv) != 4:
    print "Usage: ./runcorrector.sh <dev|test> <uniform|empirical> <queries file>"
    sys.exit()
  mode = sys.argv[1]
  prob_mode = sys.argv[2]
  queries_file = sys.argv[3]
  queries, gold, google = read_query_data()
  uni_counts, bi_counts = unserialize_data('model.dat')

  models.uni_counts = uni_counts
  models.bi_counts = Counter(bi_counts)

  grams = unserialize_data('grams.dat')
  op_counts = Counter(unserialize_data('op_counts.dat'))
  dictionary = unserialize_data('dictionary.dat')
  if prob_mode == 'uniform':
    prob = uniform_prob
  elif prob_mode == 'empirical':
    prob = empirical_prob
  else:
    print "Error: invalid probability mode"
    sys.exit()
  match = 0
  miss = 0  
  #queries = ["forign affairs reporter the age"]
  for q_idx, q in enumerate(queries):
    all_candidates = set()
    modified_queries = merges(q)
    modified_queries.add(q)
    for mod_q in modified_queries:
      corrections = []
      ws = mod_q.split(' ')
      for w_idx, w in enumerate(ws):
        corrections.append(set())
        if not w in dictionary:
          suggested_ws = suggest_word(w, grams, dictionary)
          corrections[-1] = corrections[-1].union(suggested_ws)   
          corrections[-1] = corrections[-1].union(find_split(w, dictionary))
        else:
          corrections[-1].add(w)
          suggested_ws = suggest_word(w, grams, dictionary)
          if uni_counts[w] / float(uni_counts["#TOTAL#"]) < 1e-4:           
            corrections[-1] = corrections[-1].union(suggested_ws)
      # flatten queries
      all_candidates = all_candidates.union(flatten_possibilities(corrections))

      #all_candidates = set(filter(lambda c : len(DamerauLevenshtein(q, c)) <= 2 , all_candidates))
    print q
    print gold[q_idx]
    print google[q_idx]
    all_candidates = list(all_candidates)
    candidate_probabilities = map(lambda c : get_q_prob(c,q), all_candidates)
    #print zip(all_candidates,candidate_probabilities)

    best_cand_idx  = candidate_probabilities.index(max(candidate_probabilities))
    best_correction = all_candidates[best_cand_idx]
    print best_correction
    print max(candidate_probabilities)
    if best_correction == gold[q_idx]:
      match +=1 
    else:
      miss += 1
    print match
    print miss

