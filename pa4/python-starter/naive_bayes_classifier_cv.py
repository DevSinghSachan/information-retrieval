from __future__ import print_function
from math import log
from itertools import islice
import sys

from collections import Counter
from message_iterators import MessageIterator
from heapq import *
from random import shuffle

def counter_add(c1, c2):
  c = Counter()
  for w in c1:
    c[w] += c1[w]
  for w in c2:
    c[w] += c2[w]
  return c

def prior(class_counts, classnum):
  doc_count = 0
  for class_num in class_counts:
    doc_count += class_counts[class_num]
  # we assume that all docs belong to one of the classes
  # thus no smoothing is needed
  return class_counts[classnum] / float(doc_count)


def binomial(mi,test):
  # how many docs in each class
  class_counts = Counter()
  # count of words in each class
  class_words = dict()  
  # set of all words
  dictionaries = dict()
  # set of all classes
  classes = set()
  for m in mi:
    groupnum = m.newsgroupnum
    classes.add(groupnum)
    class_counts[groupnum] += 1
    if not groupnum in class_words:
      class_words[groupnum] = Counter()
    doc = counter_add(m.subject, m.body)
    for w in doc:
      if doc[w] <= 0:
        continue
      if not (groupnum in dictionaries):
        dictionaries[groupnum] = set()
      dictionaries[groupnum].add(w)
      class_words[groupnum][w] += 1
  # used for accuracy computation
  corrects = 0
  trials = 0
  # prior probabilities of each class
  priors = dict()
  for c in classes:
    priors[c] = log(prior(class_counts, c))
  n = 0
  for m in test:
    n += 1
    if n%100 == 0:
      print("\tPercent Done: " + str(float(n)/len(test)) ,file=sys.stderr)
    groupnum = m.newsgroupnum
    scores = []
    for c in classes:
      prob = 0
      prob += priors[c]
      for term in dictionaries[groupnum]:
        term_prob = (class_words[c][term] + 1)/ (float(class_counts[c]) + len(dictionaries[groupnum]))
        if not (term in m.subject or term in m.body):
          term_prob = 1 - term_prob
        prob += log(term_prob)
      scores.append((prob,c))
    predicted_class = max(scores)[1]
    if predicted_class == groupnum:
      corrects += 1
    trials += 1
    """print("actual class : " + str(groupnum) ,file=sys.stderr)
    print("predicted class : " + str(predicted_class) ,file=sys.stderr)
    print("accuracy : " + str(float(corrects) / trials) ,file=sys.stderr)"""
  return float(corrects) / trials
def binomial_chi2(mi,test):
  # Create index by category
  counts = [0]*20
  totals = Counter()
  numDocs = [0]*20
  for i in range(len(counts)):
    counts[i] = Counter()
  for message in mi:
    numDocs[message.newsgroupnum] += 1
    doc = counter_add(message.subject, message.body)
    for word in doc:
      counts[message.newsgroupnum][word] += 1
      totals[word] += 1
  # Run chi-squared for each group
  chosenwords = [0]*20
  for i in range(20):
    chosenwords[i] = []
  for i in range(len(counts)):
    for word in counts[i]:
      # Using formula from page 276 of IR book
      N11 = counts[i][word]
      N10 = totals[word]-counts[i][word]
      N01 = numDocs[i]-counts[i][word]
      N00 = sum(numDocs)-N11-N10-N01
      chisq=float((N11+N10+N01+N00)*(N11*N00-N10*N01)**2)/((N11+N01)*(N11+N10)*(N10+N00)*(N01+N00))
      heappush(chosenwords[i],(-chisq,word))
  chosenwords = [[heappop(chosenwords[i]) for j in range(min(300, len(chosenwords[i])))] for i in range(20)]
  wordlist = [[x[1] for x in words] for words in chosenwords]
  for words in wordlist:
    output = '\t'.join(words)
    print(output)
  #remove words that aren't used
  for message in mi:
    for word in message.body:
      if(wordlist[message.newsgroupnum].count(word)==0):
        message.body[word] = 0
    for word in message.subject:
      if(wordlist[message.newsgroupnum].count(word)==0):
        message.subject[word] = 0
  return binomial(mi,test)

def multinomial(mi,test):
  dictionary = dict()
  counts = [0]*20
  numDocs = [0]*20
  for i in range(len(counts)):
    counts[i] = Counter()
  for message in mi:
    numDocs[message.newsgroupnum] += 1
    words = counter_add(message.body, message.subject)
    for word in words:
      dictionary[word] = 1
      counts[message.newsgroupnum][word] += words[word]
  output = ['']*20
  # Perform classification
  # used for accuracy computation
  corrects = 0
  trials = 0
  # prior probabilities of each class
  priors = dict()
  classes = range(20)
  total = sum(numDocs)
  for c in classes:
    priors[c] = log(numDocs[c]/float(total))
  n = 0
  for m in test:
    if n%1000 == 0:
      print("\tPercent Done: " + str(float(n)/len(test)) ,file=sys.stderr)
    n += 1
    groupnum = m.newsgroupnum
    words = counter_add(m.subject, m.body)
    scores = []
    for c in classes:
      prob = 0
      prob += priors[c]
      for word in words:
        alpha = 1
        term_prob = (counts[c][word]+alpha)/float(numDocs[c]+alpha*len(dictionary)) # Need smoothing?
        prob += words[word]*log(term_prob)
      scores.append((prob,c))
    predicted_class = max(scores)[1]
    if predicted_class == groupnum:
      corrects += 1
    trials += 1
    """print("actual class : " + str(groupnum) ,file=sys.stderr)
    print("predicted class : " + str(predicted_class) ,file=sys.stderr)
    print("accuracy : " + str(float(corrects) / trials) ,file=sys.stderr)"""

  return float(corrects) / trials

def output_probability(probs):
  for i, prob in enumerate(probs):
    if i == 0:
      sys.stdout.write("{0:1.8g}".format(prob))
    else:
      sys.stdout.write("\t{0:1.8g}".format(prob))
  sys.stdout.write("\n")


MODES = {
    'binomial': binomial,
    'binomial-chi2': binomial_chi2,
    'multinomial': multinomial
    # Add others here if you want
    }

def main():
  if not len(sys.argv) == 3:
    print("Usage: python {0} <mode> <train>".format(__file__), file=sys.stderr)
    sys.exit(-1)
  mode = sys.argv[1]
  train = sys.argv[2]

  mi = MessageIterator(train)
  data = [m for m in mi]
  shuffle(data)
  k = 10
  trials = [0]*k
  size = len(data)
  for i in range(k):
    print("iteration : " + str(i+1) +"/"+str(k),file=sys.stderr)
    train = data[(i*size)/k:((i+1)*size)/k]
    test = data[:(i*size)/k]
    test.extend(data[((i+1)*size)/k:])
    trials[i] = MODES[mode](train,test)
    print(trials[i])
  print(trials)

if __name__ == '__main__':
  main()

