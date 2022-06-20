# Bittorrent

## A simple command-line bittorrent client for downloading torrent files

This is a simple bittorrent command-line client written in python3 from sratch. It can download a torrent file and save the downloaded file in current working directory.You first need to wait for the program to connect to some peers first, then it starts downloading.
This tool can :

```
-Read and decode a torrent file
-Scrape UDP and HTTP trackers
-Connect to peers
-Request a block that you want
-Rarest piece first strategy for downloading
-Save a block temporarily in RAM, and when a piece is completely downloaded and validated, save it in hard drive
-Download single and multi-torrent files
-Write all relevant information about the torrent and downloading progress in a log file saved with same name as that of the torrent.
```

### Installation

Install all the dependancies required for the program, mentioned in [requirements.txt](https://github.com/Ketaki-k-jadhav/Bittorrent/blob/master/requirements.txt) using following command :

`pip3 install -r requirements.txt`

### Run the program
* Clone this repo
* Open terminal and type following command:
```
python3 main.py
```

### References

Following resources were extremely useful while doing this project:

* [Bittorrent Protocol Specification v1.0](https://wiki.theory.org/BitTorrentSpecification)

* [How to Write a Bittorrent Client, Part 1](http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/)

* [How to Write a Bittorrent Client, Part 2](http://www.kristenwidman.com/blog/71/how-to-write-a-bittorrent-client-part-2/)

* [Bittorrent Client](http://foss.coep.org.in/coepwiki/index.php/Bittorrent_Client)



### 
