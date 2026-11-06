import html
import feedparser
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

FEEDS = {
    "English": [
        ("World", "https://news.google.com/rss/search?q=world+international+news&hl=en&gl=US&ceid=US:en"),
        ("Politics", "https://news.google.com/rss/search?q=global+politics&hl=en&gl=US&ceid=US:en"),
        ("Business", "https://news.google.com/rss/search?q=world+business+economy&hl=en&gl=US&ceid=US:en"),
        ("Technology", "https://news.google.com/rss/search?q=world+technology+AI&hl=en&gl=US&ceid=US:en"),
        ("Science", "https://news.google.com/rss/search?q=world+science+research&hl=en&gl=US&ceid=US:en"),
        ("Health", "https://news.google.com/rss/search?q=world+health+news&hl=en&gl=US&ceid=US:en"),
        ("Sports", "https://news.google.com/rss/search?q=international+sports&hl=en&gl=US&ceid=US:en"),
        ("Environment", "https://news.google.com/rss/search?q=world+climate+environment&hl=en&gl=US&ceid=US:en")
    ],
    "Arabic": [
        ("World", "https://news.google.com/rss/search?q=أخبار+العالم+دولية&hl=ar&gl=SA&ceid=SA:ar"),
        ("Politics", "https://news.google.com/rss/search?q=أخبار+السياسة+العالمية&hl=ar&gl=SA&ceid=SA:ar"),
        ("Business", "https://news.google.com/rss/search?q=الاقتصاد+العالمي&hl=ar&gl=SA&ceid=SA:ar"),
        ("Technology", "https://news.google.com/rss/search?q=التكنولوجيا+والذكاء+الاصطناعي&hl=ar&gl=SA&ceid=SA:ar"),
        ("Science", "https://news.google.com/rss/search?q=أخبار+العلوم+العالمية&hl=ar&gl=SA&ceid=SA:ar"),
        ("Health", "https://news.google.com/rss/search?q=الصحة+العالمية&hl=ar&gl=SA&ceid=SA:ar"),
        ("Sports", "https://news.google.com/rss/search?q=الرياضة+العالمية&hl=ar&gl=SA&ceid=SA:ar"),
        ("Environment", "https://news.google.com/rss/search?q=المناخ+والبيئة+العالمية&hl=ar&gl=SA&ceid=SA:ar")
    ]
}

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def collect():
    articles = []
    seen = set()

    for language, categories in FEEDS.items():
        for category, url in categories:
            print(f"Checking {language}: {category}")

            try:
                feed = feedparser.parse(url)

                if not feed.entries:
                    print("No entries returned")
                    continue

                for item in feed.entries[:25]:
                    title = clean(item.get("title", ""))
                    link = item.get("link", "")

                    if not title or not link or len(title) < 15:
                        continue

                    source_info = item.get("source", {})
                    publisher = clean(source_info.get("title", ""))

                    if not publisher:
                        publisher = urlparse(link).netloc

                    key = (language, re.sub(r'\W+', '', title.lower()))

                    if key in seen:
                        continue

                    seen.add(key)

                    text_parts = []
                    for field in ("content", "summary", "description"):
                        value = item.get(field, "")
                        if isinstance(value, list):
                            for entry in value:
                                if isinstance(entry, dict):
                                    text_parts.append(entry.get("value", ""))
                        elif value:
                            text_parts.append(str(value))
                    cleaned_parts = []
                    for part in text_parts:
                        part = clean(html.unescape(re.sub(r"<[^>]+>", " ", str(part))))
                        if part and part not in cleaned_parts:
                            cleaned_parts.append(part)
                    summary = max(cleaned_parts, key=len, default="")[:1800]
                    image = ""
                    media = item.get("media_content", [])
                    if media and isinstance(media, list):
                        image = media[0].get("url", "")
                    if not image:
                        thumbnails = item.get("media_thumbnail", [])
                        if thumbnails and isinstance(thumbnails, list):
                            image = thumbnails[0].get("url", "")
                    articles.append({
                        "title": title,
                        "summary": summary,
                        "image": image,
                        "author": clean(item.get("author", "")),
                        "language": language,
                        "category": category,
                        "publisher": publisher,
                        "link": link,
                        "published": item.get("published", ""),
                    })

            except Exception as error:
                print("Feed error:", error)

    return articles

def main():
    os.makedirs("news", exist_ok=True)

    print("\nGLOBAL PULSE WORLDWIDE NEWS")
    print("Languages: English + Arabic")

    articles = collect()

    result = {
        "website": "Global Pulse News",
        "coverage": "Worldwide",
        "languages": ["English", "Arabic"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(articles),
        "english": sum(a["language"] == "English" for a in articles),
        "arabic": sum(a["language"] == "Arabic" for a in articles),
        "articles": articles,
        "automatic_publishing": False
    }

    with open("news/worldwide.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n========== RESULTS ==========")
    print("Total:", result["total"])
    print("English:", result["english"])
    print("Arabic:", result["arabic"])
    print("Saved: news/worldwide.json")
    print("Publishing: DISABLED")

if __name__ == "__main__":
    main()
