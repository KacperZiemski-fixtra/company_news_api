import re
from dotenv import load_dotenv
import os

from langfuse import Langfuse
from pydantic import BaseModel, Field

from PromptMaintenance import get_prompt, query_openai_responses_web_search
from company_news.models import Company, Industry, CompanyIndustryGroup, Article, MainTopic

import requests
from bs4 import BeautifulSoup
import html2text


def extract_full_page_markdown(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "footer", "header", "nav", "aside"]):
            tag.decompose()

        cleaned_html = str(soup)

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_tables = False
        markdown_text = h.handle(cleaned_html)

        return markdown_text.strip()

    except Exception as e:
        print(f"An error occured while converting the page: {e}")
        return ""


def extract_full_article_text(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)

        article_text = text.strip()

        # Deleting disclaimers
        disclaimer_pattern = r"Disclaimer:.*?details\."
        article_text = re.sub(disclaimer_pattern, '', article_text, flags=re.DOTALL).strip()

        return article_text
    except Exception as e:
        print(e)
        return ""

from urllib.parse import urlparse

def get_url_slug(url): # Returns the last element of URL without trailing slash.
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    if not path:
        return ''
    return path.split('/')[-1].lower()


from typing import List
import json

def summarize_news(news_list, company_name):
    load_dotenv()

    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

    print("Summarizing news...")
    try:
        prompt = get_prompt("NewsSummaryWizard")
        if prompt:
            final_news = []

            class NewsSummary(BaseModel):
                title: str = ""
                url: str = ""
                author: str = ""
                publication_date: str = ""
                summary: str = ""
                main_topics: List[str] = Field(default_factory=list)

            for n in news_list:
                # trace = langfuse.trace(name="Create news summary", user_id=company_name)
                system_message = prompt.compile(news_url=n.get('link'))

                # generation = trace.generation(
                #     name="Summarize news article",
                #     model="gpt-4o-mini",
                #     input={"prompt": system_message}
                # )

                response = query_openai_responses_web_search(system_message, NewsSummary)

                # generation.end(output=response)

                if isinstance(response.output_text, str):
                    parsed = json.loads(response.output_text)
                    news_obj = NewsSummary(**parsed)
                    final_news.append(news_obj.dict())
                else:
                    print("[WARN] output_text is not a string: ", response.output_text)

            return final_news
        else:
            return []
    except Exception as e:
        print(f"[ERROR] An error occurred while summarizing the news: {e}")
        return []


def save_final_news(final_news, searched_company, base_url, user_industry):
    company, _ = Company.objects.get_or_create(name=searched_company, defaults={'website': base_url})
    industry, _ = Industry.objects.get_or_create(name=user_industry)
    group, _ = CompanyIndustryGroup.objects.get_or_create(company=company, industry=industry)

    Article.objects.filter(group=group).delete()

    for news in final_news:
        article = Article.objects.create(
            group=group,
            title=news['title'],
            url=news['url'],
            author=news.get('author', ''),
            publication_date=news.get('publication_date'),
            summary=news.get('summary', '')
        )

        for topic in news.get('main_topics', []):
            MainTopic.objects.create(article=article, topic=topic)
