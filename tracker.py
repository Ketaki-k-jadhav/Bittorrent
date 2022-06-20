import requests
import struct
import random
import errno
from time import sleep
from bcoding import bdecode
import socket
from urllib.parse import urlparse
from socket import *
import traceback
import torrent
from threading import Thread
from torrent import *

class http_tracker():
    def __init__(self,torrent,tracker_url):
        self.params={
        'info_hash': torrent.info_hash,
        'peer_id': torrent.peer_id,
        'uploaded': 0,
        'downloaded': 0,
        'port': 6881,
        'left': torrent.total_length,
        'event': 'started',
        'compact': 1
        }
        self.tracker_url=tracker_url
        self.peers_list=[]
        self.peer_data={}
        self.complete=None
        self.incomplete=None
        self.interval=None

    def http_request(self):
        bencoded_response=None
        attempt=0
        flag=0
        while attempt<15:
            print("Attempt number {} for http request to {}".format(attempt+1,self.tracker_url))
            try:
                bencoded_response = requests.get(self.tracker_url, self.params, timeout=2 )
                # decode the bencoded dictionary to python ordered dictionary 
                raw_response_dict = bdecode(bencoded_response.content)
                #print(raw_response_dict)
                if raw_response_dict !=None:
                    flag=1
                    break
            except Exception as error_msg:
                pass
            attempt+=1
        
        if flag==0:
            print("http request to tracker {} failed".format(self.tracker_url))
            return -1

        if flag==1:
            if 'peers' in raw_response_dict:
                raw_peers_data = raw_response_dict['peers']
                for i in range(len(raw_peers_data)):
                    peer_list=raw_peers_data[i]
                    if type(peer_list)!=dict:
                        raw_peers_list = [raw_peers_data[i : 6 + i] for i in range(0, len(raw_peers_data), 6)]
                        for raw_peer_data in raw_peers_list:
                            peer_IP = ".".join(str(int(a)) for a in raw_peer_data[0:4])
                            peer_port = raw_peer_data[4] * 256 + raw_peer_data[5]
                            self.peers_list.append((peer_IP, peer_port))
                    else:
                        peer_IP =peer_list['ip']
                        peer_port = peer_list['port']
                        self.peers_list.append((peer_IP, peer_port))
           
                if 'complete' in raw_response_dict:
                    self.complete = raw_response_dict['complete']
                if 'incomplete' in raw_response_dict:
                    self.incomplete = raw_response_dict['incomplete']
                if 'interval' in raw_response_dict:
                    self.interval = raw_response_dict['interval']
                self.peer_data = {'interval' : self.interval, 'peers' : self.peers_list,
                         'leechers' : self.incomplete, 'seeders'  : self.complete}

            return self.peer_data

