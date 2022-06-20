import os
import sys
from download import *

def info():
    print("Welcome to command line Bittorrent client")
    print("To download a torrent file through our bittorrent client follow the instructions:")
    print("Enter command as: python3 main.py <flag>< download_location >< flag >< max_peers >< torrent_file_path> ")
    print("Flags :")
    print(" -d : downloading at desired location ")
    print(" -m : set max peers ")

def check_file_existence(path):
    try:
        f=open(path,"rb")
    except:
        print("Unable to open torrent file "+path)
        print("Please give the correct path !!")
        sys.exit()

if len( sys.argv ) < 2:
    info()
    sys.exit()

if len( sys.argv ) == 2:
    torrent_file_name = sys.argv[1]
    max_peers = 55
    download_path = "."

if len( sys.argv) == 3 or len( sys.argv) == 5 or len( sys.argv) > 6 :
    print("Incorrect arguments..!!")
    info()
    sys.exit()

if len( sys.argv) == 4:
    if sys.argv[1] != "-d" and sys.argv[1] != "-m":
        info()
        sys.exit()
    
    torrent_file_name = sys.argv[3]
    if sys.argv[1] == "-d":
        max_peers = 55
        download_path = sys.argv[2]

    if sys.argv[1] == "-m":
        max_peers = int( sys.argv[2])
        download_path = "."
    
if len( sys.argv ) == 6:
    if  sys.argv[1] != "-d" and sys.argv[1] != "-m" and sys.argv[3] != "-d" and sys.argv[3] != "-m":
        info()
        sys.exit()
    
    if sys.argv[1] == sys.argv[3]:
        info()
        sys.exit()

    torrent_file_name = sys.argv[5]
    if sys.argv[1] == "-d":
        max_peers = 55
        download_path = sys.argv[2]

    if sys.argv[1] == "-m":
        max_peers = int( sys.argv[2])
        download_path = "."

    if sys.argv[3] == "-d":
        max_peers = 55
        download_path = sys.argv[4]

    if sys.argv[3] == "-m":
        max_peers = int( sys.argv[4])
        download_path = "."

check_file_existence( torrent_file_name )
down = Download( torrent_file_name, max_peers, download_path )
down.download()
print("File Downloaded Successfully")
