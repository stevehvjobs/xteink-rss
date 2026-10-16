#!/usr/bin/env python3
"""
Xteink X3 RSS Feed Generator
Generate AI-powered daily digest in RSS format for Xteink X3 e-reader.

Usage:
    python rss_generator.py --output feed.xml  # Generate locally
    python rss_generator.py --openai --output feed.xml  # Use OpenAI API
    
Config:
    Edit the DEFAULTS section below or use environment variables:
    - OPENAI_API_KEY: OpenAI API key
    - RSS_TITLE: Feed title (default: "AI Daily Digest")
    - RSS_DESCRIPTION: Feed description (default: "AI-powered daily news digest")
    - RSS_LANGUAGE: Feed language (default: "zh-hant")
    - RSS_ITEMS: Number of articles to generate (default: 5)
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import argparse

# ==================== CONFIGURATION ====================
DEFAULTS = {
    "title": "AI 晨報",
    "description": "每日 AI 生成嘅精選資訊摘要",
    "link": "https://your-username.github.io/xteink-rss/",  # Update with your GitHub Pages URL
    "language": "zh-hant",
    "items": 5,
    "category": "AI 摘要",
    "author": "AI Assistant",
}

# API Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ==================== DATA CLASSES ====================
@dataclass
class RSSItem:
    title: str
    description: str
    link: str
    pub_date: str
    guid: str
    category: str = ""
    author: str = ""
    content: str = ""
    
    def to_xml(self) -> str:
        """Convert item to XML string"""
        xml = f"""    <item>
      <title>{self.escape_xml(self.title)}</title>
      <description>{self.escape_xml(self.description)}</description>
"""
        if self.link:
            xml += f"      <link>{self.escape_xml(self.link)}</link>\n"
        if self.pub_date:
            xml += f"      <pubDate>{self.pub_date}</pubDate>\n"
        if self.guid:
            xml += f"      <guid>{self.escape_xml(self.guid)}</guid>\n"
        if self.category:
            xml += f"      <category>{self.escape_xml(self.category)}</category>\n"
        if self.author:
            xml += f"      <author>{self.escape_xml(self.author)}</author>\n"
        if self.content:
            xml += f"      <content:encoded>{self.escape_xml(self.content)}</content:encoded>\n"
        xml += "    </item>\n"
        return xml
    
    @staticmethod
    def escape_xml(text: str) -> str:
        """Escape XML special characters"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


@dataclass
class RSSFeed:
    title: str
    description: str
    link: str
    language: str
    items: List[RSSItem]
    category: str = ""
    author: str = ""
    last_build_date: Optional[str] = None
    
    def generate_xml(self) -> str:
        """Generate complete RSS XML"""
        now_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        build_date = self.last_build_date or now_str
        items_xml = "\n".join(item.to_xml() for item in self.items)
        
        xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        xml += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        xml += "  <channel>\n"
        xml += f"    <title>{self.escape_xml(self.title)}</title>\n"
        xml += f"    <description>{self.escape_xml(self.description)}</description>\n"
        xml += f"    <link>{self.escape_xml(self.link)}</link>\n"
        xml += f"    <language>{self.language}</language>\n"
        xml += f"    <lastBuildDate>{build_date}</lastBuildDate>\n"
        xml += "    <generator>AI RSS Generator v1.0</generator>\n"
        xml += f'    <atom:link href="{self.link}feed.xml" rel="self" type="application/rss+xml"/>\n'
        if self.category:
            xml += f"    <category>{self.escape_xml(self.category)}</category>\n"
        if self.author:
            xml += f"    <managingEditor>{self.escape_xml(self.author)}</managingEditor>\n"
        xml += items_xml
        xml += "  </channel>\n"
        xml += "</rss>\n"
        return xml
    
    @staticmethod
    def escape_xml(text: str) -> str:
        """Escape XML special characters"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


# ==================== AI GENERATION ====================
def generate_with_openai(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    """Generate content using OpenAI API"""
    if not OPENAI_API_KEY:
        print("⚠️  OPENAI_API_KEY not set. Using sample data.")
        return None
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"{OPENAI_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你係一個專業嘅新聞編輯同摘要專家。你嘅任務係根據用户嘅要求生成高質量嘅中文摘要內容。使用繁體中文，語氣專業但易明。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None


def generate_sample_content(items_count: int = 5) -> List[RSSItem]:
    """Generate sample RSS items (fallback when no AI API)"""
    now = datetime.now(timezone.utc)
    items = []
    
    for i in range(items_count):
        content = f"""## 項目 {i+1}: AI 生成內容

呢個係樣本內容。當你設定好 AI API 之後，呢度會自動生成每日精選摘要。

- 標題：每日精選
- 日期：{now.strftime("%Y-%m-%d")}
- 類別：AI 摘要

