from socket import *
import struct
import time
from bitstring import BitArray

CONSTANT_HANDSHAKE_LEN = 68
BLOCK_LENGTH_CONS = 16384

KEEP_ALIVE      = None
CHOKE           = 0
UNCHOKE         = 1 
INTERESTED      = 2
UNINTERESTED    = 3
HAVE            = 4
BITFIELD        = 5
REQUEST         = 6
PIECE           = 7
CANCEL          = 8
PORT            = 9

MESSAGE_LENGTH_SIZE     = 4
MESSAGE_ID_SIZE         = 1

class Peer():
    def __init__( self, IP, Port, info_hash, client_peer_id ):

        self.peer_sock = socket( AF_INET, SOCK_STREAM )
        self.peer_sock.settimeout(3)
        self.IP = IP
        self.Port = Port
        self.unique_id = IP + ' ' +str(Port)
        self.max_peer = 55
        self.handshake_flag = False
        self.peer_connection = False
        self.protocol = "BitTorrent protocol"
        self.unique_id  = '(' + self.IP + ' : ' + str(self.Port) + ')'
        self.peer_id = None
        self.client_peer_id = client_peer_id
        self.info_hash = info_hash
        self.bitfield_pieces = []
        self.am_choking         = True              # client choking peer
        self.am_interested      = False             # client interested in peer
        self.peer_choking       = True              # peer choking client
        self.peer_interested    = False             # peer interested in clinet
        # keep alive timeout : 10 second
        self.keep_alive_timeout = 10
        # keep alive timer
        self.keep_alive_timer = None

    # For handshaking with peer
    def handshake( self ):
        if self.handshake_flag == True:
            return False
        # Create connection
        if self.create_connection() == False:
            return False
        handshake_message = self.build_handshake_message()
        #self.peer_sock.send( msg )
        self.send_data( handshake_message )
        raw_response = self.receive_data( CONSTANT_HANDSHAKE_LEN )
        if raw_response is None:
            return False
        a = self.handshake_response_validation( raw_response )
        if a is None:
            return False
        self.peer_id = a
        self.handshake_flag = True
        return True

    def create_connection( self ):
        try:
            self.peer_sock.connect(( self.IP, self.Port))
            self.peer_connection = True
            return True

        except:
            self.peer_connection = False
            return False

    def build_handshake_message( self ):
        reserved = 0x0000000000000000
        msg  = struct.pack("!B", len(self.protocol))
        msg += struct.pack("!19s", self.protocol.encode())
        msg += struct.pack("!Q", reserved)
        msg += struct.pack("!20s", self.info_hash)
        msg += struct.pack("!20s", self.client_peer_id )
        return msg

    def send_data( self, data ):
        data_len = 0
        n = len( data )
        while( data_len < n):
            try:
                data_len += self.peer_sock.send( data[data_len:])
            except:
                return False
        return True

    def receive_data( self, len_response ):
        if self.peer_connection == False:
            return

        peer_raw_data = b''
        recv_data_len = 0
        req_size = len_response

        while( recv_data_len < len_response ):
            try:
                chunk = self.peer_sock.recv( req_size )
            except:
                chunk = b''
            
            if( len(chunk) == 0):
                return None
            
            peer_raw_data += chunk
            req_size -= len(chunk)
            recv_data_len += len(chunk)

        return peer_raw_data


    def handshake_response_validation( self, raw_response ):

        len_of_response = len( raw_response)

        if( len_of_response != CONSTANT_HANDSHAKE_LEN ):
            return None

        peer_info_hash = raw_response[28:48]
        peer_id = raw_response[48:68]

        if( peer_info_hash != self.info_hash ):
            return None
        if( peer_id == self.client_peer_id ):
            return None

        return peer_id

    def create_response_message( self, message_length, message_id, message_payload ):
        message  = struct.pack("!I", message_length)
        if message_id != None:
            message += struct.pack("!B", message_id)
        if message_payload != None:
            message += message_payload
        return message

    def send_keep_alive( self ):
        message_length = 0
        message_id = None
        message = self.create_response_message( message_length, message_id, None )
        if self.send_data( message ):
            return True
        else:
            return False 

    def send_interested_message( self ):
        message_length = 1
        message = self.create_response_message( message_length, INTERESTED, None )
        if self.send_data( message):
            self.am_interested = True
            return True
        else:
            self.am_interested = False
            return False

    def send_request_message( self, piece_index, block_offset, block_length):
        message_length  = 13                                # 4 bytes message length
        message_id      = REQUEST                           # 1 byte message id
        payload         = struct.pack("!I", piece_index)    # 12 bytes payload
        payload        += struct.pack("!I", block_offset) 
        payload        += struct.pack("!I", block_length)
        message = self.create_response_message( message_length, REQUEST, payload )
        if self.send_data( message ):
            return True
        else:
            return False

    def send_cancel_message( self, piece_index, block_offset, block_length ):
        message_length  = 13                                # 4 bytes message length
        message_id      = CANCEL                           # 1 byte message id
        payload         = struct.pack("!I", piece_index)    # 12 bytes payload
        payload        += struct.pack("!I", block_offset) 
        payload        += struct.pack("!I", block_length)
        message = self.create_response_message( message_length, REQUEST, payload )
        if self.send_data( message ):
            return True
        else:
            return False

    def initialize_bitfield(self):
        if not self.handshake_flag:
            return self.bitfield_pieces

        flag = True
        while( flag ):
            response_message = self.pwm_response_handler()
            if response_message == None:
                flag = False

        return self.bitfield_pieces


    def pwm_response_handler(self ):
        response = self.recieve_peer_wire_message()
        if response == None:
            return None
        
        msg_length  = response[0]
        msg_id      = response[1]
        msg_payload = response[2]

        if( msg_length == 0 ):
            self.recieved_keep_alive()
        else:
            if msg_id == 0:
                self.peer_choking = True
            if msg_id == 1:
                self.peer_choking = False
            if msg_id == 2:
                self.peer_interested = True
            if msg_id == 3:
                self.peer_interested = False

            if msg_id == 5:
                self.bitfield_pieces = self.extract_bitfield( msg_payload )

        return response

    def extract_bitfield( self, message_payload ):
        bitfield_pieces = []
        for i, byte_value in enumerate( message_payload ):
            num = 128
            for j in range(8):
                if( num & byte_value ):
                    bitfield_pieces.append(1)
                else:
                    bitfield_pieces.append(0)
                num = num // 2
        return bitfield_pieces

    def recieve_peer_wire_message(self):
        raw_msg_length = self.receive_data( MESSAGE_LENGTH_SIZE )
        if raw_msg_length is None or len(raw_msg_length) < MESSAGE_LENGTH_SIZE:
            return None

        msg_length = struct.unpack_from("!I", raw_msg_length)[0]
        if msg_length == 0:
            return [msg_length, None, None]

        raw_msg_ID =  self.receive_data( MESSAGE_ID_SIZE)
        if raw_msg_ID is None:
            return None
        
        msg_id  = struct.unpack_from("!B", raw_msg_ID)[0]

        if msg_length == 1:
            return [ msg_length, msg_id, None]
       
        payload_length = msg_length - 1
        
        msg_payload = self.receive_data( payload_length )
        if msg_payload is None:
            return None
        
        self.keep_alive_timer = time.time()

        return [ msg_length, msg_id, msg_payload ]

    def recieved_keep_alive(self):
        self.keep_alive_timer = time.time()

    def is_peer_has_piece( self, piece_index ):
        try:
            if self.bitfield_pieces[piece_index] == 1:
                return True
            else:
                return False
        except:
            return False

    def check_download_condition( self):
        if self.handshake_flag != True:
            return False

        if self.am_interested != True:
            return False
        
        if self.peer_choking != False:
            return False
        
        return True

    # client interested
    # peer unchoke
    def download_piece(self, piece_index, piece_length, torrent ):
        if self.send_interested_message() == False:
            return False, None
        
        self.pwm_response_handler()
        if self.peer_choking == True:
            return False, None

        if self.is_peer_has_piece( piece_index ) == False:
            return False, None

        recieved_piece = b''  
        block_offset = 0 
        block_length = 0

        flag = 0
        while block_offset < piece_length:
            if piece_length - block_offset >= BLOCK_LENGTH_CONS :
                block_length = BLOCK_LENGTH_CONS
            else:
                block_length = piece_length - block_offset
            
            block_data = self.download_block( piece_index, block_offset, block_length )
            if block_data:
                flag = 0
                recieved_piece += block_data
                block_offset   += block_length
                torrent.downloaded_length += block_length 
            else:
                flag += 1
            
            if flag == 3 :
                return False, None
        
        print("successfully downloaded and validated piece", piece_index )
        return True, recieved_piece

    def download_block(self, piece_index, block_offset, block_length ):

        if self.check_download_condition() == False:
            return None
        
        if self.send_request_message( piece_index, block_offset, block_length) == False:
            return None
        response = self.recieve_peer_wire_message()

        if response == None:
            return None

        msg_id      = response[1]
        msg_payload = response[2]

        if msg_id != PIECE:
            return None

        recv_piece_index  = struct.unpack_from("!I", msg_payload, 0)[0]
        recv_block_offset = struct.unpack_from("!I", msg_payload, 4)[0]
        recv_block_data   = msg_payload[8:]

        if recv_piece_index  != piece_index :
            return None
        if recv_block_offset != block_offset:
            return None
        if len(recv_block_data) != block_length:
            return None

        return recv_block_data