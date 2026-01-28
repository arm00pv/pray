from playwright.sync_api import sync_playwright
import time

def verify(page):
    # Admin Login
    page.goto("http://localhost:5001/admins/login")
    if "Login" in page.title():
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

    # Check Admin Dashboard Charts
    print("Checking Admin Dashboard Charts...")
    page.goto("http://localhost:5001/admins/dashboard")
    page.wait_for_selector('#userGrowthChart')
    page.wait_for_selector('#prayerActivityChart')
    page.screenshot(path="verification_admin_charts.png")

    # Check Community Leaderboard
    print("Checking Community Leaderboard...")
    page.goto("http://localhost:5001/community/")
    page.wait_for_text("Prayer Warriors")
    page.screenshot(path="verification_leaderboard.png")
    print("Verification complete.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        verify(page)
    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path="verification_error.png")
    finally:
        browser.close()
