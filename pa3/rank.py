import sys
import os
if __name__ == "__main__":
    if int(sys.argv[1]) == 1:
        os.system("python cosine_sim.py " + sys.argv[2])
    elif int(sys.argv[1]) == 2:
        os.system("python bm25_sim.py " + sys.argv[2])
    elif int(sys.argv[1]) == 3:
        os.system("python window_sim.py " + sys.argv[2])
    else:
        print "WTF"
