import os
from typing import List
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

from dotenv import load_dotenv
from langfuse import Langfuse
from playwright.sync_api import sync_playwright
import re
from datetime import datetime
from pydantic import BaseModel
from NewsMaintenance import extract_full_article_text, get_url_slug
from urllib.parse import urlparse
from dateutil.parser import parse
from PromptMaintenance import get_prompt, query_openai_responses_web_search

def is_allowed_to_crawl(base_url):
    robots_url = base_url.split('/')[0] + '//' + base_url.split('/')[2] + '/robots.txt'
    try:
        response = requests.get(robots_url, timeout=10)
        robots_txt = response.text

        rp = RobotFileParser()
        rp.parse(robots_txt.splitlines())

        if rp.can_fetch("*", base_url):
            print(f"[INFO] Crawling is allowed on {base_url}")
            return True
        else:
            print(f"[INFO] Crawling is not allowed on {base_url} as per robots.txt")
            return False
    except Exception as e:
        print(f"[ERROR] An error occurred while checking robots.txt: {e}")
        return True

def find_news_page(base_url, keywords=None):
    if not is_allowed_to_crawl(base_url):
        return None

    if keywords is None:
        keywords = ["news", "whats-new", "press",  "media-centre", "media-", "media/" ]

    try:
        print(f"[INFO] Searching for news tab on {base_url}...")
        resp = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"].lower()
            text = link.get_text().lower()
            if any(kw in href or kw in text for kw in keywords):
                news_url = urljoin(base_url, link["href"])
                print(f"[FOUND] News tab found: {news_url}")
                return news_url
    except Exception as e:
        print(f"[ERROR] An error occurred while downloading main page: {e}")

    return None

def find_news_page_with_openai(base_url, searched_company):
    load_dotenv()

    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

    print("Searching for news tab with OPENAI...")
    try:
        prompt = get_prompt("FindNewsTab")
        if prompt:
            # trace = langfuse.trace(name="Find nes tab", user_id=searched_company)
            system_message = prompt.compile(base_url=base_url)

            # generation = trace.generation(
            #     name="Summarize news article",
            #     model="gpt-4o-mini",
            #     input={"prompt": system_message}
            # )

            class NewsTab(BaseModel):
                URL: str

            response = query_openai_responses_web_search(system_message, NewsTab)
            # generation.end(output=response)
            print(response)

            news_tab = response.output_parsed

            print(news_tab)

            if news_tab and news_tab.URL.strip():
                return  news_tab.URL
            else:
                return None
    except Exception as e:
        print(f"[ERROR] An error occurred while searching for a news tab: {e}")
        return None

def find_articles_with_openai(news_url, searched_company):
    load_dotenv()

    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

    print("Searching for news with OPENAI...")
    try:
        prompt = get_prompt("FindNewsFromLinks")
        if prompt:
            # trace = langfuse.trace(name="Find news on webpage", news_url=news_url, user_id=searched_company)
            system_message = prompt.compile(news_url=news_url)

            # generation = trace.generation(
            #     name="Find news",
            #     model="gpt-4o-mini",
            #     input={"prompt": system_message}
            # )

            class NewsArticle(BaseModel):
                title: str
                link: str
                date: str

            class NewsList(BaseModel):
                articles: List[NewsArticle]

            response = query_openai_responses_web_search(system_message, NewsList)
            # generation.end(output=response)

            openai_news = [article.dict() for article in response.output_parsed.articles]
            print(f"[INFO] Successfully collected {len(openai_news)} news articles.")
            return openai_news
        else:
            print("Prompt could not be fetched")
            return []
    except Exception as e:
        print("[ERROR] ", e)
        return []

