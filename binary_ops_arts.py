import struct

def read_string(file, length):
    str_bytes = bytearray(file.read(length))
    if b'\x00' in str_bytes:
        str_bytes = str_bytes[:str_bytes.index(b'\x00')]
    return str_bytes.decode("utf-8")