請設定 OPENAI_API_KEY 環境變數嚟啟用 AI 生成功能。"""
        
        item = RSSItem(
            title=f"每日精選項目 {i+1}",
            description=content[:200],
            link="",
            pub_date=now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            guid=hashlib.md5(f"item-{i}-{now.isoformat()}".encode()).hexdigest(),
            category="AI 摘要",
            author="AI Assistant",
            content=content,
        )
        items.append(item)
    
    return items


def generate_ai_content(items_count: int = 5) -> List[RSSItem]:
    """Generate AI-powered RSS items"""
    now = datetime.now(timezone.utc)
    
    # Build prompt for daily digest
    prompt = f"""請生成 {items_count} 個今日嘅精選摘要項目。每個項目應該包含：

1. 標題 (簡短有力，繁體中文)
2. 摘要內容 (100-200 字，重點清晰)
3. 內容 (300-500 字，詳細但易明)

格式要求：
- 使用繁體中文
- 內容要有價值、有深度
- 每個項目獨立，唔好重複
- 主題可以涵蓋：科技、財經、生活、健康、學習等

請按照以下 JSON 格式輸出（只輸出 JSON，唔好有其他文字）：

[
  {{
    "title": "標題",
    "description": "摘要內容",
    "content": "詳細內容"
  }},
  ...
]"""
    
    # Try AI generation
    ai_response = generate_with_openai(prompt, max_tokens=3000)
    
    if ai_response:
        # Parse JSON response
        try:
            # Find JSON array in response
            start = ai_response.find("[")
            end = ai_response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = ai_response[start:end]
                data = json.loads(json_str)
                
                items = []
                for i, item_data in enumerate(data[:items_count]):
                    item = RSSItem(
                        title=item_data.get("title", f"項目 {i+1}"),
                        description=item_data.get("description", ""),
                        link="",
                        pub_date=now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                        guid=hashlib.md5(f"{item_data.get('title', '')}-{now.isoformat()}".encode()).hexdigest(),
                        category="AI 摘要",
                        author="AI Assistant",
                        content=item_data.get("content", item_data.get("description", "")),
                    )
                    items.append(item)
                
                return items
        
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}. Falling back to sample data.")
    
    # Fallback to sample data
    print("⚠️  Using sample data. Set OPENAI_API_KEY for AI generation.")
    return generate_sample_content(items_count)


# ==================== FEED MANAGEMENT ====================
def load_existing_items() -> List[RSSItem]:
    """Load existing RSS items from a JSON file for deduplication"""
    items_file = Path("items.json")
    if items_file.exists():
        try:
            with open(items_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RSSItem(**item) for item in data]
        except (json.JSONDecodeError, KeyError):
            pass
    return []


def save_items(items: List[RSSItem]):
    """Save RSS items to JSON file for tracking"""
    items_file = Path("items.json")
    data = [asdict(item) for item in items]
    with open(items_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_feed() -> RSSFeed:
    """Create complete RSS feed"""
    # Generate new AI content
    new_items = generate_ai_content(DEFAULTS["items"])
    
    # Load existing items for deduplication
    existing_items = load_existing_items()
    
    # Combine: new items first, then existing (max 20 items total)
    all_items = new_items + existing_items[:15]
    
    # Create feed
    feed = RSSFeed(
        title=DEFAULTS["title"],
        description=DEFAULTS["description"],
        link=DEFAULTS["link"],
        language=DEFAULTS["language"],
        items=all_items[:20],  # Keep last 20 items
        category=DEFAULTS["category"],
        author=DEFAULTS["author"],
    )
    
    # Save for tracking
    save_items(all_items[:20])
    
    return feed


def main():
    parser = argparse.ArgumentParser(description="Xteink X3 RSS Feed Generator")
    parser.add_argument("--output", "-o", default="feed.xml", help="Output file path")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI API")
    parser.add_argument("--sample", action="store_true", help="Use sample data only")
    parser.add_argument("--items", type=int, default=5, help="Number of items to generate")
    parser.add_argument("--config", type=str, help="Config file path (JSON)")
    
    args = parser.parse_args()
    
    # Load config if provided
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
                DEFAULTS.update(config)
        except Exception as e:
            print(f"⚠️  Config load error: {e}")
    
    if args.items:
        DEFAULTS["items"] = args.items
    
    print(f"📰 Generating RSS feed...")
    print(f"   Title: {DEFAULTS['title']}")
    print(f"   Items: {DEFAULTS['items']}")
    
    # Create feed
    if args.sample:
        print("⚠️  Using sample data mode")
        new_items = generate_sample_content(DEFAULTS["items"])
        existing_items = load_existing_items()
        all_items = new_items + existing_items[:15]
        
        feed = RSSFeed(
            title=DEFAULTS["title"],
            description=DEFAULTS["description"],
            link=DEFAULTS["link"],
            language=DEFAULTS["language"],
            items=all_items[:20],
            category=DEFAULTS["category"],
            author=DEFAULTS["author"],
        )
    else:
        feed = create_feed()
    
    # Generate XML
    xml_content = feed.generate_xml()
    
    # Save to file
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    print(f"\n✅ RSS feed generated: {args.output}")
    print(f"   Size: {len(xml_content):,} bytes")
    print(f"   Items: {len(feed.items)}")
    print(f"   Last build: {feed.last_build_date or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
