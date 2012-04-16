#!/usr/bin/env python
from collections import deque
import os, glob, os.path
import sys
import re
#from engine import CompressedEngine as Engine
from engine import BasicEngine as Engine

if len(sys.argv) != 2:
  print >> sys.stderr, 'usage: python query.py index_dir' 
  os._exit(-1)

def merge_posting (postings1, postings2):
  new_posting = []
  p1_i = 0
  p2_i = 0
  while p1_i < len(postings1) and p2_i < len(postings2):
    if postings1[p1_i] == postings2[p2_i]:
      new_posting.append(postings1[p1_i])
      p1_i += 1
      p2_i += 1
    elif postings1[p1_i] < postings2[p2_i]:
      p1_i += 1
    else:
      p2_i += 1
  return new_posting

# file locate of all the index related files
index_dir = sys.argv[1]
index_f = open(index_dir+'/corpus.index', 'r')
word_dict_f = open(index_dir+'/word.dict', 'r')
doc_dict_f = open(index_dir+'/doc.dict', 'r')
posting_dict_f = open(index_dir+'/posting.dict', 'r')

word_dict = {}
doc_id_dict = {}
file_pos_dict = {}
doc_freq_dict = {}

engine = Engine()

print >> sys.stderr, 'loading word dict'
for line in word_dict_f.readlines():
  parts = line.split('\t')
  word_dict[parts[0]] = int(parts[1])
print >> sys.stderr, 'loading doc dict'
for line in doc_dict_f.readlines():
  parts = line.split('\t')
  doc_id_dict[int(parts[1])] = parts[0]
print >> sys.stderr, 'loading index'
for line in posting_dict_f.readlines():
  parts = line.split('\t')
  term_id = int(parts[0])
  file_pos = int(parts[1])
  doc_freq = int(parts[2])
  file_pos_dict[term_id] = file_pos
  doc_freq_dict[term_id] = doc_freq

def read_posting(term_id):
  index_f.seek(file_pos_dict[term_id])
  return engine.read_posting(index_f)


# read query from stdin
while True:
  input = sys.stdin.readline()
  input = input.strip()
  if len(input) == 0: # end of file reached
    break
  input_parts = input.split()
  term_ids = map(lambda w : word_dict[w] if w in word_dict else None, input_parts)
  if not all(map(lambda v : v is not None,term_ids)):
    print "no results found"
    continue
  term_ids = sorted(term_ids, key = lambda t : doc_freq_dict[t], reverse=True)    
  t, docs = read_posting(term_ids.pop())
  while len(term_ids) > 0 and len(docs) > 0:
    t, merge_docs = read_posting(term_ids.pop())    
    docs = merge_posting(docs, merge_docs)
  document_results = map(lambda d : doc_id_dict[d],docs)
  document_results.sort()
  for d in document_results:
    print d
