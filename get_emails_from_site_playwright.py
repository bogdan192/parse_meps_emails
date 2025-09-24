import asyncio
import random
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

BASE_URL = "https://www.europarl.europa.eu/meps/en/full-list/all"
LANGUAGES = ["en-US,en;q=0.9", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9", "es-ES,es;q=0.9"]

async def get_mep_profile_links(page):
    await page.goto(BASE_URL)
    links = await page.eval_on_selector_all(
        ".erpl_member-list > div:nth-child(1) a",
        "els => els.map(a => a.getAttribute('href'))"
    )
    return links

async def get_mep_email(playwright, mep_url, semaphore, ua):
    async with semaphore:
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

async def main():
    ua = UserAgent()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        mep_links = await get_mep_profile_links(page)
        await browser.close()

        semaphore = asyncio.Semaphore(3)
        tasks = []
        for url in mep_links:
            await asyncio.sleep(random.uniform(0.5,1.5))
            tasks.append(get_mep_email(playwright, url, semaphore, ua))

        for coro in asyncio.as_completed(tasks):
            email = await coro
            if email:
                print(email)

if __name__ == "__main__":
    asyncio.run(main())