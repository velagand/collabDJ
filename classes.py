#stores single track data
class Song():
    def __init__(self, title, artist, duration, songID):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.songID = songID
        self.votes = 0

    def vote(self):
        self.votes += 1

    def resetvote(self):
        self.votes = 0

#stores single user data - currently unused
class User():
    def __init__(self, phoneNumber):
        self.userID = phoneNumber
        self.votedSongs = []

    def voteSong(self, songID):
        if (songID in self.votedSongs):
            return 0
        else:
            self.votedSongs.append(songID)
            return 0

#stores single message data
class Message():
    def __init__(self, mSSID, query, fromNum):
        self.mSSID = mSSID
        self.query = query
        self.fromNum = fromNum