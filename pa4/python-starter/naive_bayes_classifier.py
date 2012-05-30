
from __future__ import print_function

import sys

from collections import Counter
from message_iterators import MessageIterator
from heapq import *

def binomial(mi):
  pass

def binomial_chi2(mi):
  # Create index by category
  counts = [0]*20
  totals = Counter()
  numDocs = [0]*20
  for i in range(len(counts)):
    counts[i] = Counter()
  for message in mi:
    numDocs[message.newsgroupnum] += 1
    for word in message.body:
      counts[message.newsgroupnum][word] += 1#message.body[word]
      totals[word] += 1#message.body[word]
    #for word in message.subject:
    #  counts[message.newsgroupnum][word] += 1#message.subject[word]
    #  totals[word] += 1#message.subject[word]
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
    'twcnb': twcnb
    # Add others here if you want
    }

def main():
  if not len(sys.argv) == 3:
    print("Usage: python {0} <mode> <train>".format(__file__), file=sys.stderr)
    sys.exit(-1)
  mode = sys.argv[1]
  train = sys.argv[2]

  mi = MessageIterator(train)

  try:
    MODES[mode](mi)
  except KeyError:
    print("Unknown mode: {0}".format(mode),file=sys.stderr)
    print("Accepted modes are: {0}".format(MODES.keys()), file=sys.stderr)
    sys.exit(-1)

if __name__ == '__main__':
  main()

