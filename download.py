from torrent import *
from tracker import *
from threading import Thread
from peer import *
import os
import random
import time

MAX_VALUE = 1000
MIN_VALUE = 0

class Download():
    def __init__( self, torrent_file_name, max_peers, download_path ):
        self.torrent = Torrent( torrent_file_name )
        self.tracker = Tracker( self.torrent )
        self.max_peers = max_peers

        self.file_size = self.torrent.total_length
        self.number_of_pieces = self.torrent.number_of_pieces
        self.bitfield = []
        for i in range( self.number_of_pieces):
            self.bitfield.append(0)

        self.piece_not_downloaded = []
        for i in range( self.number_of_pieces ):
            self.piece_not_downloaded.append(i)

        
        self.download_path = download_path
        self.file_name = self.torrent.file_names[0]['path']
        self.file_name = self.download_path + "/" + self.file_name
        self.file_ptr = os.open( self.file_name , os.O_RDWR | os.O_CREAT )
        self.write_null()

        self.tracker.get_peers_from_trackers( self.torrent )

        self.peer_list = self.tracker.peer_list
        self.all_peers = []
        self.active_peers = []
        for ip, port in self.peer_list:
            p = Peer( ip, port, self.torrent.info_hash, self.torrent.peer_id )
            self.all_peers.append(p)
    
    def do_handshake_bitfield( self, p, j ):
        if p.handshake() == True:
            if( len( self.active_peers ) < self.max_peers ):
                self.active_peers.append(p)
                p.initialize_bitfield()
                for i in range( self.number_of_pieces ):
                    self.bitfield[i] += p.bitfield_pieces[i]

    def connect_peers( self ):
        thread_pool = []
        j = 0
        for p in self.all_peers:
            th = Thread( target =( self.do_handshake_bitfield ) , args=( p, j ) )
            thread_pool.append(th)
            th.start()
        
        for i in thread_pool:
            i.join()

    def write_null( self ):
        buff = 8192
        data_size = self.file_size
        while data_size > 0:
            if data_size >= buff:
                data_size = data_size -buff
                data = b'\x00' * buff
            else:
                data = b'\x00' * data_size
                data_size = 0
            os.write(  self.file_ptr, data )
    
    def download_strategy( self, peer_req, piece_index, piece_length ):
        is_piece_downloaded, data = peer_req.download_piece( piece_index, piece_length, self.torrent )
        if is_piece_downloaded:
            self.piece_not_downloaded.remove( piece_index)
            os.lseek( self.file_ptr , piece_index* self.torrent.piece_length , os.SEEK_SET)
            os.write( self.file_ptr , data )
            
        if is_piece_downloaded == False :
            self.bitfield[piece_index] = MIN_VALUE

    def download( self ):
        print("connecting to peers")
        self.connect_peers()
        print( len(self.active_peers), "peers connected..!!")

        thread_down = Thread( target= self.show_progress, args=( 2,2))
        thread_down.start()

        flag_for_end_game = 0
        while len( self.piece_not_downloaded ) :
            pieces = self.pieces_selection_startergy()
            peer_list = self.peer_selection_startergy( pieces )
            temp1 = len( self.piece_not_downloaded )
            downloading_thread_pool = []

            for k in self.active_peers:
                if k not in peer_list:
                    k.send_keep_alive()

            for i in range( min(len(pieces), len( peer_list )) ):
                piece_index  = pieces[i]
                req_peer     = peer_list[i]
                piece_length = self.torrent.calculate_piece_length( piece_index )

                downloading_thread = Thread( target = self.download_strategy, args=( req_peer, piece_index, piece_length ))
                downloading_thread_pool.append(downloading_thread)
                downloading_thread.start()

            for downloading_thread in downloading_thread_pool:
                downloading_thread.join()

            if( len( self.active_peers ) < self.max_peers ):
                self.connect_peers()

            random.shuffle( self.active_peers )
        os.close( self.file_ptr )

    def end_game( self, piece_index, piece_length, req_peer ):
        if piece_index not in self.piece_not_downloaded:
            return
        is_piece_downloaded, data = req_peer.download_piece( piece_index, piece_length, self.torrent )
        if is_piece_downloaded:
            if piece_index in self.piece_not_downloaded:
                self.piece_not_downloaded.remove( piece_index)
                os.lseek( self.file_ptr , piece_index* self.torrent.piece_length , os.SEEK_SET)
                os.write( self.file_ptr , data )

    def pieces_selection_startergy( self ):
        i = 0
        pieces = []
        while i < len( self.piece_not_downloaded ) and i < len( self.active_peers ) and i < 20 :
            piece_index = self.bitfield.index( min(self.bitfield) )
            self.bitfield[ piece_index ] = MAX_VALUE
            pieces.append( piece_index )
            i += 1
        return pieces

    def peer_selection_startergy( self, pieces ):
        random.shuffle( self.active_peers )
        peer_list = []
        for i in range( min( len(pieces) , len( self.active_peers ) ) ):
            index = pieces[i]
            for j in self.active_peers:
                if j not in peer_list and j.bitfield_pieces[index] == 1:
                    peer_list.append(j)
        return peer_list

    def peer_selection_for_end_game( self, piece_index ):
        random.shuffle( self.active_peers )
        peer_list = []
        i = 0
        for p in self.active_peers:
            if p.bitfield_pieces[ piece_index] == 1:
                peer_list.append(p)
                i += 1
            if i == 5 :
                break
        return peer_list
            
    def show_progress( self,i,j ):
        temp = 0
        sleep(i)
        t1 = time.time()

        while len( self.piece_not_downloaded ):
            os.system("clear")
            speed = self.torrent.downloaded_length - temp
            temp = self.torrent.downloaded_length
            perc = ( self.number_of_pieces - len(self.piece_not_downloaded) )/self.number_of_pieces  * 100
            print("[{0}{1}] {2}%".format("#" * round(perc), "." * ( 100-round(perc)) , round(perc, 2)))
            print(
                "Downloading from {} peers at {} KBps.".format(
                    len( self.active_peers ), round( speed / 2048, 2)
                )
            )
            sleep(j)
        
        t2 = time.time()
        os.system("clear")
        print("[{0}] 100%".format("#" * 100 ) )
        print("Downloading complete at avg speed of", round( self.torrent.downloaded_length /( 1024*( t2 -t1 )), 2 ),"KBps" )
        return