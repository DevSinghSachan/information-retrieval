import struct
import sys
from array import array

class Engine:
    def read_head(self,f):
        buf = f.read(self.POSTING_HEAD_SIZE)
        if len(buf) == self.POSTING_HEAD_SIZE:
            return struct.unpack(self.POSTING_HEAD_FMT, buf)
        else:
            return None    
    def to_gaps(self,arr):
        return [arr[0]] + map(lambda p : p[1] - p[0] , zip(arr[:-1], arr[1:]))
    def from_gaps(self,arr):
        prev = 0
        res = []
        for v in arr:
            prev += v
            res.append(prev)
        return res    
    def vb_encode_num(self,n):
        bytes = array(self.POSTING_ARRAY_FMT)
        while True:
            bytes.append(n % 128)
            if n < 128:
                break
            else:
                n /= 128
        bytes[0] += 128
        # this is slow and optimally wouldn't be here
        bytes.reverse()
        return bytes

class CompressedEngine(Engine):
    POSTING_HEAD_FMT = "=II"
    POSTING_HEAD_SIZE = struct.calcsize(POSTING_HEAD_FMT)
    POSTING_ARRAY_FMT = "B"
    def print_posting(self, f, post):
        # postings are laid out as "struct(TERM,#Bytes)array(encoded_uses)"
        term, uses = post
        encoded_uses = self.vb_encode(self.to_gaps(uses))
        f.write(struct.pack(self.POSTING_HEAD_FMT, term, len(encoded_uses)))
        encoded_uses.tofile(f)
    def read_posting(self,f):
        h = self.read_head(f)
        if h:
            term,length = h
            bytes = array(self.POSTING_ARRAY_FMT)
            bytes.fromfile(f, length)
            posts = self.from_gaps(self.vb_decode(bytes.tolist()))
            return (term, posts)
    def vb_encode(self,arr):
        bytestream = array(self.POSTING_ARRAY_FMT)
        for n in arr:
            bytestream.extend(self.vb_encode_num(n))
        return bytestream
    def vb_decode(self,bytes):
        numbers = []
        n = 0
        for b in bytes:
            if b < 128:
                n = n*128 + b
            else:
                n = n*128 + (b - 128)
                numbers.append(n)
                n = 0
        return numbers

class BasicEngine(Engine):
    POSTING_HEAD_FMT = "=II"
    POSTING_HEAD_SIZE = struct.calcsize(POSTING_HEAD_FMT)
    POSTING_ARRAY_FMT = "I"
    def print_posting(self, f, post):
        # postings are laid out as "struct(TERM,#DOCS)array(uses)"
        # while we don't need this information here it uses little space
        # and makes the merge process easier
        term,uses = post
        f.write(struct.pack(self.POSTING_HEAD_FMT, term, len(uses)))
        array(self.POSTING_ARRAY_FMT,uses).tofile(f)        
    def examine_posting(self,f):
        h = self.read_head(f)
        while h:
            term,length = h
            posts = array(self.POSTING_ARRAY_FMT)
            posts.fromfile(f,length)
            print term, posts
            h = self.read_head(f)
    def read_posting(self,f):
        h = self.read_head(f)
        if h:
            term,length = h            
            posts = array(self.POSTING_ARRAY_FMT)
            posts.fromfile(f,length)
            return (term, posts.tolist())

class BasicGapEngine(Engine):
    POSTING_HEAD_FMT = "=II"
    POSTING_HEAD_SIZE = struct.calcsize(POSTING_HEAD_FMT)
    POSTING_ARRAY_FMT = "I"
    def print_posting(self, f, post):
        # postings are laid out as "struct(TERM,#DOCS)array(uses)"
        # while we don't need this information here it uses little space
        # and makes the merge process easier
        term,uses = post
        gap_uses = self.to_gaps(uses)
        f.write(struct.pack(self.POSTING_HEAD_FMT, term, len(gap_uses)))
        array(self.POSTING_ARRAY_FMT,gap_uses).tofile(f)        
    def read_posting(self,f):
        h = self.read_head(f)
        if h:
            term,length = h            
            gaps = array(self.POSTING_ARRAY_FMT)
            gaps.fromfile(f,length)
            posts = self.from_gaps(gaps)
            return (term, posts)
