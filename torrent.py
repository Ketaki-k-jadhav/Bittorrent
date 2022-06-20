import math
import hashlib
import sys
import time
from bcoding import bencode, bdecode
import logging
import os

class Torrent(object):
    def __init__(self,path):
        self.file_names = []
        self.is_multi_file=False
        self.bitfield = []

        try:
            f=open(path,"rb")
            self.torrent_file = bdecode(f)
            print("Successfully decoded torrent file", path)
        except:
            print("Unable to open torrent file...")
            sys.exit()
        
        if b'encoding' in self.torrent_file.keys() :
            self.encoding = self.torrent_file[b'encoding'].decode()
        else:
            self.encoding = 'UTF-8'
        
        self.piece_length =self.torrent_file['info']['piece length']
        self.pieces = self.torrent_file['info']['pieces']
        self.total_lenth = self.initialize_files()
        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)
        self.downloaded_length = 0
        self.raw_info_hash = bencode(self.torrent_file['info'])
        self.info_hash = hashlib.sha1(self.raw_info_hash).digest()
        self.peer_id = self.generate_peer_id()
        self.announce_list = self.get_trackers()
        for i in range( self.number_of_pieces ):
            self.bitfield.append( 0 )
        
    #structure of info:dict_keys(['length', 'name', 'piece length', 'pieces'])
    def initialize_files(self):
        self.total_length = 0
        root = self.torrent_file['info']['name']
        #for multi-file torrent files
        if 'files' in self.torrent_file['info']:
            self.is_multi_file=True
            if not os.path.exists(root):
                os.mkdir(root)
            for file in self.torrent_file['info']['files']:
                path_file = os.path.join(root, *file["path"])
                if not os.path.exists(os.path.dirname(path_file)):
                    os.makedirs(os.path.dirname(path_file))
                self.file_names.append({"path": path_file , "length": file["length"]})
                self.total_length += int(file["length"])
        #for single file torrent files
        else:
            self.file_names.append({"path": root , "length": self.torrent_file['info']['length']})
            self.total_length = self.torrent_file['info']['length']

    def get_trackers(self):
        if 'announce-list' in self.torrent_file:
            return self.torrent_file['announce-list']
        else:
            return self.torrent_file['announce']

    def generate_peer_id(self):
        seed = str(time.time())
        return hashlib.sha1(seed.encode('utf-8')).digest()  

    def calculate_piece_length( self, index_number ):
        if index_number == self.number_of_pieces-1:
            return self.total_length-self.piece_length * index_number
        else:
            return self.piece_length
        
   
