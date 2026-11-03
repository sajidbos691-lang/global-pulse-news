import feedparser
import requests
import json
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SOURCES = {
    "Google News Saudi": "https://news.google.com/rss/search?q=Saudi+Arabia&hl=ar&gl=SA&ceid=SA:ar",
    "Google News Riyadh": "https://news.google.com/rss/search?q=Riyadh&hl=ar&gl=SA&ceid=SA:ar",
    "Google News Economy": "https://news.google.com/rss/search?q=Saudi+Arabia+economy&hl=ar&gl=SA&ceid=SA:ar",
    "Google News Technology": "https://news.google.com/rss/search?q=Saudi+Arabia+technology&hl=ar&gl=SA&ceid=SA:ar"
}

os.makedirs("news", exist_ok=True)

def get_news():
    results = []
    seen = set()

    for source, url in SOURCES.items():
        print("Checking:", source)
        try:
            feed = feedparser.parse(url)

            for item in feed.entries[:20]:
                title = item.get("title", "").strip()
                link = item.get("link", "")

                if not title or not link:
                    continue

                key = title.lower()
                if key in seen:
                    continue

                seen.add(key)

                results.append({
                    "title": title,
                    "link": link,
                    "source_feed": source,
                    "published": item.get("published", ""),
                    "summary": item.get("summary", ""),
                    "verified": False,
                    "status": "PENDING_REVIEW"
                })

        except Exception as e:
            print("Source error:", e)

    return results

def main():
    print("GLOBAL PULSE NEWS BOT")
    print(datetime.now())

    news = get_news()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(news),
        "articles": news
    }

    filename = "news/news_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\nTotal articles found:", len(news))
    print("Saved:", filename)
    print("All articles require verification before publication.")

if __name__ == "__main__":
    main()
