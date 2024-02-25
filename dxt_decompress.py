"""
S3TC DXT1/DXT5 Texture Decompression
Original C++ code https://github.com/Benjamin-Dobell/s3tc-dxt-decompression
"""

import struct

class DXTBuffer:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.block_count_x = (self.width + 3) // 4
        self.block_count_y = (self.height + 3) // 4

    def DXT5DecompressBlock(self, x, y, width, height, block, image):
        alpha0 = block[0]
        alpha1 = block[1]

        alphaCode1 = block[4] | (block[5] << 8) | (block[6] << 16) | (block[7] << 24)
        alphaCode2 = block[2] | (block[3] << 8)

        color0 = struct.unpack('<H', block[8:10])[0]
        color1 = struct.unpack('<H', block[10:12])[0]

        code = struct.unpack('<L', block[12:16])[0]
        
        temp = (color0 >> 11) * 255 + 16
        r0 = ((temp//32 + temp)//32)
        temp = ((color0 & 0x07E0) >> 5) * 255 + 32
        g0 = ((temp//64 + temp)//64)
        temp = (color0 & 0x001F) * 255 + 16
        b0 = ((temp//32 + temp)//32)
    
        temp = (color1 >> 11) * 255 + 16
        r1 = ((temp//32 + temp)//32)
        temp = ((color1 & 0x07E0) >> 5) * 255 + 32
        g1 = ((temp//64 + temp)//64)
        temp = (color1 & 0x001F) * 255 + 16
        b1 = ((temp//32 + temp)//32)

        for j in range(4):
            for i in range(4):
                alphaCodeIndex = 3*(4*j+i)
                alphaCode = 0

                if alphaCodeIndex <= 12:
                    alphaCode = (alphaCode2 >> alphaCodeIndex) & 0x07
                elif alphaCodeIndex == 15:
                    alphaCode = (alphaCode2 >> 15) | ((alphaCode1 << 1) & 0x06)
                else:
                    alphaCode = (alphaCode1 >> (alphaCodeIndex - 16)) & 0x07

                finalAlpha = 0
                if alphaCode == 0:
                    finalAlpha = alpha0
                elif alphaCode == 1:
                    finalAlpha = alpha1
                else:
                    if alpha0 > alpha1:
                        finalAlpha = ((8-alphaCode)*alpha0 + (alphaCode-1)*alpha1)//7
                    else:
                        if alphaCode == 6:
                            finalAlpha = 0
                        elif alphaCode == 7:
                            finalAlpha = 255
                        else:
                            finalAlpha = ((6-alphaCode)*alpha0 + (alphaCode-1)*alpha1)//5

                colorCode = (code >> 2*(4*j+i)) & 0x03
                finalColor = None
                match colorCode:
                    case 0:
                        finalColor = (r0, g0, b0, finalAlpha)
                    case 1:
                        finalColor = (r1, g1, b1, finalAlpha)
                    case 2:
                        finalColor = ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3, finalAlpha)
                    case 3:
                        finalColor = ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3, finalAlpha)


                if x + i < width:
                    image_byte_index = ((y + j)*width + (x + i)) * 4
                    image[image_byte_index+0] = finalColor[0]
                    image[image_byte_index+1] = finalColor[1]
                    image[image_byte_index+2] = finalColor[2]
                    image[image_byte_index+3] = finalColor[3]


    def DXT5DecompressFile(self, file, image):
        for y in range(self.block_count_y):
            for x in range(self.block_count_x):
                block_data = file.read(16)
                self.DXT5DecompressBlock(x*4, y*4, self.width, self.height, block_data, image)

    def DXT5Decompress(self, file):
        image_data = bytearray(self.width * self.height * 4)
        self.DXT5DecompressFile(file, image_data)
        return image_data


    def DXT1DecompressBlock(self, x, y, width, height, block, image):
        color0 = struct.unpack('<H', block[0:2])[0]
        color1 = struct.unpack('<H', block[2:4])[0]
        code = struct.unpack('<L', block[4:8])[0]

        temp = (color0 >> 11) * 255 + 16
        r0 = ((temp//32 + temp)//32) & 0xFF
        temp = ((color0 & 0x07E0) >> 5) * 255 + 32
        g0 = ((temp//64 + temp)//64) & 0xFF
        temp = (color0 & 0x001F) * 255 + 16
        b0 = ((temp//32 + temp)//32) & 0xFF
    
        temp = (color1 >> 11) * 255 + 16
        r1 = ((temp//32 + temp)//32) & 0xFF
        temp = ((color1 & 0x07E0) >> 5) * 255 + 32
        g1 = ((temp//64 + temp)//64) & 0xFF
        temp = (color1 & 0x001F) * 255 + 16
        b1 = ((temp//32 + temp)//32) & 0xFF

        for j in range(4):
            for i in range(4):
                finalColor = None
                positionCode = (code >>  2*(4*j+i)) & 0x03

                match positionCode:
                    case 0:
                        finalColor = (r0, g0, b0, 255)
                    case 1:
                        finalColor = (r1, g1, b1, 255)
                    case 2:
                        if color0 > color1:
                            finalColor = ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3, 255)
                        else:
                            finalColor = ((r0+r1)//2, (g0+g1)//2, (b0+b1)//2, 255)
                    case 3:
                        if color0 > color1:
                            finalColor = ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3, 255)
                        else:
                            finalColor = (0, 0, 0, 255)

                if x + i < width:
                    image_byte_index = ((y + j)*width + (x + i)) * 4
                    image[image_byte_index+0] = finalColor[0]
                    image[image_byte_index+1] = finalColor[1]
                    image[image_byte_index+2] = finalColor[2]
                    image[image_byte_index+3] = finalColor[3]


    def DXT1DecompressFile(self, file, image):
        for y in range(self.block_count_y):
            for x in range(self.block_count_x):
                block_data = file.read(8)
                self.DXT1DecompressBlock(x*4, y*4, self.width, self.height, block_data, image)

    def DXT1Decompress(self, file):
        image_data = bytearray(self.width * self.height * 4)
        self.DXT1DecompressFile(file, image_data)
        return image_data