# YouTube Knowledge - 自動文字起こしシステム

YouTubeプレイリストの動画を自動で文字起こしし、ナレッジとして蓄積するシステム。

## 仕組み

```
YouTube プレイリストに動画追加
         ↓
GitHub Actions (1時間ごと)
         ↓
字幕を自動取得 → transcripts/ に保存
         ↓
git pull でローカルに同期
         ↓
Claude Code で要約・分類
```

## セットアップ

### 1. GitHubリポジトリにSecretsを設定

Settings → Secrets and variables → Actions → New repository secret

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 のAPIキー |
| `YOUTUBE_PLAYLIST_ID` | 監視するプレイリストのID (例: `PL7tsSDAfkl3lv5JjMc_y4AipaoLsDtGcy`) |

### 2. 使い方

1. YouTubeで文字起こししたい動画をプレイリストに追加
2. 1時間以内に自動で字幕が取得される
3. `git pull` でローカルに取得
4. Claude Code で要約・分類

### 3. 手動実行

Actions → Fetch YouTube Transcripts → Run workflow

## フォルダ構成

```
youtube-knowledge/
├── transcripts/           # 文字起こしファイル
│   ├── 2024-12-06_動画タイトル.md
│   └── .processed.json    # 処理済みID一覧
├── scripts/
│   └── fetch_transcripts.py
└── .github/workflows/
    └── fetch-transcripts.yml
```

## ローカルでテスト

```bash
export YOUTUBE_API_KEY="your-api-key"
export YOUTUBE_PLAYLIST_ID="your-playlist-id"
python scripts/fetch_transcripts.py
```