def extract_articles_with_playwright(news_url, max_articles=10, min_title_length=20):
    if not is_allowed_to_crawl(news_url):
        return None

    added = set()

    def extract_date_from_text(text):
        patterns = [
            (r"\d{4}-\d{2}-\d{2}", 1),  # Format: 2025-05-08
            (r"\d{2}/\d{2}/\d{4}", 2),  # Format: 08/05/2025
            (r"\d{1,2}\s+\w+\s+\d{4}", 3),  # Format: 8 May 2025
            (r"\w+\s+\d{1,2},\s+\d{4}", 4),  # Format: May 8, 2025
            (r"\d{1,2}\.\d{1,2}\.\d{4}", 5),  # Format: 08.05.2025
            (r"\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]{3,}", 6),  # Format: 8th May
            (r"\d{4}\.\d{2}\.\d{2}", 7)  # Format: 2025.05.08
        ]
        for pattern, fmt in patterns:
            match = re.search(pattern, text)
            if match:
                if fmt == 6:
                    match = re.sub(r"(st|nd|rd|th)", "", match.group(0))
                    current_year = datetime.now().year
                    match += (" " + str(current_year))
                    return match
                return match.group(0)
        return ""

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            print(f"[INFO] Loading the page: {news_url}")
            page.goto(news_url, timeout=60000)
            page.wait_for_timeout(3000)

            anchors = page.query_selector_all("a[href]")
            links_info = []

            base_path = urlparse(news_url).path.rstrip()
        except Exception as e:
            print(e)
            return []

        for a in anchors:
            try:
                title = a.inner_text().strip()
                href = a.get_attribute("href")
                full_url = urljoin(news_url, href)

                if not full_url.startswith(news_url+"/"):
                    if not urlparse(full_url).path.startswith(base_path+"/"):
                        if not len(get_url_slug(full_url)) > 20:
                            continue
                if not title or not href:
                    continue
                if href.startswith("javascript") or href.startswith("#"):
                    continue
                if len(title) < min_title_length:
                    continue
                if full_url in added:
                    continue

                # Searching for publication date in the closest surrounding of the link
                date_text = ""
                parent = a
                for _ in range(3):  # Search through few superior levels
                    parent = parent.evaluate_handle("e => e.parentElement")
                    siblings_text = parent.evaluate("e => e.innerText || ''")
                    date_text = extract_date_from_text(siblings_text)
                    if date_text:
                        break

                if date_text:
                    try:
                        parsed_date = parse(date_text)
                        if parsed_date > datetime.today():
                            parsed_date = parsed_date.replace(year=parsed_date.year-1)
                    except Exception as e:
                        print(f"[WARN] Could not parse the date: {date_text} -> {e}")
                        continue
                else:
                    print(f"[INFO] Missing date for URL: {full_url}")
                    continue

                if not parsed_date:
                    continue

                links_info.append({
                    "title": clear_title(title),
                    "link": full_url,
                    "date": parsed_date.strftime("%m/%d/%Y")
                })
                added.add(full_url)
                if len(links_info) >= max_articles:
                    break
            except Exception as e:
                print(f"[WARN] An error occurred while analyzing the URL: {e}")

        browser.close()
        print(f"[INFO] Successfully collected {len(links_info)} news articles.")
        return links_info


def clear_title(text):
    try:
        if re.search("\n\n", text):
            clean_title = text.split('\n\n')[0]
            return clean_title
        else:
            return text
    except Exception as e:
        print(f"[ERR] An error occurred while clearing the title: {e}")

def scrape_company_news(base_url, searched_company, max_articles=10, deep_scrape=True):
    news_url = find_news_page(base_url)
    if not news_url:
        print("[FAIL] News tab not found")
        news_url = find_news_page_with_openai(base_url, searched_company)
        if not news_url:
            print("[FAIL] News tab not found")
            return []

    articles = set()

    try:
        articles = extract_articles_with_playwright(news_url, max_articles=max_articles)
    except Exception as e:
        print(e)

    if not articles:
        print("[INFO] No news articles — skipping deep-scraping.")
        articles = find_articles_with_openai(news_url, searched_company)
        if not articles:
            return[]

    # Deep scraping only if any news articles were found
    if deep_scrape:
        articles_final = []
        for a in articles:
            try:
                a["content"] = extract_full_article_text(a["link"])
                time.sleep(1.0)
                articles_final.append(a)
            except Exception as e:
                print(e)
    else:
        articles_final = articles

    return articles_final
