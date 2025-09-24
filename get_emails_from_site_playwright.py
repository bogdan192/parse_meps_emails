import asyncio
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from fake_useragent import UserAgent
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.europarl.europa.eu/meps/en/full-list/all"
LANGUAGES = ["en-US,en;q=0.9", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9", "es-ES,es;q=0.9"]

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 5  # Base delay between retries in seconds
MAX_REQUESTS_PER_MINUTE = 20


class RateLimiter:
    def __init__(self, requests_per_minute):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests
                         if now - req_time < timedelta(minutes=1)]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until oldest request expires
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                logging.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)

        self.requests.append(now)


async def get_mep_profile_links(page):
    await page.goto(BASE_URL)
    links = await page.eval_on_selector_all(
        ".erpl_member-list > div:nth-child(1) a",
        "els => els.map(a => a.getAttribute('href'))"
    )
    return links


async def get_mep_email_with_retry(playwright, mep_url, semaphore, ua, rate_limiter):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            async with semaphore:
                await rate_limiter.acquire()

                user_agent = ua.random
                extra_headers = {
                    "Accept-Language": random.choice(LANGUAGES)
                }
                browser = await playwright.chromium.launch()
                context = await browser.new_context(
                    user_agent=user_agent,
                    extra_http_headers=extra_headers
                )
                page = await context.new_page()

                full_url = f"https://www.europarl.europa.eu{mep_url}" if mep_url.startswith('/') else mep_url
                await page.goto(full_url)
                email_href = await page.eval_on_selector(
                    ".link_email",
                    "el => el ? el.getAttribute('href') : null"
                )
                await browser.close()
                return email_href

        except PlaywrightTimeoutError as e:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                logging.error(f"Failed to fetch {mep_url} after {MAX_RETRIES} retries")
                return None

            # Exponential backoff with jitter
            delay = BASE_DELAY * (2 ** retry_count) + random.uniform(0, 2)
            logging.warning(f"Attempt {retry_count} failed for {mep_url}. Retrying in {delay:.2f} seconds")
            await asyncio.sleep(delay)

        except Exception as e:
            logging.error(f"Unexpected error for {mep_url}: {str(e)}")
            return None


async def main():
    ua = UserAgent()
    rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            mep_links = await get_mep_profile_links(page)
        finally:
            await browser.close()

        semaphore = asyncio.Semaphore(2)  # Reduced concurrent connections
        tasks = []

        for url in mep_links:
            tasks.append(get_mep_email_with_retry(playwright, url, semaphore, ua, rate_limiter))

        results = []
        for coro in asyncio.as_completed(tasks):
            email = await coro
            if email:
                print(email)
                results.append(email)

        logging.info(f"Successfully retrieved {len(results)} emails out of {len(mep_links)} attempts")
        logging.info('Writing emails to mep_emails.txt')
        with open("mep_emails.txt", "w") as f:
            for email in results:
                if 'mailto:' in email:
                    email = email.replace('mailto:', '').strip()
                f.write(f"{email}\n")

if __name__ == "__main__":
    asyncio.run(main())
