import struct

def read_string(file, length):
    str_bytes = bytearray(file.read(length))
    if b'\x00' in str_bytes:
        str_bytes = str_bytes[:str_bytes.index(b'\x00')]
    return str_bytes.decode("utf-8")

def write_string(file, s, length):
    str_bytes = s.encode("utf-8")
    str_bytes = str_bytes[:length]  # truncate if too long
    str_bytes += b'\x00' * (length - len(str_bytes))  # pad with nulls
    file.write(str_bytes)