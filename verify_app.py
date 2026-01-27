from playwright.sync_api import sync_playwright
import time
import random

def verify(page):
    suffix = str(random.randint(10000, 99999))
    username = f"user_{suffix}"
    email = f"user_{suffix}@test.com"
    password = "Password123!"

    print(f"Registering User 1: {username}...")
    page.goto("http://localhost:5001/register")
    page.fill('input[name="username"]', username)
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.fill('input[name="confirm_password"]', password)

    # Try filling security question (assuming input type text based on previous analysis)
    # If it's a select, this might fail, so we wrap in try/except logic or check.
    # Looking at auth_routes.py, it reads from request.form.get('security_question').
    # Usually consistent with <input name="security_question">.
    try:
        page.fill('input[name="security_question"]', 'Pet?')
    except:
        # Maybe select?
        try:
             page.select_option('select[name="security_question"]', index=1)
        except:
             print("Could not fill security_question")
             pass

    page.fill('input[name="security_answer"]', 'Dog')

    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print(f"After register, URL: {page.url}")

    # Login User 1
    if "/dashboard" not in page.url:
        if "login" in page.url:
             print("Redirected to login. Logging in...")
             page.fill('input[name="username"]', username)
             page.fill('input[name="password"]', password)
             page.click('button[type="submit"]')
             page.wait_for_load_state('networkidle')
        elif "register" in page.url:
             print("Still on register page. Registration failed?")
             page.screenshot(path="verification_register_fail.png")
             try:
                 print(page.inner_text('.alert'))
             except:
                 pass
             return

    # 3. Create Entries for Heatmap
    print("Navigating to dashboard...")
    page.goto("http://localhost:5001/dashboard")

    print("Creating entry...")
    if page.is_visible('textarea[name="content"]'):
        page.fill('textarea[name="content"]', 'Prayer for today')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
    else:
        print("Content textarea not found! validation failed.")

    # Screenshot Dashboard
    page.screenshot(path="verification_dashboard.png")

    # 4. Register User 2 for Chat
    print("Registering User 2...")
    page.goto("http://localhost:5001/logout")

    suffix2 = str(random.randint(10000, 99999))
    username2 = f"user_{suffix2}"
    email2 = f"user_{suffix2}@test.com"

    page.goto("http://localhost:5001/register")
    page.fill('input[name="username"]', username2)
    page.fill('input[name="email"]', email2)
    page.fill('input[name="password"]', password)
    page.fill('input[name="confirm_password"]', password)

    try:
        page.fill('input[name="security_question"]', 'Pet?')
    except:
        try:
             page.select_option('select[name="security_question"]', index=1)
        except:
             pass
    page.fill('input[name="security_answer"]', 'Dog')

    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print(f"After register 2, URL: {page.url}")

    if "/dashboard" not in page.url:
        page.goto("http://localhost:5001/login")
        page.fill('input[name="username"]', username2)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

    # Message User 1
    print(f"Messaging User 1 ({username})...")
    page.goto(f"http://localhost:5001/u/{username}")

    # Click Message button
    try:
        # Expect navigation to conversation page
        with page.expect_navigation():
            try:
                page.click('text=Send Message')
            except:
                print("Send Message button not found by text, trying selector")
                page.click('a[href*="/messages/conversation/"]')
    except Exception as e:
        print(f"Navigation failed or timeout: {e}")

    # Verify we are on the conversation page
    print(f"Current URL: {page.url}")
    if "/messages/conversation/" not in page.url:
        print("Failed to navigate to conversation page.")
        # Try direct navigation if possible?
        # Maybe button failed.
        # But let's proceed to try wait.

    # Chat UI verification
    print("Verifying Chat UI...")
    try:
        page.wait_for_selector('#gifModal', state='attached', timeout=5000)
    except:
        print("GIF Modal not found in DOM.")
        page.screenshot(path="verification_chat_fail.png")
        # Dump page content to debug
        # print(page.content())
        raise

    page.screenshot(path="verification_chat_ui.png")

    # Open GIF Modal
    print("Opening GIF Modal...")
    page.click('button[data-bs-target="#gifModal"]')
    # Wait for modal visibility
    page.wait_for_selector('#gifModal.show')
    page.screenshot(path="verification_gif_modal.png")

    # Click GIF
    print("Selecting GIF...")
    page.click('#gifContainer img:first-child')

    # Send
    print("Sending message...")
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    # Verify Render
    print("Verifying render...")
    # Wait for any img in .card-body that is not the avatar?
    # Avatar has class rounded-circle
    # GIF has class img-fluid (added by my filter)
    page.wait_for_selector('.card-body img.img-fluid')
    page.screenshot(path="verification_chat_rendered.png")
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
