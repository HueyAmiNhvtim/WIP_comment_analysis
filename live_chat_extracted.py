# THANK YOU SO MUCH XENOVA https://github.com/xenova/chat-replay-downloader
from chat_replay_downloader.chat_replay_downloader import get_chat_replay

# The return is literally a list of dictionaries, each dictionary containing
# the author and their livechat message as well as the timestamp. Wow.
youtube_messages = get_chat_replay("https://www.youtube.com/watch?v=0_9pGc_qP9s")
for i in range(5):
    print(youtube_messages[i])
print(len(youtube_messages))
