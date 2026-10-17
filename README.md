# Xteink X3 RSS Feed Pipeline

自動化生成 AI 晨報並部署到 GitHub Pages，X3 可透過 RSS reader 訂閱。

## 架構

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GitHub Actions  │────▶│  GitHub Pages    │────▶│   Xteink X3     │
│  (每日定時執行)   │     │  (feed.xml)      │     │  (RSS Reader)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                                             │
        │  呼叫 OpenAI API                            │  定時同步
        ▼                                             ▼
┌─────────────────┐                           ┌─────────────────┐
│  AI 生成內容      │                           │  本地快取文章    │
│  (Python Script)  │                           │  (SD Card)      │
└─────────────────┘                           └─────────────────┘
```

## 快速開始

### 1. Fork 呢個 repo

1. 按 GitHub 頁面上方嘅 **Fork** 按鈕
2. 將 repo fork 到你嘅 GitHub account

### 2. 設定環境變數

去 GitHub repo 嘅 **Settings → Secrets and variables → Actions**，新增以下 secret：

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

可選設定：
```
OPENAI_MODEL=gpt-4o-mini          # 預設 gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1  # 可改用其他兼容 API
RSS_TITLE=AI 晨報                  # Feed 標題
RSS_ITEMS=5                       # 每日文章數量
```

### 3. 啟用 GitHub Pages

1. 去 **Settings → Pages**
2. Source 選擇 **GitHub Actions**
3. Build and deployment 選擇 **GitHub Actions workflow**
4. 按 **Save**

### 4. 手動測試

去 **Actions → Daily RSS Generator → Run workflow**，手動執行一次檢查有冇問題。

## 每日定時執行

去 `.github/workflows/daily-rss.yml` 設定執行時間：

```yaml
schedule:
  - cron: '0 0 * * *'  # 每日凌晨 0:00 UTC (香港時間 08:00)
```

## X3 設定 RSS

1. 喺 X3 上打開 CrossPoint 固件
2. 進入 **RSS / Atom reader** 功能
3. 加入你嘅 RSS feed URL：
   ```
   https://<你的 username>.github.io/xteink-rss/feed.xml
   ```
4. 設定同步頻率（如果固件支援）或者手動刷新

## 本地開發測試

```bash
# 安裝依賴
pip install requests

# 生成樣本內容
python rss_generator.py --sample --output feed.xml

# 使用 AI 生成
export OPENAI_API_KEY=sk-xxxx
python rss_generator.py --output feed.xml

# 指定文章數量
python rss_generator.py --items 10 --output feed.xml

# 使用自訂 config
python rss_generator.py --config config.json --output feed.xml
```

## 自訂內容主題

修改 `generate_ai_content()` function 裡面嘅 prompt，例如：

### 財經摘要
```python
prompt = """請生成 5 個今日全球財經新聞摘要..."""
```

### 科技日報
```python
prompt = """請生成 5 個今日科技新聞摘要..."""
```

### 學習卡片
```python
prompt = """請生成 5 個今日學習卡片..."""
```

## 檔案結構

```
xteink-rss/
├── rss_generator.py      # 主 generator 腳本
├── config.example.json   # 設定範本
├── README.md             # 說明文件
├── .github/
│   └── workflows/
│       └── daily-rss.yml # GitHub Actions workflow
├── feed.xml              # 輸出 (由 GitHub Actions 生成)
└── items.json            # 本地追蹤 (用於去重)
```

## 進階設定

### 使用其他 AI provider

喺 `generate_with_openai()` function 入面，可以修改 API endpoint 嚟支援：
- Anthropic Claude
- Google Gemini
- 本地部署嘅 Ollama

### 添加更多內容來源

可以修改腳本加入：
- News API
- RSS 聚合其他新聞來源
- Twitter/X 熱門話題
- 自己嘅資料庫

### 自訂 RSS 格式

修改 `RSSItem.to_xml()` 方法來自訂 XML 輸出格式。

## 故障排除

### GitHub Actions 失敗

1. 檢查 **Actions** 頁面嘅錯誤訊息
2. 確認 `OPENAI_API_KEY` secret 已設定
3. 檢查 GitHub Pages 設定

### X3 無法讀取 RSS

1. 確認 RSS URL 正確
2. 檢查 X3 嘅 Wi-Fi 連線
3. 嘗試手動刷新 feed

### 內容質量唔好

1. 調整 prompt 嘅描述
2. 改變 `temperature` 參數 (0.5-0.9)
3. 增加 `max_tokens` 限制

## License

MIT License
