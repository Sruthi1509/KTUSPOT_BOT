"""Fetch the newest announcements displayed on KTU's announcements page."""

from datetime import date, datetime, timedelta

from playwright.sync_api import sync_playwright

URL = "https://ktu.edu.in/Menu/announcements"
ANNOUNCEMENT_SELECTOR = "div.p-t-15.p-b-15.shadow.row.m-b-25"


def _is_within_last_two_days(date_text: str) -> bool:
    """KTU publishes dates such as 'Tuesday, August 4, 2026'."""
    try:
        announcement_date = datetime.strptime(date_text, "%A, %B %d, %Y").date()
    except ValueError:
        return False
    return announcement_date >= date.today() - timedelta(days=2)


def fetch_announcements(debug: bool = False) -> list[dict]:
    """Return the announcements currently listed on the first KTU page."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_selector(ANNOUNCEMENT_SELECTOR, timeout=30_000)
            if debug:
                with open("debug_rendered.html", "w", encoding="utf-8") as output:
                    output.write(page.content())
                print("Saved debug_rendered.html")

            results = []
            for card in page.locator(ANNOUNCEMENT_SELECTOR).all():
                title = (card.locator("h6.f-w-bold").first.text_content() or "").strip()
                if not title:
                    continue
                date = (card.locator("div.text-theme").first.text_content() or "").strip()
                if not _is_within_last_two_days(date):
                    continue
                description = (card.locator("div.m-t-10.font-14:not(.text-theme)").first.text_content() or "").strip()
                button = card.locator("button").first
                resource_id = button.get_attribute("value") if card.locator("button").count() else ""
                results.append({"title": title, "date": date, "description": description,
                                "link": page.url, "resource_id": resource_id or ""})
            return results
        finally:
            browser.close()


if __name__ == "__main__":
    for announcement in fetch_announcements(debug=True):
        print(announcement)
