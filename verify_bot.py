import feedparser
import requests
import json
import re
import os
from difflib import SequenceMatcher
from urllib.parse import urlparse
from datetime import datetime, timezone

SOURCES = {
    "Saudi Gazette": "https://saudigazette.com.sa/rssFeed/74",
    "Umm Al-Qura": "https://www.uqn.gov.sa/rssFeed/19",
    "Arab News": "https://news.google.com/rss/search?q=site:arabnews.com+Saudi&hl=en&gl=SA&ceid=SA:en",
    "SPA": "https://news.google.com/rss/search?q=site:spa.gov.sa+Saudi&hl=ar&gl=SA&ceid=SA:ar",
    "Al Riyadh": "https://news.google.com/rss/search?q=site:alriyadh.com&hl=ar&gl=SA&ceid=SA:ar",
    "Okaz": "https://news.google.com/rss/search?q=site:okaz.com.sa&hl=ar&gl=SA&ceid=SA:ar",
}

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

def publisher(entry, fallback):
    source = entry.get("source", {}).get("title", "")
    if source:
        return source.strip()

    domain = urlparse(entry.get("link", "")).netloc.lower()
    return domain or fallback

def collect():
    articles = []

    for name, url in SOURCES.items():
        print("Reading:", name)

        try:
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                print("Feed unavailable:", name)
                continue

            for item in feed.entries[:30]:
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()

                if not title or not link:
                    continue

                articles.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher(item, name),
                    "feed": name,
                    "published": item.get("published", "")
                })

        except Exception as error:
            print("Error:", name, error)

    return articles

def compare(a, b):
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()

def verify(articles):
    output = []

    for article in articles:
        matches = []

        for other in articles:
            if article["link"] == other["link"]:
                continue

            if article["publisher"].lower() == other["publisher"].lower():
                continue

            score = compare(article["title"], other["title"])

            if score >= 0.58:
                matches.append({
                    "publisher": other["publisher"],
                    "title": other["title"],
                    "similarity": round(score, 2),
                    "link": other["link"]
                })

        unique_publishers = {
            x["publisher"].lower() for x in matches
        }

        confirmed = len(unique_publishers) >= 1

        article["matching_reports"] = matches
        article["independent_source_count"] = len(unique_publishers)
        article["status"] = (
            "CANDIDATE_FOR_HUMAN_REVIEW"
            if confirmed else "PENDING_VERIFICATION"
        )
        article["verified"] = False

        output.append(article)

    return output

def main():
    os.makedirs("news", exist_ok=True)

    print("\nGLOBAL PULSE VERIFICATION BOT")
    articles = collect()

    results = verify(articles)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "articles": results,
        "publication_enabled": False
    }

    with open("news/verification.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    candidates = sum(
        x["status"] == "CANDIDATE_FOR_HUMAN_REVIEW"
        for x in results
    )

    print("\nTotal:", len(results))
    print("Candidates for review:", candidates)
    print("Pending:", len(results) - candidates)
    print("Saved: news/verification.json")
    print("Automatic publishing: DISABLED")

if __name__ == "__main__":
    main()
