#!/bin/env python
from collections import deque
import os, glob, os.path
import sys
import re
import struct
from array import array
from engine import Engine

if len(sys.argv) != 3:
  print >> sys.stderr, 'usage: python index.py data_dir output_dir' 
  os._exit(-1)

total_file_count = 0
root = sys.argv[1]
out_dir = sys.argv[2]
if not os.path.exists(out_dir):
  os.makedirs(out_dir)

# this is the actual posting lists dictionary
posting_dict = {}
# this is a dict holding document name -> doc_id
doc_id_dict = {}
# this is a dict holding word -> word_id
word_dict = {}
# this is a queue holding block names, later used for merging blocks
block_q = deque([])

# function to count number of files in collection
def count_file():
  global total_file_count
  total_file_count += 1

# function for printing a line in a postings list to a given file
def print_posting(f, posting_line):
  term = posting_line[0]
  uses = posting_line[1]
  posting_dict[term] = (f.tell(), len(uses))
  # postings are laid out as "struct(#DOCS)array(uses)"
  f.write(struct.pack(Engine.POSTING_ARRAY_HEAD_FMT,len(uses))
  array(Engine.POSTING_ARRAY_FMT,uses).tofile(f)
                     
# function for merging two lines of postings list to create a new line of merged results
def merge_posting (line1, line2):
  # don't forget to return the resulting line at the end
  print >> sys.stderr, 'you must provide implementation'
  return None

doc_id = -1
word_id = 0

for dir in sorted(os.listdir(root)):
  print >> sys.stderr, 'processing dir: ' + dir
  dir_name = os.path.join(root, dir)
  block_pl_name = out_dir+'/'+dir 
  # append block names to a queue, later used in merging
  block_q.append(dir)
  block_pl = open(block_pl_name, 'w')
  term_doc_list = []
  for f in sorted(os.listdir(dir_name)):
    count_file()
    file_id = os.path.join(dir, f)
    doc_id += 1
    doc_id_dict[file_id] = doc_id
    fullpath = os.path.join(dir_name, f)
    file = open(fullpath, 'r')
    for line in file.readlines():
      tokens = line.strip().split()
      for token in tokens:
        if token not in word_dict:
          word_dict[token] = word_id
          word_id += 1
        term_doc_list.append( (word_dict[token], doc_id) )
  print >> sys.stderr, 'sorting term doc list for dir:' + dir
  # sort term doc list
  term_doc_list.sort()
  print >> sys.stderr, 'print posting list to disc for dir:' + dir
  # write the posting lists to block_pl for this current block 
  posting_line = [term_doc_list[0][0], []]
  for td in term_doc_list:
    if td[0] == posting_line:
      posting_line[1].append(td[1])
    else:
      print_posting(block_pl, posting_line)
      posting_line = [td[0],[td[1]]]
  if len(posting_line[1]) > 0:
    print_posting(block_pl, posting_line)        
  block_pl.close()

print >> sys.stderr, '######\nposting list construction finished!\n##########'

print >> sys.stderr, '\nMerging postings...'
while True:
  if len(block_q) <= 1:
    break
  b1 = block_q.popleft()
  b2 = block_q.popleft()
  print >> sys.stderr, 'merging %s and %s' % (b1, b2)
  b1_f = open(out_dir+'/'+b1, 'r')
  b2_f = open(out_dir+'/'+b2, 'r')
  comb = b1+'+'+b2
  comb_f = open(out_dir + '/'+comb, 'w')
  # (provide implementation merging the two blocks of posting lists)
  # write the new merged posting lists block to file 'comb_f'
  b1_f.close()
  b2_f.close()
  comb_f.close()
  os.remove(out_dir+'/'+b1)
  os.remove(out_dir+'/'+b2)
  block_q.append(comb)
    
print >> sys.stderr, '\nPosting Lists Merging DONE!'

# rename the final merged block to corpus.index
final_name = block_q.popleft()
os.rename(out_dir+'/'+final_name, out_dir+'/corpus.index')

# print all the dictionary files
doc_dict_f = open(out_dir + '/doc.dict', 'w')
word_dict_f = open(out_dir + '/word.dict', 'w')
posting_dict_f = open(out_dir + '/posting.dict', 'w')
print >> doc_dict_f, '\n'.join( ['%s\t%d' % (k,v) for (k,v) in sorted(doc_id_dict.iteritems(), key=lambda(k,v):v)])
print >> word_dict_f, '\n'.join( ['%s\t%d' % (k,v) for (k,v) in sorted(word_dict.iteritems(), key=lambda(k,v):v)])
print >> posting_dict_f, '\n'.join(['%s\t%s' % (k,'\t'.join([str(elm) for elm in v])) for (k,v) in sorted(posting_dict.iteritems(), key=lambda(k,v):v)])
doc_dict_f.close()
word_dict_f.close()
posting_dict_f.close()

print total_file_count
