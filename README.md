# collabDJ - [collabDJ.com](http://www.collabdj.com)
Group control of a Google Play Music playlist using text messages

To run:
```
Set Twilio account SID, auth token, and phone number in main.py
Set Google Play Music username, password, and playlist share token in main.py

python main.py
```

To test my instance:
```
USAGE:
    send a text message to +15186590134

    message options:
    #help: help command
    #votes: view the current vote counts
    #top: view the current top voted song
    #start: restart the server
    #stop: stop the server, clear playlist and vote queue
    #clear: clear playlist
    #kill: exit main loop, delete playlist, stop server (REQUIRES MANUAL REBOOT) - is not activated for production
    query: any other query will be processed by google music as a song/artist/album search
```
Playlist URL: [https://play.google.com/music/playlist/AMaBXylUEOcHdjhsYOJraDeBLYNF-E2XJzphw8I6fgbImJiQ0xNixs5WXkePjy7vqoXCr8-bru6GVeGGD0YmT1a0w9XrjNIiPw%3D%3D](https://play.google.com/music/playlist/AMaBXylUEOcHdjhsYOJraDeBLYNF-E2XJzphw8I6fgbImJiQ0xNixs5WXkePjy7vqoXCr8-bru6GVeGGD0YmT1a0w9XrjNIiPw%3D%3D)
