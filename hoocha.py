from pytchat import LiveChat

chat = LiveChat(video_id="?v=OCGCgUmpd8k&t=73s")

# This code is copy-pasted from https://github.com/taizan-hokuto/pytchat/wiki/LiveChat
while chat.is_alive():
    try:
        data = chat.get()
        items =  data.items
        for c in items:
            print(f"{c.datetime} [{c.author.name}] - {c.message}")
            #data.tick()
    except KeyboardInterrupt:
        chat.terminate()
        break