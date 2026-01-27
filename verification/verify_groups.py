from playwright.sync_api import sync_playwright
import time

def verify_groups(page, browser):
    # Create two users
    ts = int(time.time())
    u1 = f"creator_{ts}"
    u2 = f"joiner_{ts}"

    print(f"Testing with Users: {u1}, {u2}")

    # 1. Register User 1
    page.goto("http://localhost:5001/register")
    page.fill("input[name='username']", u1)
    page.fill("input[name='email']", f"{u1}@example.com")
    page.fill("input[name='password']", "Password123!")
    page.fill("input[name='confirm_password']", "Password123!")
    page.select_option("select[name='security_question']", "What was the name of your first pet?")
    page.fill("input[name='security_answer']", "Fluffy")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard")

    # 2. Create Group
    page.goto("http://localhost:5001/groups/")
    page.fill("input[name='name']", f"Group {ts}")
    page.fill("input[name='description']", "Test Description")
    page.fill("input[name='purpose']", "Test Purpose")
    page.click("button:has-text('Create')")

    # 3. View Group (User 1)
    # Click "Enter" button for the new group
    # Locate the card by text, then the enter button
    page.locator(f".card:has-text('Group {ts}') >> text=Enter").click()
    page.wait_for_url(r"**/groups/\d+")

    print("Entered group detail page.")

    # Should see "Group Admins" and u1
    if page.locator("div.card-header:has-text('Group Admins')").count() > 0:
        print("Admins section found.")
    else:
        print("Error: Admins section missing.")

    if page.locator("div.alert:has-text('Purpose')").count() > 0:
        print("Purpose found.")
    else:
        print("Error: Purpose missing.")

    # Check Chat disabled (members=1)
    if page.locator("text=Chat will be enabled once more members join").count() > 0:
        print("Chat restriction message found.")
    else:
        print("Error: Chat restriction message missing.")

    page.click("text=Logout")

    # 4. Register User 2
    page.goto("http://localhost:5001/register")
    page.fill("input[name='username']", u2)
    page.fill("input[name='email']", f"{u2}@example.com")
    page.fill("input[name='password']", "Password123!")
    page.fill("input[name='confirm_password']", "Password123!")
    page.select_option("select[name='security_question']", "What was the name of your first pet?")
    page.fill("input[name='security_answer']", "Fluffy")
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard")

    # 5. Join Group
    page.goto("http://localhost:5001/groups/")
    page.locator(f".card:has-text('Group {ts}') >> text=Join Group").click()

    # 6. View Group (User 2)
    page.locator(f".card:has-text('Group {ts}') >> text=Enter").click()
    page.wait_for_url(r"**/groups/\d+")

    # Check Members list > 1
    # Check Chat enabled
    if page.locator("text=Group Chat").count() > 0:
        print("Chat enabled for 2 members.")
    else:
        print("Error: Chat missing for 2 members.")

    # Check Admins list (should contain u1)
    if page.locator(f"text={u1}").count() > 0:
        print(f"Admin {u1} visible.")

    # Check Members list (should contain u2)
    if page.locator(f"text={u2}").count() > 0:
        print(f"Member {u2} visible.")

    print("Verification script finished.")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify_groups(page, browser)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/group_error.png")
        finally:
            browser.close()
