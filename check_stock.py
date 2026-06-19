"""
Amul Stock Checker
-------------------
Visits an Amul shop product page, sets the delivery pincode (just like a real
user would), checks whether the product is in stock for that pincode, and
sends an email alert if it is.

Designed to be run on a schedule (e.g. every 4 hours via GitHub Actions cron,
or your own cron/Task Scheduler).
"""

import os
import sys
import smtplib
import traceback
from email.mime.text import MIMEText
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ----------------------------- Configuration ------------------------------ #

PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "https://shop.amul.com/en/product/amul-chocolate-whey-protein-34-g-or-pack-of-60-sachets",
)
PINCODE = os.environ.get("PINCODE", "560016")

GMAIL_USER = os.environ.get["GMAIL_USER","dhanushspjimr@gmail.com"]               # sender Gmail address
GMAIL_APP_PASSWORD = os.environ.get["GMAIL_APP_PASSWORD","frtwsjlllwkjcuak"]  # 16-char Gmail App Password
TO_EMAIL = os.environ.get("TO_EMAIL", "GMAIL_USER")    # recipient (defaults to sender)

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Phrases that indicate the product is OUT of stock on this page.
OUT_OF_STOCK_MARKERS = ["notify me", "sold out", "out of stock"]
# Phrases that indicate the product IS available to order.
IN_STOCK_MARKERS = ["add to cart", "add to wishlist", "buy now"]


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")


def set_pincode(page) -> None:
    """Open the pincode selector and enter the configured pincode."""
    # The site shows a "Select Delivery Pincode" box. There's usually a
    # visible input for it; if it's hidden behind a clickable element first,
    # we try clicking common triggers before looking for the input.
    possible_triggers = [
        "text=Select Delivery Pincode",
        "text=Select Pincodes",
        "[id*='pincode' i]",
    ]
    for trigger in possible_triggers:
        try:
            el = page.locator(trigger).first
            if el.is_visible(timeout=1500):
                el.click(timeout=1500)
                break
        except Exception:
            continue

    # Now find the actual text input for the pincode and type it in.
    input_selectors = [
        "input[placeholder*='pincode' i]",
        "input[name*='pincode' i]",
        "input#search",
        "input[type='text']",
    ]
    pincode_input = None
    for sel in input_selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                pincode_input = loc
                break
        except Exception:
            continue

    if pincode_input is None:
        raise RuntimeError("Could not find the pincode input field on the page.")

    pincode_input.fill(PINCODE)
    page.wait_for_timeout(800)

    # Try pressing Enter first (works on most StoreHippo-based sites).
    try:
        pincode_input.press("Enter")
    except Exception:
        pass

    # Also try clicking a nearby submit/apply/search button, in case Enter
    # alone doesn't trigger it.
    for btn_text in ["Apply", "Search", "Submit", "Go"]:
        try:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if btn.is_visible(timeout=800):
                btn.click(timeout=800)
                break
        except Exception:
            continue

    # Give the page time to refresh stock info after the pincode is set.
    page.wait_for_timeout(2500)


def check_stock(page) -> bool:
    """Return True if the product appears to be in stock."""
    body_text = page.locator("body").inner_text().lower()

    if any(marker in body_text for marker in OUT_OF_STOCK_MARKERS):
        return False
    if any(marker in body_text for marker in IN_STOCK_MARKERS):
        return True

    # Ambiguous — treat as out of stock to avoid false "available" emails,
    # but this will show up clearly in the logs for debugging.
    log("WARNING: Could not confidently determine stock status from page text.")
    return False


def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [TO_EMAIL], msg.as_string())

    log(f"Email sent to {TO_EMAIL}")


def main() -> None:
    log(f"Checking: {PRODUCT_URL} | pincode={PINCODE}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ))
        try:
            page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)

            try:
                set_pincode(page)
            except Exception as e:
                log(f"Could not set pincode automatically: {e}")
                if DEBUG:
                    page.screenshot(path="debug_pincode_step.png", full_page=True)

            in_stock = check_stock(page)

            if DEBUG:
                page.screenshot(path="debug_final.png", full_page=True)
                with open("debug_final.html", "w", encoding="utf-8") as f:
                    f.write(page.content())

            log(f"Result: {'IN STOCK' if in_stock else 'out of stock'}")

            if in_stock:
                send_email(
                    subject="🟢 Amul product is back in stock!",
                    body=(
                        f"Good news — the product looks available for pincode {PINCODE}:\n\n"
                        f"{PRODUCT_URL}\n\n"
                        "Go grab it before it sells out again!"
                    ),
                )
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("Script failed with an error:")
        traceback.print_exc()
        sys.exit(1)
