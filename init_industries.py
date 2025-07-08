import os
from dotenv import load_dotenv
import django


load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "company_news.settings")
django.setup()

from company_news.models import Industry, IndustrySources, IndustryKeywords

industry_sources = {
    "fintech": [
        "bankier.pl", "cashless.pl", "finextra.com", "bloomberg.com", "forrester.com", "finance.yahoo.com",
        "fintechfutures.com", "thepaypers.com", "paymentsjournal.com", "techcrunch.com", "businessinsider.com",
        "fintechnews.sg", "finews.asia", "thefintechtimes.com"
    ],
    "banking": [
        "reuters.com", "bloomberg.com", "bankingtech.com", "thebanker.com", "americanbanker.com", "ft.com"
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
        "therealdeal.com", "housingwire.com", "inman.com", "bloomberg.com", "ft.com", "propertywire.com"
    ]
}

industry_keywords = {
    "technology": ["tech", "software", "AI", "artificial intelligence", "startup", "digital", "app", "platform", "technology"],
    "finance": ["bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money"],
    "healthcare": ["health", "medical", "hospital", "pharma", "medicine", "treatment", "patient", "healthcare"],
    "energy": ["energy", "oil", "renewable", "solar", "wind", "electric", "battery", "power"],
    "fintech": ["tech", "software", "AI", "artificial intelligence", "startup", "digital", "app", "platform", "technology", "bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money", "cloud"],
    "banking": ["bank", "investment", "finance", "fintech", "crypto", "blockchain", "trading", "money", "fraud"]
}

for name, sources in industry_sources.items():
    industry, created = Industry.objects.get_or_create(name=name)
    for source in sources:
        IndustrySources.objects.get_or_create(industry=industry, source=source)

for name, keywords in industry_keywords.items():
    try:
        industry = Industry.objects.get(name=name)
        for word in keywords:
            IndustryKeywords.objects.get_or_create(industry=industry, keyword=word)
    except Industry.DoesNotExist:
        print(f"Industry {name} does not exist")

print("Industry data was saved into the database.")