class udp_tracker():
    def __init__(self,torrent,tracker_url):
        self.params={
        'info_hash': torrent.info_hash,
        'peer_id': torrent.peer_id,
        'uploaded': 0,
        'downloaded': 0,
        'port': 6881,
        'left': torrent.total_length,
        'event': 'started',
        'compact': 1
        }
        self.tracker_url=tracker_url
        self.ip=None
        self.port=None
        self.peer_list=[]
        self.peer_data={}
        self.connection_id = 0x41727101980                       
        self.action = 0x0                                            
        self.transaction_id = int(random.randrange(0, 255))  
    
    def udp_request(self):
        temp_peer_data={}
        temp_peer_list=[]
        flag=0
        try:
            self.sock = socket(AF_INET, SOCK_DGRAM) 
            self.sock.settimeout(5)
            self.tracker_url=urlparse(self.tracker_url)
            self.ip=gethostbyname(self.tracker_url.hostname)
            self.port=self.tracker_url.port
            connection_payload = self.udp_connection_payload()
            self.connection_id = self.udp_connection_request(connection_payload)
            announce_payload = self.udp_announce_payload()
            self.raw_announce_reponse = self.udp_announce_request(announce_payload)
            temp_peer_data=self.parse_udp_tracker_response(self.raw_announce_reponse)
            temp_peer_list=self.peer_data['peers']
            flag=1
            
        except:
            pass
        if flag==1:
            self.peer_data.update(temp_peer_data)
            self.peer_list.append(temp_peer_list)
            return self.peer_data 
        else:
            print("udp request to tracker {} failed".format(self.tracker_url))
            return -1

    def udp_connection_payload(self):
        conn_request  = struct.pack("!q", self.connection_id)     # first 8 bytes : connection_id
        conn_request += struct.pack("!i", self.action)            # next 4 bytes  : action
        conn_request += struct.pack("!i", self.transaction_id)    # next 4 bytes  : transaction_id
        return conn_request
    
    def udp_connection_request(self,connection_payload):
        self.sock.sendto(connection_payload, (self.ip, self.port))
        try:
            raw_connection_data, conn = self.sock.recvfrom(2048)
            return self.parse_connection_response(raw_connection_data)
        except :
            print('UDP tracker connection request failed')
       
    def parse_connection_response(self, raw_connection_data):
        if(len(raw_connection_data) < 16):
            print('UDP tracker wrong reponse length of connection ID !')
        
        response_action = struct.unpack_from("!i", raw_connection_data)[0]       
        
        response_transaction_id = struct.unpack_from("!i", raw_connection_data, 4)[0]
        if(response_transaction_id != self.transaction_id):
            print('UDP tracker wrong response transaction ID !')
        
        reponse_connection_id = struct.unpack_from("!q", raw_connection_data, 8)[0]
        return reponse_connection_id
    
   
    def udp_announce_payload(self):
        self.action = 0x1            
        conn_id =  struct.pack("!q", self.connection_id)    
        action= struct.pack("!i", self.action)  
        trans_id= struct.pack("!i", self.transaction_id)  
        info_hash= struct.pack("!20s", self.params['info_hash'])
        peer_id= struct.pack("!20s", self.params['peer_id'])         
        downloaded= struct.pack("!q", self.params['downloaded'])
        left= struct.pack("!q", self.params['left'])
        uploaded= struct.pack("!q", self.params['uploaded']) 
        event= struct.pack("!i", 0x2) 
        my_ip= struct.pack("!i", 0x0) 
        random_key= struct.pack("!i", int(random.randrange(0, 255)))
        peer_numbers= struct.pack("!i", -1)                   
        response_port= struct.pack("!H", self.params['port'])   
        announce_payload=(conn_id+action+trans_id+info_hash+peer_id+downloaded+left+uploaded+event+my_ip+
        random_key+peer_numbers+response_port)
        return announce_payload

   
    def udp_announce_request(self, announce_payload):
        raw_announce_data = None
        attempt = 0
        while(attempt < 10):
            try:
                self.sock.sendto(announce_payload, (self.ip, self.port))    
                raw_announce_data, conn = self.sock.recvfrom(2048)
                break
            except:
                error_log =  ' failed announce request attempt ' + str(attempt + 1)
                print(error_log)
            attempt = attempt + 1
        return raw_announce_data

    
    def parse_udp_tracker_response(self, raw_announce_reponse):
        if(len(raw_announce_reponse) < 20):
            print('Invalid response length in announcing!')
        response_action = struct.unpack_from("!i", raw_announce_reponse)[0]     
        response_transaction_id = struct.unpack_from("!i", raw_announce_reponse, 4)[0]
        if response_transaction_id != self.transaction_id:
            print('The transaction id in annouce response do not match')
        
        offset = 8
        self.interval = struct.unpack_from("!i", raw_announce_reponse, offset)[0]
        offset = offset + 4
        self.leechers = struct.unpack_from("!i", raw_announce_reponse, offset)[0] 
        offset = offset + 4
        self.seeders = struct.unpack_from("!i", raw_announce_reponse, offset)[0] 
        offset = offset + 4
        self.peers_list = []
        while(offset != len(raw_announce_reponse)):
          
            raw_peer_data = raw_announce_reponse[offset : offset + 6]    
            
            peer_ip = ".".join(str(int(a)) for a in raw_peer_data[0:4])
            
            peer_port = raw_peer_data[4] * 256 + raw_peer_data[5]
           
            self.peers_list.append((peer_ip, peer_port))
            offset = offset + 6
        self.peer_data = {'interval' : self.interval, 'peers': self.peers_list,
                     'leechers' : self.leechers, 'seeders'  : self.seeders}

        if(len(self.peer_data['peers']))==0:
            print("peer ip and port are not received from the tracker")
    
        return self.peer_data


    
class Tracker():
    def __init__(self,torrent):
        self.tracker_urls=[]
        self.peer_data={}
        self.peer_list=[]
        for i in range(len(torrent.announce_list)):
            self.tracker_urls.append(torrent.announce_list[i][0])
    
    def get_peers_from_trackers(self,torrent):
        thread_pool = []
        for tracker_url in self.tracker_urls:
            th = Thread( target = self.get_peers, args=( torrent, tracker_url ))
            thread_pool.append(th)
            th.start()

        for i in thread_pool:
            i.join()
        return self

    def get_peers( self, torrent, tracker_url ):
        if str.startswith(tracker_url,"http"):
            response=http_tracker(torrent,tracker_url).http_request()
            if response !=-1:
                self.peer_data.update(response)
                for p in response['peers']:
                    if p not in self.peer_list:
                        self.peer_list.append(p)
                
        if str.startswith(tracker_url,"udp"):
            response=udp_tracker(torrent,tracker_url).udp_request()
        
            if response !=-1:
                self.peer_data.update(response)
                for p in response['peers']:
                    if p not in self.peer_list:
                        self.peer_list.append(p)
