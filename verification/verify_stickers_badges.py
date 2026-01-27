from playwright.sync_api import sync_playwright
import time

def verify_features(page):
    unique_user = f"badgeuser_{int(time.time())}"

    # 1. Register
    page.goto("http://localhost:5001/register")
    page.fill("input[name='username']", unique_user)
    page.fill("input[name='email']", f"{unique_user}@example.com")
    page.fill("input[name='password']", "Password123!")
    page.fill("input[name='confirm_password']", "Password123!")
    page.select_option("select[name='security_question']", "What was the name of your first pet?")
    page.fill("input[name='security_answer']", "Fluffy")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard")

    # 2. Post Entry (Should award First Prayer badge)
    page.fill("textarea[name='content']", "Testing badges and stickers")
    page.click("button:has-text('Add Entry')")

    # Check flash message for badge
    # "Prayer entry added. You earned new badges: First Prayer!"
    if page.locator("div.alert:has-text('First Prayer')").count() > 0:
        print("Badge earned notification found.")
    else:
        print("Warning: Badge earned notification not found.")

    # Check Dashboard for Badge
    if page.locator("span.badge:has-text('First Prayer')").count() > 0:
        print("Badge found on dashboard.")
    else:
        print("Error: Badge not found on dashboard.")

    # 3. Add Sticker
    # Find the entry card (first one)
    # Click sticker button (e.g. Heart)
    page.click("button[name='sticker'][value='❤️']")

    # Verify sticker count appears
    if page.locator("span.badge:has-text('❤️ 1')").count() > 0:
        print("Sticker added successfully.")
    else:
        print("Error: Sticker not found.")

    # 4. Check Public Profile
    page.goto(f"http://localhost:5001/u/{unique_user}")
    if page.locator("span.badge:has-text('First Prayer')").count() > 0:
        print("Badge found on public profile.")
    else:
        print("Error: Badge not found on public profile.")

    page.screenshot(path="verification/badges_stickers.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify_features(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()
