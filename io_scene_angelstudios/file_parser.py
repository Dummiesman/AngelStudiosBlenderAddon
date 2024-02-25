import shlex

class FileParser:
    def __init__(self, lines):
        self.__current_line = 0
        self.__lines = lines
        self.__line_count = len(lines)
        
    def parse_float(self, str):
        if str == "-1.#QNAN0" or str == "1.#QNAN0":
            return float('nan')
        else:
            return float(str)
    
    def read_line(self):
        line = self.__lines[self.__current_line]
        self.__current_line += 1
        return line

    def read_tokens(self):
        return shlex.split(self.read_line())
    
    def read_int(self):
        tok = self.read_tokens()
        if len(tok) < 2:
            raise Exception(f"Failed to parse integer at line {self.__current_line} : {tok}")
        return int(tok[1])
        
    def read_float(self):
        tok = self.read_tokens()
        if len(tok) < 2:
            raise Exception(f"Failed to parse float at line {self.__current_line} : {tok}")
        return self.parse_float(tok[1])
        
    def read_int_array(self):
        tok = self.read_tokens()
        if len(tok) < 1:
            raise Exception(f"Failed to parse int array at line {self.__current_line} : {tok}")
        return [int(f) for f in tok[1:]]
        
    def read_float_array(self):
        tok = self.read_tokens()
        if len(tok) < 1:
            raise Exception(f"Failed to parse float array at line {self.__current_line} : {tok}")
        return [self.parse_float(f) for f in tok[1:]]
        
    def skip_to(self, query, max_lines=None):
        max_line = self.__line_count
        if max_lines is not None:
            max_line = min(self.__line_count, self.__current_line + max_lines)
            
        query_list = None
        if isinstance(query, str):
            query_list = [query]
        elif isinstance(query, list) or isinstance(query, tuple):
            query_list = query
        else:
            raise Exception("skip_to expects string or list/tuple query")
        
        for x in range(self.__current_line, max_line):
            tokens = self.__lines[x].split()
            if len(tokens) > 0 and tokens[0] in query_list:
                self.__current_line = x
                return True
                
        return False
    
    def skip_to_group_end(self):
        return self.skip_to("}")
    
    def tell(self):
        return self.__current_line

    def seek(self, offset, whence=0):
        if whence == 0:
            self.__current_line = offset
        elif whence == 1:
            self.__current_line = offset + self.__current_line
        elif whence == 2:
            self.__current_line = self.__line_count + offset
        self.__current_line = min(self.__current_line, self.__line_count)