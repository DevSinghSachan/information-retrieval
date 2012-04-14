import struct
from array import array
class BasicEngine:
    POSTING_HEAD_FMT = "=II"
    POSTING_HEAD_SIZE = struct.calcsize(POSTING_HEAD_FMT)
    POSTING_ARRAY_FMT = "I"
    def read_head(self,f):
        buf = f.read(self.POSTING_HEAD_SIZE)
        if len(buf) == self.POSTING_HEAD_SIZE:
            return struct.unpack(self.POSTING_HEAD_FMT, buf)
        else:
            return None    
    def print_posting(self, f, post):
        # postings are laid out as "struct(TERM,#DOCS)array(uses)"
        # while we don't need this information here it uses little space
        # and makes the merge process easier
        term,uses = post
        f.write(struct.pack(self.POSTING_HEAD_FMT,term, len(uses)))
        array(self.POSTING_ARRAY_FMT,uses).tofile(f)        
    def examine_posting(self,f):
        h = self.read_head(f)
        while h:
            term,length = h
            posts = array(self.POSTING_ARRAY_FMT)
            posts.fromfile(f,length)
            print term, posts
            h = self.read_head(f)
    def iter_docs(self, f):
        h = self.read_head(f)
        posts = array(self.POSTING_ARRAY_FMT)
        if h:
            term,length = h
            for i in xrange(length):
                posts.fromfile(f,1)
                yield posts[0]
    def read_posting(self,f):
        h = self.read_head(f)
        if h:
            term,length = h            
            posts = array(self.POSTING_ARRAY_FMT)
            posts.fromfile(f,length)
            return (term, posts.tolist())
