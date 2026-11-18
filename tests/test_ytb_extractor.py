from src.extractor.youtube_extractor import YoutubeExtractor
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from chat_downloader.errors import ChatGeneratorError

# TODO: When pagination is implemented, test that part too.

class TestYoutubeExtractor:
    # Test the extract video_info
    def test_extract_video_info_livestream(self, ytb_extractor: YoutubeExtractor, mock_youtube_client: MagicMock):
        # Imitate parts of youtube_client API Behaviour
        mock_youtube_client.videos().list().execute.return_value = {
            "items": [
                {
                    "id": "Qap7HFEx_oM",
                    "snippet": {
                        "title": "【#戌神ころね初配信】！！！！はじめまして！！！！",
                        "publishedAt": "2019-04-13T13:41:48Z",
                        "channelId": "UChAnqc_AY5_I3Px5dig3X1Q",
                    },
                    "statistics": {
                        'viewCount': '921152', 
                        'likeCount': '30591', 
                        'favoriteCount': '0', 
                        'commentCount': '1461'
                    },
                    "liveStreamingDetails": {
                        'actualStartTime': '2019-04-13T12:02:15Z', 
                        'actualEndTime': '2019-04-13T13:06:23Z', 
                        'scheduledStartTime': '2019-04-13T12:00:00Z'
                    }
                }
            ]
        }
        
        result = ytb_extractor.extract_video_info(video_id="Qap7HFEx_oM")
        
        assert result["platform_video_id"] == "ytb_Qap7HFEx_oM"
        assert result["title"] == "【#戌神ころね初配信】！！！！はじめまして！！！！"
        assert result["published_at"] == datetime(2019, 4, 13, 13, 41, 48, tzinfo=timezone.utc)
        assert result["view_count"] == 921152
        assert result["comment_count"] == 1461
        assert result["is_livestream"] is True
        assert result["platform_owner_ids"] == ["ytb_UChAnqc_AY5_I3Px5dig3X1Q"]        
    
    def test_extract_video_info_not_found(self, ytb_extractor: YoutubeExtractor, mock_youtube_client: MagicMock):
        """Test that an invalid/private video ID returns an empty dict gracefully."""
        mock_youtube_client.videos().list().execute.return_value = {"items": []}
        result = ytb_extractor.extract_video_info("asdaZxcz")
        assert result == {}

    # Test extract comment section
    def test_extract_comments_uses_inline_replies_when_complete(
        self, ytb_extractor: YoutubeExtractor, mock_youtube_client: MagicMock
    ):
        """
        When totalReplyCount matches the number of replies already attached in
        commentThreads().list(), comments().list() should NOT be called (saving quota).
        """
        mock_youtube_client.commentThreads().list().execute.return_value = {
            # No nextPageToken -> stops after 1 page and we only need to test 
            # that we don't call youtube api again when the inline replies are already all there are.
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "id": "c_top_1",
                            "snippet": {
                                "publishedAt": "2018-02-03T13:40:10Z",
                                "textOriginal": "Top level comment!",
                                "authorChannelId": {"value": "UC_user_1"},
                            },
                        },
                        "totalReplyCount": 1,
                    },
                    "replies": {
                        "comments": [
                            {
                                "id": "c_reply_1",
                                "snippet": {
                                    "publishedAt": "2019-05-02T13:05:00Z",
                                    # Fallback to textDisplay with HTML entities if textOriginal is absent
                                    # Should be more general since textOriginal of a comment is only available if the
                                    # invoker is the author of that comment.
                                    "textDisplay": "Reply with &quot;quotes&quot; &amp; symbols",
                                    "authorChannelId": {"value": "UC_user_2"},
                                },
                            }
                        ]
                    },
                }
            ]
        }
        comments = ytb_extractor.extract_comments("vid_abc")
        assert len(comments) == 2
        assert comments[0]["platform_comment_id"] == "ytb_c_top_1"
        assert comments[0]["published_at"] == datetime(2018, 2, 3, 13, 40, 10, tzinfo=timezone.utc)
        assert comments[0]["text"] == "Top level comment!"
        assert comments[0]["platform_user_id"] == "ytb_UC_user_1"
        assert comments[1]["platform_comment_id"] == "ytb_c_reply_1"
        assert comments[1]["published_at"] == datetime(2019, 5, 2, 13, 5, 0, tzinfo=timezone.utc)
        assert comments[1]["text"] == 'Reply with "quotes" & symbols'
        assert comments[1]["platform_user_id"] == "ytb_UC_user_2"
        # Verify we did NOT waste API quota calling comments().list()
        mock_youtube_client.comments().list.assert_not_called()
    
    def test_extract_comments_fetches_all_replies_when_partial(
        self, ytb_extractor: YoutubeExtractor, mock_youtube_client: MagicMock
    ):
        """
        When totalReplyCount > len(inline replies), extractor must call
        comments().list() to fetch the full reply chain.
        """
        mock_youtube_client.commentThreads().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "id": "c_top_1",
                            "snippet": {
                                "publishedAt": "2026-05-01T13:00:00Z",
                                "textDisplay": "Popular comment",
                                "authorChannelId": {"value": "UC_user_1"},
                            },
                        },
                        "totalReplyCount": 2,  # total is 2, but we're gonna use maxResults = 1
                    },
                    "replies": {
                        "comments": [
                            # YouTube only previewed 1 of the 2 replies inline
                            # 
                            {
                                "id": "c_reply_1",
                                "snippet": {
                                    "publishedAt": "2026-05-01T13:01:00Z",
                                    "textDisplay": "Reply 1",
                                    "authorChannelId": {"value": "UC_user_2"},
                                },
                            }
                        ]
                    },
                }
            ]
        }
        # Mock the follow-up comments().list() call that fetches all 2 replies
        mock_youtube_client.comments().list().execute.return_value = {
            "items": [
                {
                    "id": "c_reply_1",
                    "snippet": {
                        "publishedAt": "2026-05-01T13:01:00Z",
                        "textOriginal": "Reply 1",
                        "authorChannelId": {"value": "UC_user_2"},
                    },
                },
                {
                    "id": "c_reply_2",
                    "snippet": {
                        "publishedAt": "2026-05-01T13:02:00Z",
                        "textOriginal": "Reply 2",
                        "authorChannelId": {"value": "UC_user_3"},
                    },
                },
            ]
        }
        comments = ytb_extractor.extract_comments("vid_abc")
        # 1 top-level + 2 fetched replies = 3 total
        assert len(comments) == 3
        assert [c["platform_comment_id"] for c in comments] == [
            "ytb_c_top_1",
            "ytb_c_reply_1",
            "ytb_c_reply_2",
        ]
        assert[c["published_at"] for c in comments] == [
            datetime(2026, 5, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 1, 13, 1, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 1, 13, 2, 0, tzinfo=timezone.utc),
        ]
        assert[c["text"] for c in comments] == [
            "Popular comment",
            "Reply 1",
            "Reply 2"
        ]
        assert[c["platform_user_id"] for c in comments] == [
            "ytb_UC_user_1",
            "ytb_UC_user_2",
            "ytb_UC_user_3"
        ]
    
    # Test the livechat extraction part.
    @patch("src.extractor.youtube_extractor.ChatDownloader")
    def test_extract_livechat_success(self, mock_chat_downloader_cls: MagicMock, ytb_extractor: YoutubeExtractor):
        """Test parsing chat-downloader messages (microsecond timestamps & HTML unescaping)."""
        mock_chat_downloader_cls.return_value.get_chat.return_value = [
            {
                "message_id": "msg_100",
                "timestamp": 1700000000000000.0,  # 1,700,000,000 seconds in microseconds
                "message": " Grass &amp; Wahoo ",
                "author": {"id": "UC_chatter_99"},
            }
        ]
        livechats = ytb_extractor.extract_livechat("vid_abc")
        assert len(livechats) == 1
        assert livechats[0]["platform_comment_id"] == "ytb_msg_100"
        assert livechats[0]["published_at"] == datetime.fromtimestamp(1700000000, tz=timezone.utc)
        assert livechats[0]["text"] == " Grass & Wahoo "
        assert livechats[0]["platform_user_id"] == "ytb_UC_chatter_99"
    
    @patch("src.extractor.youtube_extractor.ChatDownloader")
    def test_extract_livechat_handles_error(self, mock_chat_downloader_cls: MagicMock, ytb_extractor: YoutubeExtractor):
        """Test that ChatGeneratorError (e.g. disabled chat replay) returns [] instead of crashing."""
        mock_chat_downloader_cls.return_value.get_chat.side_effect = ChatGeneratorError("Chat replay is disabled")
        livechats = ytb_extractor.extract_livechat("vid_abc")
        assert livechats == []
    
    def test_extract_users_deduplicates_ids(self, ytb_extractor: YoutubeExtractor):
        """If the channel owner also comments and chats, their user ID should appear only once."""
        video = {"platform_owner_ids": ["ytb_UC_owner"]}
        comments = [
            {"platform_user_id": "ytb_UC_owner"},
            {"platform_user_id": "ytb_UC_fan_1"},
        ]
        livechats = [
            {"platform_user_id": "ytb_UC_fan_1"},
            {"platform_user_id": "ytb_UC_fan_2"},
        ]
        users = ytb_extractor.extract_users(video=video, livechats=livechats, comments=comments)
        assert len(users) == 3
        assert set(users) == {"ytb_UC_owner", "ytb_UC_fan_1", "ytb_UC_fan_2"}