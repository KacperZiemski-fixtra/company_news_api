import os
from serpapi import GoogleSearch
from datetime import datetime, timedelta
from NewsMaintenance import get_url_slug, summarize_news, save_final_news
from SiteCrawler import scrape_company_news, extract_full_article_text

industry_sources = {
    "fintech": [
        "bankier.pl", "cashless.pl", "finextra.com", "bloomberg.com", "forrester.com", "finance.yahoo.com",
        "fintechfutures.com", "thepaypers.com", "paymentsjournal.com", "techcrunch.com", "businessinsider.com",
        "fintechnews.sg", "finews.asia", "thefintechtimes.com"
    ],
    "banking": [
        "reuters.com", "bloomberg.com", "bankingtech.com", "thebanker.com", "americanbanker.com"
    ],
    "energy": [
        "energetyka24.com", "energyvoice.com", "greentechmedia.com", "energylivenews.com", "power-technology.com",
        "oilprice.com", "renewableenergyworld.com", "cleantechnica.com", "energycentral.com"
    ],
    "logistics": [
        "logistyka.rp.pl", "trans.info", "supplychaindigital.com", "freightwaves.com", "theloadstar.com",
        "logisticsmanager.com", "supplychainquarterly.com", "supplychaintoday.com"
    ],
    "ecommerce": [
        "emarketer.com", "retaildive.com", "practicalecommerce.com", "ecommercebytes.com", "internetretailing.net",
        "ecommerce-news.eu", "businessinsider.com", "techcrunch.com"
    ],
    "cybersecurity": [
        "cyberscoop.com", "threatpost.com", "krebsonsecurity.com", "darkreading.com", "infosecurity-magazine.com",
        "securityweek.com", "thehackernews.com", "zdnet.com"
    ],
    "telecommunications": [
        "lightreading.com", "telecoms.com", "totaltele.com", "fiercetelecom.com", "rcrwireless.com"
    ],
    "healthcare": [
        "healthcareitnews.com", "medgadget.com", "mobihealthnews.com", "medicalnewstoday.com", "healthline.com",
        "healthcarefinancenews.com"
    ],
    "automotive": [
        "autonews.com", "automotiveworld.com", "caranddriver.com", "motortrend.com", "autoexpress.co.uk"
    ],
    "technology": [
        "techcrunch.com", "wired.com", "thenextweb.com", "venturebeat.com", "theverge.com", "zdnet.com",
        "cnet.com", "gizmodo.com", "mashable.com", "engadget.com"
    ],
    "real_estate": [
        "therealdeal.com", "housingwire.com", "inman.com", "bloomberg.com", "propertywire.com"
    ]
}

excluded_sources = [
    "ft.com"
]

def filter_recent_news(news_list, max_age_days=730):
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    filtered = []
    for n in news_list:
        try:
            raw_date = n.get("date", "")
            parsed_date = datetime.strptime(raw_date.split(",")[0], "%m/%d/%Y")
            if parsed_date > cutoff:
                n["parsed_date"] = parsed_date
                filtered.append(n)
        except Exception as e:
            print(f"Could not parse the date: {n.get('title')} → {e}")
            continue
    return filtered

def deduplicate_by_link(news_list):
    if not news_list:
        return []

    seen_links = set()
    unique_news = []

    for news in news_list:
        link = news.get('link', '').strip()

        if link and link not in seen_links:
            seen_links.add(link)
            unique_news.append(news)

    return unique_news

def industry_filter(news_list, target_industry, threshold=0.10):
    industry_keywords = {
        "technology": ["tech", "software", "AI", "artificial intelligence", "startup", "digital", "app", "platform", "technology"],
        "finance": ["bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money"],
        "healthcare": ["health", "medical", "hospital", "pharma", "medicine", "treatment", "patient", "healthcare"],
        "energy": ["energy", "oil", "renewable", "solar", "wind", "electric", "battery", "power"],
        "fintech": ["tech", "software", "AI", "artificial intelligence", "startup", "digital", "app", "platform", "technology", "bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money", "cloud"],
        "banking": ["bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money"]
    }

    keywords = industry_keywords.get(target_industry.lower(), [target_industry.lower()])
    result_news = []

    for n in news_list:
        text = (n.get("title", "") + " " + n.get("content", "")[:300]).lower()

        # Counting keywords matches
        matches = sum(1 for keyword in keywords if keyword in text)
        score = min(matches / len(keywords), 1.0)  # Normalize to 0-1

        # if score >= threshold:
        #     n["industry_score"] = score
        #     result_news.append(n)

        n["industry_score"] = score
        result_news.append(n)

    return result_news

def check_if_company_related(news_list, company_name):
    result_news = []
    for n in news_list:
        if 'link' in n:
            text = extract_full_article_text(n['link'])
            title = n['title']
            if company_name in title or company_name in text:
                n["content"] = text
                result_news.append(n)
    return result_news

def filter_by_known_sources(news_list, target_industry, source_database):
    trusted_sources = source_database.get(target_industry, [])
    result_news = []
    result_news_known_sources = []
    for n in news_list:
        link = n.get("link", "").lower()
        if any(trusted_source.lower() in link for trusted_source in trusted_sources):
            n["industry_score"] = 1.0  # Setting the highest possible score
            result_news_known_sources.append(n)
        elif any(excluded_source.lower() in link for excluded_source in excluded_sources):
            continue
        else:
            result_news.append(n)
    return result_news_known_sources, result_news

def get_news(base_url, user_industry, searched_company):
    try:
        news_articles = scrape_company_news(base_url, searched_company, max_articles=15)

        print("Searching for news with SERPAPI...")
        params = {
            "engine": "google_news",
            "q": searched_company,
            "api_key": os.getenv("SERPAPI_KEY")
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        # Pipeline execution
        news_results = results["news_results"]  # News from Serp API
        print(f"{len(news_results)} news found")
        print("Processing...")

        company_related_news = check_if_company_related(news_results,
                                                        searched_company)  # Company related news filtering
        company_related_news += news_articles
        recent_news = filter_recent_news(company_related_news)  # Date filtering
        deduplicated_news = deduplicate_by_link(recent_news)  # URL and title deduplication
        industry_news_known_sources, industry_news_not_known_sources = filter_by_known_sources(deduplicated_news,
                                                                                               user_industry,
                                                                                               industry_sources)  # Setting priority for industry related sources
        industry_news = industry_filter(industry_news_not_known_sources, user_industry)  # Industry filtering
        industry_news += industry_news_known_sources

        sorted_news = sorted(
            industry_news,
            key=lambda n: (n.get('industry_score', 0), n.get('parsed_date', datetime.min)),
            reverse=True
        )

        best_news = sorted_news[:9]

        final_news = summarize_news(best_news, searched_company)

        # save_final_news(final_news, searched_company, base_url, user_industry)

        return final_news
    except Exception as e:
        print(e)
        return []
