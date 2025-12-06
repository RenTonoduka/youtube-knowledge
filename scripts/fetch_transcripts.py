#!/usr/bin/env python3
"""
YouTube Playlist Transcript Fetcher
プレイリストの動画から字幕を取得してローカルに保存
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

import requests
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeTranscriptFetcher:
    def __init__(self, api_key: str, playlist_id: str, output_dir: str = "transcripts"):
        self.api_key = api_key
        self.playlist_id = playlist_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_file = self.output_dir / ".processed.json"
        self.processed_ids = self._load_processed()

    def _load_processed(self) -> set:
        """処理済み動画IDを読み込む"""
        if self.processed_file.exists():
            with open(self.processed_file, "r") as f:
                return set(json.load(f))
        return set()

    def _save_processed(self):
        """処理済み動画IDを保存"""
        with open(self.processed_file, "w") as f:
            json.dump(list(self.processed_ids), f, indent=2)

    def _sanitize_filename(self, title: str) -> str:
        """ファイル名に使えない文字を除去"""
        # 使えない文字を置換
        sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
        # 長すぎる場合は切り詰め
        return sanitized[:100]

    def get_playlist_videos(self) -> list:
        """プレイリストの動画一覧を取得"""
        videos = []
        next_page_token = None

        while True:
            url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                "part": "snippet",
                "playlistId": self.playlist_id,
                "maxResults": 50,
                "key": self.api_key,
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            response = requests.get(url, params=params)
            data = response.json()

            if "error" in data:
                print(f"API Error: {data['error']['message']}")
                break

            for item in data.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "channel": snippet.get("videoOwnerChannelTitle", "Unknown"),
                    "published_at": snippet["publishedAt"],
                    "description": snippet.get("description", "")[:500],
                })

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return videos

    def fetch_transcript(self, video_id: str) -> str | None:
        """動画の字幕を取得"""
        try:
            ytt_api = YouTubeTranscriptApi()
            # 日本語を優先、なければ英語、それもなければ自動生成
            transcript = ytt_api.fetch(video_id, languages=['ja', 'en', 'ja-JP'])
            return '\n'.join([t.text for t in transcript])
        except Exception as e:
            print(f"  ⚠️ 字幕取得失敗 ({video_id}): {e}")
            return None

    def save_transcript(self, video: dict, transcript: str):
        """字幕をファイルに保存"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = self._sanitize_filename(video["title"])
        filename = f"{date_str}_{safe_title}.md"
        filepath = self.output_dir / filename

        content = f"""# {video['title']}

## メタデータ
- **Video ID**: {video['video_id']}
- **チャンネル**: {video['channel']}
- **URL**: https://www.youtube.com/watch?v={video['video_id']}
- **取得日時**: {datetime.now().isoformat()}

## 概要
{video['description']}

---

## 文字起こし

{transcript}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✅ 保存: {filename}")
        return filepath

    def run(self):
        """メイン処理"""
        print(f"📺 プレイリスト {self.playlist_id} から動画を取得中...")
        videos = self.get_playlist_videos()
        print(f"  → {len(videos)} 件の動画を検出")

        new_videos = [v for v in videos if v["video_id"] not in self.processed_ids]
        print(f"  → {len(new_videos)} 件が未処理")

        if not new_videos:
            print("✨ 新規動画はありません")
            return []

        results = []
        for video in new_videos:
            print(f"\n📝 処理中: {video['title'][:50]}...")
            transcript = self.fetch_transcript(video["video_id"])

            if transcript:
                filepath = self.save_transcript(video, transcript)
                self.processed_ids.add(video["video_id"])
                results.append({
                    "video_id": video["video_id"],
                    "title": video["title"],
                    "filepath": str(filepath),
                    "char_count": len(transcript),
                })
            else:
                print(f"  ⏭️ スキップ（字幕なし）")

        self._save_processed()
        print(f"\n🎉 完了！{len(results)} 件の字幕を保存しました")
        return results


def main():
    # 環境変数から設定を読み込む
    api_key = os.environ.get("YOUTUBE_API_KEY")
    playlist_id = os.environ.get("YOUTUBE_PLAYLIST_ID")
    output_dir = os.environ.get("OUTPUT_DIR", "transcripts")

    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable is required")
    if not playlist_id:
        raise ValueError("YOUTUBE_PLAYLIST_ID environment variable is required")

    fetcher = YouTubeTranscriptFetcher(api_key, playlist_id, output_dir)
    results = fetcher.run()

    # GitHub Actions用に結果を出力
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_transcripts={len(results)}\n")


if __name__ == "__main__":
    main()
