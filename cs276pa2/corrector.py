import sys
from models import *

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

def kgrams(word,k):
  grams = []
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
       elif ins_cost == min_cost:
         if j == 0:
           ops[i,j] = ops[i,j-1] + [('i',0,str2[j])]
         else:
           ops[i,j] = ops[i,j-1] + [('i',str1[i], str2[j])]
       elif subs_cost == min_cost and cost > 0:
         ops[i,j] = ops[i-1,j-1] + [('s',str2[j],str1[i])]
       elif trans_cost == min_cost and cost > 0:
         ops[i,j] = ops[i-2,j-2] + [('t',str1[i],str1[i-1])]
       else:
         ops[i,j] = ops[i-1,j-1]
   return ops[(len(str1) -1, len(str2)-1)]

if __name__ == '__main__':
  if len(sys.argv) != 4:
    print "Usage: ./runcorrector.sh <dev|test> <uniform|empirical> <queries file>"
    sys.exit()
  mode = sys.argv[1]
  prob = sys.argv[2]
  queries_file = sys.argv[3]
  queries, gold, google = read_query_data()
  uni_counts, bi_counts = unserialize_data('model.dat')
  grams = unserialize_data('grams.dat')
  op_counts = unserialize_data('op_counts.dat')
  
  dictionary = unserialize_data('dictionary.dat')
  print find_candidates("hellp", grams, dictionary)
