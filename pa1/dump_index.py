import sys
from engine import BasicEngine as Engine
if len(sys.argv) != 2:
    print "error"
    exit()
index = sys.argv[1]
index_f = open(index,'r')
e = Engine()
print e.examine_posting(index_f)
