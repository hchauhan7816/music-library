import socket
import threading
import struct
import pickle
import os

class Command:
    command = ""
    payload = ""

def loadSongDict():
    f = open("socket-demo-with-GUI/Server/Song/songList.txt", "r")
    songDict = {}
    for line in f:
        read = line.split(",")
        songDict[int(read[0])] = read[1].replace("\n","")
    f.close()
    return songDict

def saveSongDict(songDict):
    f = open("socket-demo-with-GUI/Server/Song/songList.txt", "w")
    songlist = []
    for key in songDict:
        songlist.append(str(key))
        songlist.append(",")
        songlist.append(songDict[key])
        songlist.append("\n")
    f.writelines(songlist)
    f.close()

# Class of Thread
class SocketThread(threading.Thread):
    
    def __init__(self, socketInstance):
        threading.Thread.__init__(self)
        self.mySocket = socketInstance
        global songDict
        
    def run(self):
        global songDict
        try:
            while (True):
                print("Reading initial length")
                a = self.mySocket.recv(4)
                print("Wanted 4 bytes got " + str(len(a)) + " bytes")

                if len(a) < 4:
                    raise Exception("Client closed socket, ending client thread")

                messageLength = struct.unpack('i', a)[0]
                print("Message Length: ", messageLength)
                data = bytearray()
                while messageLength > len(data):
                    data += self.mySocket.recv(messageLength - len(data))

                newCommand = pickle.loads(data)
                print("\nCommand is: ", newCommand.command.replace('_',' '))

             
                ClientCommand = newCommand.command.split(" ")
                # Divide the command to recognize it, " " is the divider

                # 1.Adding Songs:
                if ClientCommand[0] == "AddSong":
                    songName = ClientCommand[1].replace('_',' ')
                    #Get the Song Name, The space in song name is replaced by '_' in data transform
                    print("Adding song")

                    songID = 1;
                    for key in songDict:
                        songID = key + 1
                    # Result: ID of new song = ID of the final song + 1

                    music = open("socket-demo-with-GUI/Server/Song/" + str(songID) + ".mp3", 'wb')
                    print("Adding", str(songID) + ".mp3",
                          "(Song Name: " + songName + ")")
                    music.write(newCommand.payload)
                    music.close() # Save the song as .mp3 file

                    songDict[songID] = songName
                    saveSongDict(songDict) # Add the song to songlist

                    replyCommand = Command()
                    replyCommand.command = "SongAdded " + str(songID)

                # 2.Download a song by songID:
                elif ClientCommand[0] == "GetSong":
                    SongID = ClientCommand[1]       #Get the Song ID
                    print("Sending song")
                    replyCommand = Command()
                    
                    if int(SongID) not in songDict:  # Check if the Song ID exist
                        raise Exception("File not found")
                    
                    music = open("socket-demo-with-GUI/Server/Song/" + SongID + ".mp3", 'rb')
                    print("Sending", SongID + ".mp3","(" + songDict[int(SongID)] + ")")
                    replyCommand.payload = music.read()
                    music.close()
                    replyCommand.command = "SongData"

                # 3.Remove a song from the server:
                elif ClientCommand[0] == "RemoveSong":
                    songID = ClientCommand[1]
                    print("Removing song")

                    try: # Remove the song file
                        os.remove("socket-demo-with-GUI/Server/Song/" + songID + ".mp3")
                    except Exception as e:
                        print(e)
                        
                    # Remove the song from songlist
                    songDict.pop(int(songID))
                    saveSongDict(songDict)

                    count = 1
                    replyCommand = Command()
                    replyCommand.command = "SongRemovedOK"

                # Get all the avaliable songs
                elif ClientCommand[0] == "GetSongList":
                    print("Sending song list")
                    replyCommand = Command()
                    replyCommand.command = "SongList"
                    replyCommand.payload = songDict
                    
                else:
                    print("Unknown Command:", newCommand.command.replace('_',' '))
                    raise Exception("Unknown Command")

                packedData = pickle.dumps((replyCommand))               # Serialize the class to a binary array
                self.mySocket.sendall(struct.pack("i", len(packedData))) # Length of the message is just the length of the array
                self.mySocket.sendall(packedData)

        except Exception as e:
            print(e)
            print("\nClosing socket")
            self.mySocket.close()

#start our main....

host = "localhost"
port = 4561

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((host,port))
serverSocket.listen(1)

print("Listening...")

songDict = loadSongDict()
print(songDict.items())

while True:
    (clientSocket, address) = serverSocket.accept()
    print("Got incoming connection")
    newThread = SocketThread(clientSocket)        # make a new instance of our thread class to handle requests
    newThread.start()                             