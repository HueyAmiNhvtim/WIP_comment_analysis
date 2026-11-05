# Probably store the credential stuff into a .env file. DatabaseManager already handles that.
# Also probably a main class to log into OAuth stuff. I forgot why I wrote the previous comment tbh.
from googleapiclient.errors import HttpError
from chat_downloader import ChatDownloader
from chat_downloader.errors import ChatGeneratorError, InvalidURL
from src.extractor.base_extractor import BaseExtractor
from typing import List

import html
from datetime import datetime

# DATA FORMAT THAT IS SUPPOSEDLY RETURNED BY THIS EXTRACTOR IS SPECIFIED IN extractor/base.py
# TODO: Modify this extractor to follow the data format specified in base.py
# TODO: For each of the except in the try-except (or try-catch), get the error to a logger instead of just printing it out...

# Why do I feel like you have to specify the actual video for the youtube_client....
# No, if you look at the request_shenanigans.py, the stuff to request commentThreads and livechat messages all have the video_id parameter

class YoutubeExtractor(BaseExtractor):
    def __init__(self, youtube_client):
        self.youtube_client = youtube_client #
        self._VALID_URLS_ = [f"https://www.youtube.com/watch?v="]

    def extract_comments(self, video_id: str) -> List[dict]:
        """Extract post-stream comments."""
        result = []
        try:
            thread_request = self.youtube_client.commentThreads().list(
                part="snippet, replies", # Specify the specific keys that are gonna appear in the response's commentThread resource
                maxResults=100,
                moderationStatus="published",
                textFormat="html",
                videoId=video_id
            )

            while True:
                thread_response = thread_request.execute()
                
                for comment_thread in thread_response.get("items", []):
                    result += self.__extract_comment_thread(comment_thread)
                    
                next_page_token = thread_response.get("nextPageToken", False)
                # Quit if no more comments in the comment section to extract.
                if not next_page_token:
                    break
                
                thread_request = self.youtube_client.commentThreads().list(
                    part="snippet,replies",
                    maxResults=100,
                    moderationStatus="published",
                    textFormat="html",
                    videoId=video_id, 
                    pageToken=next_page_token,
                )
        except HttpError as err:
            print(err) # TODO: May do more in the future
        return result

    # WIP: BOTH EXTRACT comments function are WIP. HAS TO FOLLOW THE data format        
    def __extract_comment_thread(self, commentThread: dict) -> List[dict]:
        """Extract every comment in a comment thread (well, public ones)
        """
        
        # TODO: you know the pagination thing that Google did for their Youtube API..
        #       Maybe in the future you can try doing that to prevent returning
        #       a massive list of comments to whatever backend we're gonna do.
        #       Hint: perhaps you can return the generator instead.
        #             and yield the comments in batches? in the comment processing pipeline?
        #             ehh, we will get there when we get there I guess.
        # Part of the above comment because it's too long.
        result = []
        
        # Get the comment at the top of the comment thread
        top_level_comment = commentThread["snippet"]["topLevelComment"]
        top_level_comment_snippet = top_level_comment["snippet"]
        top_level_comment_dict = dict()
        top_level_comment_dict["platform_comment_id"] = f"ytb_{top_level_comment["id"]}"
        top_level_comment_dict["published_at"] = datetime.fromisoformat(top_level_comment_snippet["publishedAt"])
        top_level_comment_dict["text"] = top_level_comment_snippet.get("textOriginal") or html.unescape(top_level_comment_snippet.get("textDisplay", ""))
        top_level_comment_dict["platform_user_id"] = f"ytb_{top_level_comment_snippet["authorChannelId"]["value"]}"
        result.append(top_level_comment_dict)
        
        actual_reply_count = commentThread["snippet"]["totalReplyCount"] 
        # only request when totalreplycount > 0 (avoid wasting quota via trying to extract replies)
        if actual_reply_count > 0:
            retrieved_replies = commentThread.get("replies", {}).get("comments", [])
            retrieved_reply_count = len(retrieved_replies)
            
            # Only call the api when the retrieved replies are not enough!
            # Youtube usually only serves the first few replies as an example
            if actual_reply_count != retrieved_reply_count:
                # Loop through the replies of the current top level comment
                replies_request = self.youtube_client.comments().list(
                    part="snippet",
                    maxResults=100,
                    parentId=top_level_comment["id"]
                )
                
                while True:
                    try:
                        replies_response = replies_request.execute()
                        for reply in replies_response.get("items", []):
                            reply_dict = dict()
                            reply_snippet = reply["snippet"]
                            reply_dict["platform_comment_id"] = f"ytb_{reply["id"]}"
                            reply_dict["published_at"] = datetime.fromisoformat(reply_snippet["publishedAt"])
                            reply_dict["text"] = reply_snippet.get("textOriginal") or html.unescape(reply_snippet.get("textDisplay", ""))
                            reply_dict["platform_user_id"] = f"ytb_{reply_snippet["authorChannelId"]["value"]}"
                            result.append(reply_dict)      
                                            
                        next_page_token = replies_response.get("nextPageToken")
                        if not next_page_token:
                            break
                            
                        replies_request = self.youtube_client.comments().list(
                            part="snippet",
                            maxResults=100,
                            parentId=top_level_comment["id"],
                            pageToken=next_page_token,
                        ) 
                    except HttpError as err:
                        print(err)
            else:
                for reply in retrieved_replies:
                    reply_dict = dict()
                    reply_snippet = reply["snippet"]
                    reply_dict["platform_comment_id"] = f"ytb_{reply["id"]}"
                    reply_dict["published_at"] = datetime.fromisoformat(reply_snippet["publishedAt"])
                    reply_dict["text"] = reply_snippet.get("textOriginal") or html.unescape(reply_snippet.get("textDisplay", ""))
                    reply_dict["platform_user_id"] = f"ytb_{reply_snippet["authorChannelId"]["value"]}"
                    result.append(reply_dict) 
        return result

    def extract_livechat(self, video_id: str) -> List[dict]:
        """Extract live chat logs."""
        # TODO: Possibly another generator implementation like in comment thread in the future.
        # TODO: Maybe test it against an actual live stream. tho...that may require us to use
        #       Youtube's actual API for getting the livechat of an active live stream. Maybe in the future.
        #       For archived livestream, we can't as of the August 2026. Hence the inclusion of that chatreplaydownloader!
        #       
        result = []
        
        chat = None
        chat_retrieved = False
        for url in self._VALID_URLS_:
            if chat_retrieved:
                break
            try:
                vid_url = url + video_id
                chat = ChatDownloader().get_chat(vid_url, message_groups=['messages'], max_attempts=10)
                chat_retrieved = True
            except ChatGeneratorError as err:
                print(f"Can't find a valid generator for Youtube using this link: {url}.\nError: {err}")
            except InvalidURL as err:
                print(f"Invalid url: {url}.\nError: {err}")
            
        if chat_retrieved:
            for message in chat: # ignore the error, the chat_retrieved guarantees that if chat generator can't be retrieved, it will block the code from going into this part
                message_dict = dict()
                message_dict["platform_comment_id"] = f"ytb_{message["message_id"]}"
                message_dict["published_at"] = datetime.fromtimestamp(message["timestamp"]/1e6) # The chat library returns timestamp in MICROSECONDS, and python's fromtimestamp only deals with timestamp in SECONDS
                message_dict["text"] = html.unescape(message["message"])
                message_dict["platform_user_id"] = f"ytb_{message["author"]["id"]}"
                result.append(message_dict)
        return result
    
    def extract_video_info(self, video_id: str) -> dict:
        """Extract metadata like title, views, and total comment count."""
        result = dict()
        # TODO: In the future...maybe implement a cache to avoid wasting quota on repeatedly reached video.
        try:
            video_request = self.youtube_client.videos().list(
                part="snippet,statistics,liveStreamingDetails",
                id=video_id
            )
            video_response = video_request.execute()

            items = video_response.get("items", [])
            if not items:
                print(f"No video found for ID: {video_id}") # TODO: gonna do more in the future, probably connect to frontend or sth.
                                                            # That would also mean possibly unique Exceptions
                return result
            
            video_data = items[0]
            snippet = video_data.get("snippet", {})
            statistics = video_data.get("statistics", {})
            
            result["platform_video_id"] = f"ytb_{video_id}"
            result["title"] = snippet.get("title", "Unknown Title")
            
            if snippet.get("publishedAt", False):
                result["published_at"] = datetime.fromisoformat(snippet["publishedAt"])
            else:
                result["published_at"] = None
                
            result["view_count"] = int(statistics.get("viewCount", 0))
            result["comment_count"] = int(statistics.get("commentCount", 0))
            
            live_broad_cast_status = snippet.get("liveBroadcastContent", "none")
            # TEMPORARY FIX: MAKE RESULT RETURN THE RESPONSE 
            # TODO: Gonna require some refactoring to avoid code organization looking messy.
            # Like, one method needing the result from another's response...
            result["is_livestream"] = "liveStreamingDetails" in video_data
            # NOTE: Youtube API (as of the time of writing of Oct 2026) does not have a way to see other collaborators' channelId in a collab video. I'm going 
            #       to follow the same data format as it is specified in base.py in case they decided to do so.
            #       Even though there is potentially a way to find collaborators channelID, it is not 100% reliable as creators
            #       can just not put the collaborator names and/or handles in both title and description.
            result["platform_owner_ids"] = [snippet["channelId"]] 
            return result
        except HttpError as err:
            print(err)
        return result