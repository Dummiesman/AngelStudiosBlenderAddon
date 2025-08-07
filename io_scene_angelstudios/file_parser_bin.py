import struct

class FileParser:
    def __init__(self, stream):
        self.__stream = stream
        
    def read_line(self):
        raise NotImplementedError()

    def read_tokens(self):
        raise NotImplementedError
    
    def match_token(self, name):
        return True
    
    def match_int(self, name):
        return struct.unpack("<L", self.__stream.read(4))
    
    def read_int(self):
        return struct.unpack("<L", self.__stream.read(4))
    
    def match_float(self, name):
        return struct.unpack("<F", self.__stream.read(4))
    
    def read_float(self):
        return struct.unpack("<F", self.__stream.read(4))
        
    def read_int_array(self, count):
        arr = []
        for x in range(count):
            arr.append(self.read_int())
        return arr
        
    def read_float_array(self, count):
        arr = []
        for x in range(count):
            arr.append(self.read_float())
        return arr
    
    def match_vector(self, name, count):
        arr = []
        for x in range(count):
            arr.append(self.read_float())
        return arr
    
    def read_vector(self, name, count):
        return self.match_vector(name, count)
        
    def skip_to(self, query, max_lines=None):
        raise NotImplementedError()
    
    def skip_to_group_end(self):
        raise NotImplementedError()
    
    def tell(self):
        raise NotImplementedError()

    def seek(self, offset, whence=0):
        raise NotImplementedError()