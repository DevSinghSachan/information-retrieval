from __future__ import print_function
from math import log
from itertools import islice
import sys

from collections import Counter
from message_iterators import MessageIterator
from heapq import *

def counter_add(c1, c2):
  c = Counter()
  for w in c1:
    c[w] += c1[w]
  for w in c2:
    c[w] += c2[w]
  return c

def main():

  if not len(sys.argv) == 2:
    print("Usage: python  <train>".format(__file__), file=sys.stderr)
    sys.exit(-1)
  train  = sys.argv[1]
  mi = MessageIterator(train)
  word_num = 1
  word_map = dict()
  print_counts = Counter()
  for m in mi:
    for k in m.subject:
      if ":" in k or " " in k:        
        print("Found invalid word, quiting" ,file=sys.stderr)
        exit()

    doc = counter_add(m.subject, m.body)
    for k in doc:
      if not k in word_map:
        word_map[k] = word_num
      word_num += 1
    data = map(lambda k : (word_map[k],doc[k])  , doc)
    data.sort()
    data = " ".join(map(lambda (fid, c) : str(fid) + ":" + str(c), data))
    if print_counts[m.newsgroupnum] >= 20:
      continue
    print_counts[m.newsgroupnum] += 1
    print(str(m.newsgroupnum + 1) + " " + data)

if __name__ == '__main__':
  main()

