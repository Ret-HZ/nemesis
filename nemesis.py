# MIT License
#
# Copyright (c) 2021 Christopher Holzmann Pérez
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



from typing import OrderedDict
from binary_reader import BinaryReader
import argparse
import json
import zlib
import os



def extractREGFILE (path, game):
    metadata = OrderedDict()

    f = open(path, "rb")
    reader = BinaryReader(f.read())
    if reader.read_str(4) != 'RGF.':
        raise Exception('Incorrect magic. Expected RGF.')
    
    if game == "X":
        badCombinations = badCombinationsX
    elif game == "XP":
        badCombinations = badCombinationsXProto
    elif game == "X2":
        badCombinations = badCombinationsX2

    #Create unpack folder
    unpackFolderPath = path + ".unpack"
    if not os.path.exists(unpackFolderPath):
        os.makedirs(unpackFolderPath)

    regfileSize = reader.read_uint32()
    ptrAudioContainer = reader.read_uint32()
    folderAmount = reader.read_uint32()
    reader.seek(reader.pos() + 0x10)


    #Get folder info
    for folder in range(folderAmount):
        folderName = reader.read_str(0xA)
        metadata[folderName] = dict()

        #Skies of Deception
        if game == "X" or game == "XP":
            folderUnknown1 = reader.read_uint16()
            folderUnknown2 = reader.read_uint16()
            folderUnknown3 = reader.read_uint16()
            reader.seek(reader.pos() + 0x14) #Skip the 1 and the padding, always the same
            folderUnknown4 = reader.read_uint16()
            metadata[folderName]["folderUnknown1"] = folderUnknown1
            metadata[folderName]["folderUnknown2"] = folderUnknown2
            metadata[folderName]["folderUnknown3"] = folderUnknown3
            metadata[folderName]["folderUnknown4"] = folderUnknown4


        fileAmount = reader.read_uint16() #Files in the folder
        ptrFileSection = reader.read_uint32()
        folderUnknown5 = reader.read_uint16()
        folderUnknown6 = reader.read_uint16()
        metadata[folderName]["folderUnknown5"] = folderUnknown5
        metadata[folderName]["folderUnknown6"] = folderUnknown6


        #Create folder
        folderPath = unpackFolderPath + "/" + folderName
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        print ("Folder", folderName, "(" + str(fileAmount) + " files)")
        metadata[folderName]["Files"] = dict()

        #Extract files
        if fileAmount > 0:
            posFolderTable = reader.pos()
            reader.seek(ptrFileSection)

            for i in range(fileAmount):
                fileName = reader.read_str(0xC)
                metadata[folderName]["Files"][fileName] = dict()

                fileUnknown1 = reader.read_int16()
                fileUnknown2 = reader.read_uint16()
                metadata[folderName]["Files"][fileName]["fileUnknown1"] = fileUnknown1
                metadata[folderName]["Files"][fileName]["fileUnknown2"] = fileUnknown2 #Possible ID

                if [fileUnknown1, fileUnknown2] in badCombinations:
                    print("Bad combination. Dummy file", fileName)
                    fileData = bytearray()
                else:
                    fileSize = reader.read_uint32() - 0x4
                    fileData = reader.read_bytes(fileSize)
                    try: #Check header and attempt decompression
                        readertemp = BinaryReader(fileData)
                        magic = readertemp.read_str(4)
                        if magic == "DEF.":
                            metadata[folderName]["Files"][fileName]["Compressed"] = True
                            readertemp.seek(0x10)
                            compressedFile = readertemp.read_bytes(fileSize-0x10)
                            fileData = zlib.decompress(compressedFile)
                        else:
                            metadata[folderName]["Files"][fileName]["Compressed"] = False
                    except:
                        metadata[folderName]["Files"][fileName]["Compressed"] = False
                    

                savePath = folderPath + "/" + fileName
                with open(savePath , 'wb') as file:
                    file.write(fileData)
                    file.close()
            
            reader.seek(posFolderTable)
    

    #Extract audio section
    print ("Extracting raw audio section...")
    reader.seek(ptrAudioContainer)
    audioSection = reader.read_bytes(reader.size()-ptrAudioContainer)
    with open(unpackFolderPath + "/audio_section.dat" , 'wb') as file:
        file.write(audioSection)
        file.close()


    #Save metadata
    print("Saving metadata...")
    with open(unpackFolderPath + "/metadata.json" , 'w') as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)
        file.close()



# Any of these combinations ([fileUnknown1, fileUnknown2]) correspond to a dummy file without size or data
badCombinationsX = [
    [-256, 1280],
]

badCombinationsXProto = [
    [-256, 1276],
]

badCombinationsX2 = [
    [0, 1780],
    [-256, 1781],
    [-256, 7399],
    [-256, 7400],
    [-256, 7401],
    [-256, 7402],
    [-256, 7403],
    [256, 1772],
    [256, 1773],
]



if __name__ == '__main__':
    print(r'''
███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗
████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝''' +'\n')
    print("Ace Combat's REGFILE.CDI unpacker\n\n")
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='Input file (REGFILE.CDI) to unpack', type=str)
    parser.add_argument("-g", "--game", required=False, help='X = Ace Combat X: Skies of Deception, XP = Ace Combat X: Skies of Deception [16-05-2006 Prototype], X2 = Ace Combat: Joint Assault')
    args = parser.parse_args()

    path = args.input
    game = args.game
    if game:
        game = game.upper()

    if os.path.isfile(path):
        while game not in ["X", "XP", "X2"]:
            game = input("Select origin game:\nX  = Ace Combat X: Skies of Deception\nXP = Ace Combat X: Skies of Deception [16-05-2006 Prototype]\nX2 = Ace Combat: Joint Assault\n\nGame: ").upper()
        extractREGFILE(path, game)