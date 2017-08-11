from gmusicapi import Mobileclient
from twilio.rest import Client
from classes import Song, Message
import threading
import time
import urllib3

#disable urllib3 SSL warnings
urllib3.disable_warnings()

#google play music auth
loginID = "" #Google play username
authToken = "" #Google play password

#twilio auth
account_sid = "" #twilio account_sid
auth_token = "" #twilio auth_token

#GLOBAL VARS
PLAYLISTNAME = 'collabDJ'
twilioNumber = "" #twilio number

#Google Play Music Playlist
share_tok = "" #Google playlist share token https://play.google.com/music/playlist/<token>

currentSongLength = 5000
killServer = False
receiveStop = False
isPlaylistCreated = False
listOfMessages = []

#adds top voted song to playlist then sleeps for half the length of the song
class timerThread (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        global receiveStop
        global currentSongLength
        while True:
            done = False
            if len(songList) > 0:
                currentSongLength = int(topVotedSong(songList).duration)/1100
                done = addTopSong(songList)
            if done:
                time.sleep(currentSongLength)


#parse gmusicapi response
def parseQuery(query):
    results = api.search(query, max_results=15)
    if results['song_hits'] == []:
        return 'error'
    parsedID = results['song_hits'][0]['track']['storeId']
    parsedTitle = results['song_hits'][0]['track']['title']
    parsedArtist = results['song_hits'][0]['track']['artist']
    parsedLength = results['song_hits'][0]['track']['durationMillis']
    return Song(parsedTitle, parsedArtist, parsedLength, parsedID)


#create the playlist
def createPlaylist():
    global playlistID
    global isPlaylistCreated

    #playlistID = api.create_playlist(PLAYLISTNAME, 'none', True)
    isPlaylistCreated = True

    playlistID = "" #Google playlist ID


#delete the playlist
def deletePlaylist():
    global isPlaylistCreated

    if (isPlaylistCreated):
        api.delete_playlist(playlistID)
        isPlaylistCreated = False
    else:
        print("Playlist Not Created Yet")


#returns true if song is already in list, false if not
def listContains(song, listOfSongs):
    for i in listOfSongs:
        if i.songID == song.songID:
            return True
    return False


#returns top voted song (highest vote count/most recently voted if there is a tie)
def topVotedSong(listOfSongs):
    topSong = listOfSongs[0]
    for i in listOfSongs:
        if i.votes >= topSong.votes:
            topSong = i
    return topSong


#adds top song to the playlist, and sets vote count to -1 to signify that it has been added
def addTopSong(songList):
    s1 = topVotedSong(songList)
    if s1.votes > -1:
        api.add_songs_to_playlist(playlistID, s1.songID)
        print("Added " + s1.title.encode('utf-8') + " by " + s1.artist.encode('utf-8') + " to playlist\n")
        s1.votes = -1
        return 1
    else:
        return 0


#returns the requested song from the list
def returnSong(song, songList):
    for i in songList:
        if song.songID == i.songID:
            return i
    else:
        return song


#parse sms message from twilio
def parseMessage(message):
    ssid = message.sid
    fromNum = message.from_
    query = message.body
    return Message(ssid, query, fromNum)


#download all sms messages, add them to a list, and then delete the messages from twilio servers
def filterMessages(number):
    #download and save messages
    messages = client.messages.list(to=number)
    newMessages = []
    for i in messages:
        if i.status == 'received':
            newMessages.append(parseMessage(i))
        else:
            print(i.status)

    #delete processed messages from twilio servers
    for message in newMessages:
            try:
                client.messages(message.mSSID).delete()
            except Exception as ex:
                print("message delete failed\n")
                print(ex)
    return newMessages


#send text message to voter's phone with info on if the song is queued or needs more votes
def sendConfirmationMessage(song, number):
    if int(song.votes) == int(topVotedSong(songList).votes):
        body = "You have successfully voted for " + song.title.encode('utf-8') + " by " + song.artist.encode('utf-8') + ". It's currently set to be queued up next!"
    else:
        numberMore = int(topVotedSong(songList).votes) - int(song.votes)
        body = "You have successfully voted for " + song.title.encode('utf-8') + " by " + song.artist.encode('utf-8') + ". It needs " + str(numberMore) + " vote(s) to queued up next!"
    to = number
    from_ = twilioNumber
    client.messages.create(body=body, to=to, from_=from_)
    print("sent confirmation message to " + number + "\n")


#clears vote queue and playlist
def stopServer(number):
    global receiveStop
    receiveStop = True
    for song in songList:
        song.votes = -1
    tracks = api.get_shared_playlist_contents(share_tok)
    playlists = api.get_all_user_playlist_contents()
    entry_ids = []
    for track in playlists[0]["tracks"]:
        entry_ids.append(track["id"])
    api.remove_entries_from_playlist(entry_ids)
    print("playlist cleared\n")
    print('receive stopped\n')
    client.messages.create(body="collabDJ stopped. Playlist and vote queue cleared.", to=number, from_=twilioNumber)


#main loop
def loopFunction():
    global receiveStop
    global killServer

    #kill command flag
    killServer = False
    #stop command flag
    receiveStop = False
    while not killServer:
        newMessages = filterMessages(twilioNumber)
        for i in newMessages:
            query = i.query

            if query == "":
                continue

            #stop server command
            if query == '#stop':
                if receiveStop == True:
                    client.messages.create(body="Error: collabDJ already stopped.", to=i.fromNum, from_=twilioNumber)
                else:
                    stopServer(i.fromNum)

            #start server command
            elif query == '#start':
                if receiveStop == False:
                    client.messages.create(body="Error: collabDJ already started.", to=i.fromNum, from_=twilioNumber)
                else:
                    receiveStop = False
                    print('receive started\n')
                    client.messages.create(body="collabDJ started.", to=i.fromNum, from_=twilioNumber)

            #clear tracks from playlist command
            elif query == '#clear':
                tracks = api.get_shared_playlist_contents(share_tok)
                playlists = api.get_all_user_playlist_contents()
                entry_ids = []
                for track in playlists[0]["tracks"]:
                    entry_ids.append(track["id"])
                api.remove_entries_from_playlist(entry_ids)
                print("playlist cleared\n")
                client.messages.create(body="Playlist cleared.", to=i.fromNum, from_=twilioNumber)

            #kill server/delete playlist command (CAUTION! Requires restarting server manually)
            elif query == '#kill':
                killServer = True
                stopServer(i.fromNum)
                print('server killed\n')
                client.messages.create(body="collabDJ killed.", to=i.fromNum, from_=twilioNumber)
                break

            #help command
            elif query == '#help':
                print('request help\n')
                client.messages.create(body="Hi! Text me the name of a song you want to listen to. Alternatively, text one of the following commands.\n\nText Commands:\n#help: Get help message\n#votes: Get current vote counts\n#top: Get current top voted song\n#status: Get collabDJ status", to=i.fromNum, from_=twilioNumber)

            #status command
            elif query == "#status":
                print('request status\n')
                if receiveStop == True:
                    client.messages.create(body="collabDJ is stopped.", to=i.fromNum, from_=twilioNumber)
                elif receiveStop == False:
                    client.messages.create(body="collabDJ is running.", to=i.fromNum, from_=twilioNumber)

            #votes sends list of songs in the current vote round
            elif query == '#votes':
                if receiveStop == True:
                    client.messages.create(body="collabDJ stopped. Text command #start to begin.", to=i.fromNum, from_=twilioNumber)
                    continue
                sortedVotes = sorted(songList, key=lambda song: (-song.votes, -songList.index(song)))
                body = "Vote Count:\n"
                for song in sortedVotes:
                    if song.votes == -1:
                        continue
                    else:
                        body = body + str(song.votes) + " - " + song.title.encode('utf-8') + " by " + song.artist.encode('utf-8') + "\n"

                if body != "Vote Count:\n":
                    print("sent number of votes message\n")
                    client.messages.create(body=body, to=i.fromNum, from_=twilioNumber)
                else:
                    print("sent no songs up for vote message\n")
                    client.messages.create(body="There are currently no songs up for vote!", to=i.fromNum, from_=twilioNumber)

            #top sends current top voted song
            elif query == '#top':
                if receiveStop == True:
                    client.messages.create(body="collabDJ stopped. Text command #start to begin.", to=i.fromNum, from_=twilioNumber)
                elif len(songList) == 0:
                    client.messages.create(body="There are currently no songs up for vote!", to=i.fromNum, from_=twilioNumber)
                    print("sent no songs up for vote message")
                elif topVotedSong(songList).votes == -1:
                    client.messages.create(body="There are currently no songs up for vote!", to=i.fromNum, from_=twilioNumber)
                    print("sent no songs up for vote message")
                else:
                    s1 = topVotedSong(songList)
                    sms = "Top Voted Song:\n" + s1.title.encode('utf-8') + " by " + s1.artist.encode('utf-8') + " - " + str(s1.votes)
                    client.messages.create(body=sms, to=i.fromNum, from_=twilioNumber)
                    print("sent top voted song message")

            #song query: if server not stopped
            elif not receiveStop:
                s = parseQuery(query)
                if s == 'error':
                    client.messages.create(body="Sorry, we couldn't find your song.", to=i.fromNum, from_=twilioNumber)
                    print("sent search failed message to " + i.fromNum + "\n")
                    time.sleep(1)
                else:
                    #first time seeing song request
                    if not listContains(s, songList):
                        songList.append(s)
                        s.vote()

                    #received song request before
                    else:
                        s = returnSong(s, songList)
                        #if song not already added to playlist, increase vote by 1
                        if not s.votes == -1:
                            s.vote()
                        #if song already added to playlist, reset vote to 0, then add vote
                        else:
                            s.resetvote()
                            s.vote()

                    #print confirmation to console
                    print "Received song request:"
                    print "Track: " + s.title.encode('utf-8')
                    print "Artist: " + s.artist.encode('utf-8')
                    if s.votes > -1:
                        print "Votes: " + str(s.votes)

                    sendConfirmationMessage(s, i.fromNum)

            #song query: if server stopped
            else:
                client.messages.create(body="collabDJ stopped. Text command #start to begin.", to=i.fromNum, from_=twilioNumber)
        time.sleep(1)
        #MOVED THIS TIME>SLEEP OVER ONE TAB

#connect to twilio api
client = Client(account_sid, auth_token)

#connect to gmusicapi
api = Mobileclient()
logged_in = api.login(loginID, authToken, Mobileclient.FROM_MAC_ADDRESS)
if (logged_in):
    print("log in success\n")
else:
    print("log in failed, please verify login details\n")

#delete any unprocessed texts from previous queue
deleteMessages = client.messages.list(to=twilioNumber)
for i in deleteMessages:
    ssid = i.sid
    client.messages(ssid).delete()
print('previous queue cleared\n')

#create playlist
createPlaylist()
print('playlist created\n')

#create list for songs in queue
songList = []

#start timerThread (periodically adds tracks to playlist) with threadID = 1
delayLoop = timerThread(1)
delayLoop.start()

#start query parsing/queueing loop
loopFunction()

#if loop is exited (kill command), delete the playlist
deletePlaylist()
print('deleted playlist')
