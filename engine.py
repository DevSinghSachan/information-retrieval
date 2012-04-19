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

# We'll want the file size in bits stored since we can't store partial bytes at the head of the file
class GammaCompressedEngine(Engine):
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
    def vb_encode(self, arr):
        bytestream = array(self.POSTING_ARRAY_FMT)
        buf = ''
        numbits = 0
        for n in arr:
            # pull bits from end
            s = ''
            b = n
            while b>0:
                if(b%2 == 1):
                    s = ''.join(['1',s])
                else:
                    s = ''.join(['0',s])
                b = b/2
            # s now contains a string of the binary.
            # Convert s into gamma compressed form
            s = (len(s)-1)*'1'+'0'+s[1:]
            buf = buf + s
            # totally copying things all over the place :/
            while len(buf)>8:
                numbits += 8
                bytestream.append(int(buf[:8],2))
                buf = buf[8:]
        if(len(buf)>0):
            # this line does not run
            numbits += len(buf)
            buf = buf + '0'*(8-len(buf))
            bytestream.append(int(buf,2))
        #TODO: Add numbits to file
        for i in range(4):
            bytestream.insert(0,numbits%(1<<8))
            numbits /=(1<<8)

        return bytestream

    def vb_decode(self, bytes):
        #TODO Read numbits and stop if we've read numbits bits
        numbits = 0
        for i in range(4):
            numbits = (numbits*1<<8)+bytes.pop(0)
        numbers = []
        n = 0
        getLength = True #getlength means we're still in the prefix
        l = 0
        for b in bytes:
            if(numbits <= 0):
                    break
            for bit in range(7,-1,-1):
                if(numbits <= 0):
                    break
                numbits -= 1
                if getLength:
                    if b & 1<<bit:
                        l += 1
                    else:
                        if l==0:
                            numbers.append(1)
                        else:
                            getLength = False
                            n = 1<<l
                            if l==0:
                                numbers.append(1)
                else:
                    if b & 1<<bit:
                        n += 1<<(l-1)
                    l = l-1
                    if(l==0):
                        getLength = True
                        numbers.append(n)
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
