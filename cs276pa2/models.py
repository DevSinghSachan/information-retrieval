
import sys
import os.path
import gzip
from glob import iglob
import random
import itertools
import marshal
import math
from collections import Counter

bi_counts = Counter()
uni_counts = Counter()
L = 0.2 #lambda

def scan_corpus(training_corpus_loc):
  """
  Scans through the training corpus and counts how many lines of text there are
  """
  global bi_counts
  global uni_counts
  for block_fname in iglob( os.path.join( training_corpus_loc, '*.gz' ) ):
    print >> sys.stderr, 'processing dir: ' + block_fname
    with gzip.open( block_fname ) as f:
      num_lines = 0
      for line in f:
        # remember to remove the trailing \n
        line = line.rstrip()
        words = line.split()
        for word in words:
          uni_counts[word] += 1
        for tup in itertools.izip( words[:-1], words[1:] ):
          bi_counts[tup] += 1

def P_mle_uni(w1):
  return uni_counts[w1]/len(uni_counts)

def P_mle_bi(w1, w2): # P(w2|w1)
  return bi_counts[tuple([w1, w2])]/uni_counts[w1]

def P_int_bi(w1, w2): # P(w2|w1)
  return L*P_mle_uni(w2)+(1-L)*P_mle_bi(w1,w2)

# Q here is a raw sentence
def log_P(Q):
  words = Q.rstrip().split()
  log_p = math.log(P_mle_uni(words[0]))
  for tup in itertools.izip( words[:-1], words[1:] ):
    log_p += P_int_bi(tup[0], tup[1])
  return log_p

def read_edit1s():
  """
  Returns the edit1s data
  It's a list of tuples, structured as [ .. , (misspelled query, correct query), .. ]
  """
  edit1s = []
  with gzip.open(edit1s_loc) as f:
    # the .rstrip() is needed to remove the \n that is stupidly included in the line
    edit1s = [ line.rstrip().split('\t') for line in f if line.rstrip() ]
  return edit1s

def serialize_data(data, fname):
  """
  Writes `data` to a file named `fname`
  """
  with open(fname, 'wb') as f:
    marshal.dump(data, f)

def unserialize_data(fname):
  """
  Reads a pickled data structure from a file named `fname` and returns it
  IMPORTANT: Only call marshal.load( .. ) on a file that was written to using marshal.dump( .. )
  marshal has a whole bunch of brittle caveats you can take a look at in teh documentation
  It is faster than everything else by several orders of magnitude though
  """
  with open(fname, 'rb') as f:
    marshal.load(f)
    return marshal.load(f)

def loadModel():
  global bi_counts
  global uni_counts
  unicounts, bi_counts = return unserialize_data('model.dat')

if __name__ == '__main__':
  if len(sys.argv) != 3:
    print "Usage: python models.py <training corpus dir> <training edit1s file>"
    sys.exit()
  training_corpus_loc = sys.argv[1]
  edit1s_loc = sys.argv[2]
  scan_corpus(training_corpus_loc)
  serialize_data(tuple([dict(uni_counts), dict(bi_counts)]), 'model.dat')
  
