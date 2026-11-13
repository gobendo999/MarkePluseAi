import re
import json
import logging
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Topic 23: Resilient E-Commerce Web Scraper
    Hybrid Scraper: Fast static HTML parsing with Playwright Headless Chromium
    fallback for dynamic JavaScript sites (Daraz, Amazon, etc.)
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    @classmethod
    def scrape_product(cls, url: str) -> dict:
        """
        যেকোনো প্রোডাক্টের URL থেকে ডাইনামিক বা স্ট্যাটিক উপায়ে দাম, নাম, কারেন্সি বের করে
        """
        url_lower = url.lower()

        # ১. দারাজের মতো ডাইনামিক জাভাস্ক্রিপ্ট নির্ভর সাইটের জন্য সরাসরি Playwright ব্যবহার করা
        # যাতে আসল অফার/সেল প্রাইস (যেমন ৳ ৪২০) পাওয়া যায় (বেস ক্যাটালগ ৳ ৮০০ নয়)
        if "daraz" in url_lower:
            pw_result = cls._scrape_with_playwright(url)
            if pw_result.get("success") and pw_result.get("price", Decimal("0.00")) > Decimal("0.00"):
                return pw_result

        # ২. সাধারণ স্ট্যাটিক স্ক্র্যাপিং (requests + BeautifulSoup) - সুপার ফাস্ট
        static_result = cls._scrape_static(url)
        if static_result.get("success") and static_result.get("price", Decimal("0.00")) > Decimal("0.00"):
            return static_result

        # ৩. স্ট্যাটিক স্ক্র্যাপিংয়ে দাম না পেলে Playwright ফলব্যাক
        if not ("daraz" in url_lower):
            pw_fallback = cls._scrape_with_playwright(url)
            if pw_fallback.get("success") and pw_fallback.get("price", Decimal("0.00")) > Decimal("0.00"):
                return pw_fallback

        # যদি দাম না পাওয়া যায় তবে স্ট্যাটিক রেসপন্স বা ডিফল্ট রিটার্ন
        return static_result if static_result.get("success") else {
            "success": False,
            "error": static_result.get("error", "Unable to extract price"),
        }

    @classmethod
    def _scrape_with_playwright(cls, url: str) -> dict:
        """
        Headless Chromium ব্রাউজারের মাধ্যমে পেজ রেন্ডার করে রিয়েল-টাইম জাভাস্ক্রিপ্ট প্রাইস রিড করা
        """
        try:
            from playwright.sync_api import sync_playwright

            store_name = "Generic Store"
            currency = "USD"
            url_lower = url.lower()

            if "daraz" in url_lower:
                store_name = "Daraz"
                currency = "BDT"
            elif "amazon" in url_lower:
                store_name = "Amazon"
                currency = "USD"
            elif "startech" in url_lower:
                store_name = "Star Tech"
                currency = "BDT"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=cls.HEADERS["User-Agent"])
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                # ডাইনামিক প্রাইস রেন্ডার হওয়ার জন্য ৩ সেকেন্ড অপেক্ষা
                page.wait_for_timeout(3200)

                # টাইটেল সংগ্রহ
                title = None
                for t_sel in [".pdp-mod-product-badge-title", "h1", "title"]:
                    t_loc = page.locator(t_sel)
                    if t_loc.count() > 0:
                        candidate = t_loc.first.inner_text().strip()
                        if candidate:
                            title = candidate
                            break

                # প্রাইস সংগ্রহ: .pdp-price এলিমেন্টের প্রথমটি হলো একচুয়াল সেল প্রাইস
                price = None
                for p_sel in [".pdp-price", ".pdp-price_type_normal", ".pdp-mod-product-price", "[class*='pdp-price']"]:
                    p_loc = page.locator(p_sel)
                    if p_loc.count() > 0:
                        raw = p_loc.first.inner_text()
                        cleaned = cls._clean_price(raw)
                        if cleaned > Decimal("0.00"):
                            price = cleaned
                            if "৳" in raw or "tk" in raw.lower():
                                currency = "BDT"
                            break

                browser.close()

                return {
                    "success": True,
                    "title": title[:400] if title else "Tracked Product",
                    "price": price or Decimal("0.00"),
                    "currency": currency,
                    "store_name": store_name,
                    "stock_status": "IN_STOCK" if (price and price > Decimal("0.00")) else "UNKNOWN",
                }
        except Exception as e:
            logger.warning(f"Playwright scraping failed for {url}: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def _scrape_static(cls, url: str) -> dict:
        """
        সাধারণ স্ট্যাটিক HTML পার্সার
        """
        try:
            response = requests.get(url, headers=cls.HEADERS, timeout=12)
            response.raise_for_status()
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch page: {str(e)}"}

        page_text = response.text
        soup = BeautifulSoup(response.content, "html.parser")

        store_name = "Generic Store"
        currency = "USD"
        url_lower = url.lower()

        if "daraz" in url_lower:
            store_name = "Daraz"
            currency = "BDT"
        elif "amazon" in url_lower:
            store_name = "Amazon"
            currency = "USD"
        elif "startech" in url_lower:
            store_name = "Star Tech"
            currency = "BDT"
        elif "ryans" in url_lower:
            store_name = "Ryans Computers"
            currency = "BDT"

        title = None
        price = None

        # Schema.org JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    if data.get("@type") == "Product" or "Product" in str(data.get("@type", "")):
                        title = data.get("name")
                        offers = data.get("offers", {})
                        if isinstance(offers, dict):
                            price = offers.get("price") or offers.get("lowPrice")
                            if offers.get("priceCurrency"):
                                currency = offers.get("priceCurrency").upper()
                        elif isinstance(offers, list) and len(offers) > 0:
                            price = offers[0].get("price")
                            if offers[0].get("priceCurrency"):
                                currency = offers[0].get("priceCurrency").upper()
                        if price:
                            break
            except Exception:
                continue

        # OpenGraph
        if not title:
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title = og_title.get("content")

        if not price:
            og_price = soup.find("meta", property="product:price:amount") or soup.find("meta", property="og:price:amount")
            if og_price:
                price = og_price.get("content")
            og_currency = soup.find("meta", property="product:price:currency") or soup.find("meta", property="og:price:currency")
            if og_currency and og_currency.get("content"):
                currency = og_currency.get("content").upper()

        # Daraz static regex
        if not price:
            m_daraz = re.search(r'pdt_price(?:\\+|")*:\s*(?:\\+|")*([^\\"]+)', page_text)
            if m_daraz:
                price = m_daraz.group(1)

        # CSS Selectors
        if not price:
            for selector in [".price_color", ".price", ".product-price", ".pdp-price", ".a-price .a-offscreen", ".current-price"]:
                price_el = soup.select_one(selector)
                if price_el:
                    price = price_el.get_text(strip=True)
                    break

        # Fallback Title
        if not title:
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "Scraped Product"

        if price:
            raw_price_str = str(price)
            if "৳" in raw_price_str or "tk" in raw_price_str.lower():
                currency = "BDT"
            elif "€" in raw_price_str:
                currency = "EUR"
            elif "₹" in raw_price_str:
                currency = "INR"
            elif "£" in raw_price_str:
                currency = "GBP"

        clean_price = cls._clean_price(price) if price else Decimal("0.00")

        return {
            "success": True,
            "title": title[:400] if title else "Untitled Product",
            "price": clean_price,
            "currency": currency,
            "store_name": store_name,
            "stock_status": "IN_STOCK" if clean_price > Decimal("0.00") else "UNKNOWN",
        }

    @staticmethod
    def _clean_price(price_str) -> Decimal:
        """
        কারেন্সি সিম্বল বাদ দিয়ে পিওর নম্বরে রূপান্তর করা
        """
        if isinstance(price_str, (int, float, Decimal)):
            return Decimal(str(price_str))

        cleaned = re.sub(r"[^\d.]", "", str(price_str))
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal("0.00")

    @classmethod
    def search_startech(cls, query: str, limit: int = 5) -> list:
        """
        Star Tech লাইভ সার্চ ইঞ্জিন থেকে সরাসরি প্রোডাক্টের নাম, দাম ও লিংক বের করে
        """
        try:
            url = f"https://www.startech.com.bd/product/search?search={query}"
            res = requests.get(url, headers=cls.HEADERS, timeout=10)
            if res.status_code != 200:
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select(".p-item")[:limit]
            results = []

            for item in items:
                name_tag = item.select_one(".p-item-name a")
                price_tag = item.select_one(".p-item-price")
                img_tag = item.select_one(".p-item-img img")

                if name_tag and price_tag:
                    title = name_tag.text.strip()
                    product_url = name_tag.get("href", "")
                    actual_price_tag = price_tag.select_one(".price-new") or price_tag.select_one("span") or price_tag
                    raw_price = actual_price_tag.text.strip()
                    price = cls._clean_price(raw_price)
                    image_url = img_tag.get("src", "") if img_tag else ""

                    results.append({
                        "title": title,
                        "price": float(price),
                        "currency": "BDT",
                        "url": product_url,
                        "image_url": image_url,
                        "store_name": "Star Tech",
                    })

            return results
        except Exception as e:
            logger.error(f"StarTech search error for '{query}': {e}")
            return []
