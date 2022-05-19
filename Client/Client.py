import socket
import struct
import pickle
import os
from tkinter import *

host = "localhost"
port = 4561

class Command:
    command = ""
    payload = ""

# Adding Songs (and return SongID)
def addSong(songName, s):
    try:
        addCommand = Command()
        addCommand.command = "AddSong" + " " + songName.replace(' ','_')
        # ' ' is a divider
        
        music = open("socket-demo-with-GUI/Client/Song/" + songName + ".mp3", 'rb')
        addCommand.payload = music.read()
        music.close()
        
        packedData = pickle.dumps(addCommand)
        s.sendall(struct.pack("i", len(packedData)))
        s.sendall(packedData) # Send data

        replyLen = struct.unpack("i", s.recv(4))[0]
        data = bytearray()
        while (replyLen > len(data)):
            data += s.recv(replyLen - len(data))
        replyCommand = pickle.loads(data) # Receive the server reply
        
        ServerCommand = replyCommand.command.split(" ")
        if ServerCommand[0] == "SongAdded":
            SongID = ServerCommand[1]
            print("The song was successfully added as ID:", SongID)
            return SongID
    except Exception as e:
        print("Error occured: ", e)

# Download a song by songID in client: (and save it as songName.mp3)
def getSongByID(songID, songName, s):
    try:
        getCommand = Command()
        getCommand.command = "GetSong" + " " + str(songID) # " " is a divider
        packedData = pickle.dumps(getCommand)
        totalLen = len(packedData)

        s.sendall(struct.pack("i", totalLen))
        s.sendall(packedData)

        replyLen = struct.unpack("i", s.recv(4))[0]
        data = bytearray()
        while (replyLen > len(data)):
            data += s.recv(replyLen - len(data))

        replyCommand = pickle.loads(data)
        f = open("socket-demo-with-GUI/Client/Song/" + songName + ".mp3", "wb")
        f.write(replyCommand.payload)
        print("Song saved as " + songName + ".mp3")
        f.close()
    except Exception as e:
        print("Error occured: ", e)

# Remove a song from the server:
def removeSong(songID, s):
    try:
        removeCommand = Command()
        removeCommand.command = "RemoveSong" + " " + str(songID) # " " is a divider
        packedData = pickle.dumps(removeCommand)
        totalLen = len(packedData)

        s.sendall(struct.pack("i", totalLen))
        s.sendall(packedData)

        replyLen = struct.unpack("i", s.recv(4))[0]
        data = bytearray()
        while (replyLen > len(data)):
            data += s.recv(replyLen - len(data))

        replyCommand = pickle.loads(data)
        if replyCommand.command == "SongRemovedOK":
            print("The song(ID: " + str(songID)
                  + ") is successfully removed from sever.")
    except Exception as e:
        print("Error occured: ", e)

# Get a list of all avaliable song
def getSongList(s):
    getCommand = Command()
    getCommand.command = "GetSongList"
    packedData = pickle.dumps(getCommand)
    totalLen = len(packedData)

    s.sendall(struct.pack("i", totalLen))
    s.sendall(packedData)

    replyLen = struct.unpack("i", s.recv(4))[0]
    data = bytearray()
    while (replyLen > len(data)):
        data += s.recv(replyLen - len(data))
    replyCommand = pickle.loads(data)

    print("SongList is: ", replyCommand.payload)
    return replyCommand.payload

# Class for GUI
class Application():
    def __init__(self):
        global s
        self.root = Tk()
        self.frm = Frame(self.root)
        
        #Left
        self.frm_L = Frame(self.frm)

        Label(self.frm_L, text = ' ').pack()
        Label(self.frm_L, text = 'Local Song',
             font =('Arial',20)).pack()

        self.localsong_var = StringVar()
        self.localsong = Listbox(self.frm_L, width=40, height=20,
            listvariable = self.localsong_var)
        for a,b,files in os.walk("Song/"):
            for item in files:
                self.localsong.insert(END, item)
        self.localsong.pack()

        self.frm_L.pack(side=LEFT)

        #Mid
        self.frm_M = Frame(self.frm)
        Button(self.frm_M, text="Upload Song",
               command=self.addsong, width=30).pack(side=TOP)
        Button(self.frm_M, text="Download Song",
               command=self.getsong, width=30).pack(side=TOP)
        Label(self.frm_M, text = '\n\n\n\n\n\n\n\n\n\n').pack(side=TOP)
        self.frm_M.pack(side=LEFT)

        #Right
        self.frm_R = Frame(self.frm)
        
        Button(self.frm_R, text="Remove Song From Server",
               command=self.removesong, width=40).pack(side=TOP)
        Label(self.frm_R, text = 'Sever Song',
             font =('Arial',20)).pack()
        
        self.hostsong_var = StringVar()
        self.hostsong = Listbox(self.frm_R, width=40,
            height=20, listvariable = self.hostsong_var)
        self.hostsongList = getSongList(s)

        # Get all avaliable songs at start
        for item in self.hostsongList:
            self.thelist = str(item) + ". " + self.hostsongList[item] + ".mp3"
            self.hostsong.insert(END, self.thelist)
        self.hostsong.pack()
        
        self.songList_var = StringVar()
        self.songList = Listbox(self.frm_R, width=40,
            height=20, listvariable = self.songList_var)

        self.frm_R.pack(side=RIGHT)
        self.frm.pack()

    def addsong(self):
        songName = self.localsong.get(self.localsong.curselection())
        songName = songName.replace(".mp3","")
        songID = addSong(songName, s)
        self.hostsong.insert(END, songID + ". " + songName + ".mp3")

    def getsong(self):
        Song = self.hostsong.get(self.hostsong.curselection())
        songID = int(Song.split(". ")[0])
        songName = Song.split(". ")[1].replace(".mp3","")
        count = 0
        localsong = self.localsong_var.get().split(", ")
        for item in localsong:
            if songName in localsong[count]:
                print("The song is exist in local song")
                return
            count = count + 1
        getSongByID(songID, songName, s)
        self.localsong.insert(END, songName + ".mp3")

    def removesong(self):
        Song = self.hostsong.get(self.hostsong.curselection())
        songID = int(Song.split(". ")[0])
        count = 0
        hostsong = self.hostsong_var.get().split(", ")
        for item in hostsong:
            if str(songID)+". " in hostsong[count]:
                self.hostsong.delete(count)
            count = count + 1
        count = 0
        songlist = self.songList_var.get().split(", ")
        for item in songlist:
            if str(songID)+". " in songlist[count]:
                self.songList.delete(count)
            count = count + 1
        removeSong(songID, s)
        

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
    
root = Application()
mainloop()

s.close()
