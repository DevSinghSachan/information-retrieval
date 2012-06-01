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

def prior(class_counts, classnum):
  doc_count = 0
  for class_num in class_counts:
    doc_count += class_counts[class_num]
  # we assume that all docs belong to one of the classes
  # thus no smoothing is needed
  return class_counts[classnum] / float(doc_count)


def binomial(mi):
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
  # ensures we print the first $X of each class
  print_counts = Counter()
  # used for accuracy computation
  corrects = 0
  trials = 0
  # prior probabilities of each class
  priors = dict()
  for c in classes:
    priors[c] = log(prior(class_counts, c))    
  for m in mi:
    groupnum = m.newsgroupnum
    if print_counts[groupnum] >= 20:
      continue
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
    print("\t".join(map(lambda (prob,c) : str(prob), scores)))
    print_counts[groupnum] += 1
    predicted_class = max(scores)[1]
    if predicted_class == groupnum:
      corrects += 1
    trials += 1
    print("actual class : " + str(groupnum) ,file=sys.stderr)
    print("predicted class : " + str(predicted_class) ,file=sys.stderr)
    print("accuracy : " + str(float(corrects) / trials) ,file=sys.stderr)
def binomial_chi2(mi):
  # Create index by category
  counts = [0]*20
  totals = Counter()
  numDocs = [0]*20
  for i in range(len(counts)):
    counts[i] = Counter()
  for message in mi:
    numDocs[message.newsgroupnum] += 1
    doc = counter_add(m.subject, m.body)
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
  binomial(mi)

def multinomial(mi):
  pass



def twcnb_init(mi, filter_func=None):
  """
  converts the mi into the needed weight format we need
  for all of the twcnb-related functions
  """
  class_words = dict()  
  for m in mi:
    groupnum = m.newsgroupnum
    if not groupnum in class_words:
      class_words[groupnum] = Counter()
    doc = counter_add(m.subject, m.body)
    # as a hack just put everything in m.body
    m.body = doc
  if filter_func:
    # should modify mi in place, but whatever
    mi = filter_func(mi)
  for m in mi:
    groupnum = m.newsgroupnum
    for w in m.body:
      if m.body[w] <= 0:
        continue
      class_words[groupnum][w] += 1  
  return class_words

def cnb_filter(class_words):
  # we need to know how big the dictionary is
  dictionary = set()
  for c in class_words:
    dictionary = dictionary.union(class_words[c].keys())
  alpha = len(dictionary)
  cc_words = dict()
  # LINE 4 PAGE 7
  for c in class_words:
    cc_words[c] = Counter()
    denom = len(class_words[c]) # alpha
    for j in class_words:
      if j == c:
        continue
      for k in class_words[j]:
        denom += class_words[j][k]
    for i in class_words[c]:
      num = 1
      for j in class_words:
        if j == c:
          continue
        num += class_words[j][i]
      cc_words[c][i] = log(num / float(denom))
  return cc_words

def wcnb_filter(class_words):
  for c in class_words:
    weight_sum = 0.0
    for w in class_words[c]:
      weight_sum += abs(class_words[c][w])
    for  w in class_words[c]:
      class_words[c][w] /= weight_sum
  return class_words

def twcnb_filter(mi):
  # EQUATION 1
  for m in mi:
    for w in m.body:
      m.body[w] = log(m.body[w] + 1)
  # EQUATION 2
  for m in mi:
    for i in m:
      num = len(mi)
      denom = 0
      for j in mi:
        if mi[j][i] > 0:
          denom += 1
  return mi
      
    

def advanced_nb(mi, weight_filter_func, message_filter_func=None):
  if message_filter_func != None:
    mi = message_filter_func(mi)
  class_words = twcnb_init(mi)
  class_words = weight_filter_func(class_words)
  class_count = Counter()
  correct = 0
  total = 0
  for m in mi:
    groupnum = m.newsgroupnum
    if class_count[groupnum] >= 20:
      continue
    class_count[groupnum] += 1
    doc = counter_add(m.body,m.subject)
    scores = []
    for c in class_words:
      score = 0
      for w in doc:
        score += doc[w] * class_words[c][w]
      scores.append((score, c))
    total += 1
    predicted_class = min(scores)[1]
    if predicted_class == groupnum:
      correct += 1
    print("actual class : " + str(groupnum), file=sys.stderr)
    print("predicted class : " + str(predicted_class), file=sys.stderr)
    print("accuracy : " + str(float(correct) / total), file=sys.stderr)

def cnb(mi):
  advanced_nb(mi, cnb_filter)
def wcnb(mi):
  advanced_nb(mi, lambda cw : wcnb_filter(cnb_filter(cw)))
  dictionary = dict()
  counts = [0]*20
  totals = Counter()
  numDocs = [0]*20
  for i in range(len(counts)):
    counts[i] = Counter()
  for message in mi:
    numDocs[message.newsgroupnum] += 1
    words = counter_add(message.body, message.subject)
    for word in words:
      dictionary[word] = 1
      counts[message.newsgroupnum][word] += words[word]
      #totals[word] += words[word]
  output = ['']*20
  # Perform classification
  # ensures we print the first $X of each class
  print_counts = Counter()
  # used for accuracy computation
  corrects = 0
  trials = 0
  # prior probabilities of each class
  priors = dict()
  classes = range(20)
  total = sum(numDocs)
  for c in classes:
    priors[c] = log(numDocs[c]/float(total))
  for m in mi:
    groupnum = m.newsgroupnum
    words = counter_add(m.subject, m.body)
    if print_counts[groupnum] >= 20:
      continue
    scores = []
    for c in classes:
      prob = 0
      prob += priors[c]
      for word in words:
        term_prob = words[word]*(counts[c][word]+1)/float(numDocs[c]+len(dictionary))  # Need smoothing?
        prob += log(term_prob)
      scores.append((prob,c))
    #print("\t".join(map(lambda (prob,c) : str(prob), scores)))
    print_counts[groupnum] += 1
    predicted_class = max(scores)[1]
    if predicted_class == groupnum:
      corrects += 1
    trials += 1
    print("actual class : " + str(groupnum) ,file=sys.stderr)
    print("predicted class : " + str(predicted_class) ,file=sys.stderr)
    print("accuracy : " + str(float(corrects) / trials) ,file=sys.stderr)
    output[groupnum] += str(predicted_class)+"\t"
  for i in range(len(output)):
    print(output[i][:-1])

def twcnb(mi):
  pass

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
    'multinomial': multinomial,
    'twcnb': twcnb,
    'cnb' : cnb,
    'wcnb' : wcnb
    # Add others here if you want
    }

def main():
  if not len(sys.argv) == 3:
    print("Usage: python {0} <mode> <train>".format(__file__), file=sys.stderr)
    sys.exit(-1)
  mode = sys.argv[1]
  train = sys.argv[2]

  mi = MessageIterator(train)

  #try:
  MODES[mode](mi)
  #except KeyError:
  #  print("Unknown mode: {0}".format(mode),file=sys.stderr)
  #  print("Accepted modes are: {0}".format(MODES.keys()), file=sys.stderr)
  #  sys.exit(-1)

if __name__ == '__main__':
  main()

