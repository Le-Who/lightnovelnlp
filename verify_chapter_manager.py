from playwright.sync_api import sync_playwright, expect

def test_chapter_manager_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock API calls
        page.route("**/api/projects/123", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"id": 123, "name": "Test Project", "genre": "fantasy", "created_at": "2024-01-01T00:00:00Z"}'
        ))

        page.route("**/api/projects/123/chapters**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[]'
        ))

        # Navigate
        page.goto("http://localhost:3000/projects/123")

        # Wait for page to load
        page.wait_for_selector("text=Test Project")

        # Click NEW_FILE button
        page.click("text=NEW_FILE")

        # Wait for modal
        page.wait_for_selector("role=dialog")

        # Take screenshot of open modal
        page.screenshot(path="verification_modal_open.png")
        print("Screenshot verification_modal_open.png saved.")

        # Verify close button exists
        close_button = page.locator("button[aria-label='Close modal']")
        expect(close_button).to_be_visible()

        # Verify inputs have labels associated via for/id
        expect(page.locator("label[for='chapter-title']")).to_be_visible()
        expect(page.locator("input#chapter-title")).to_be_visible()

        expect(page.locator("label[for='chapter-content']")).to_be_visible()
        expect(page.locator("textarea#chapter-content")).to_be_visible()

        # Test close button
        close_button.click()
        expect(page.locator("role=dialog")).not_to_be_visible()
        print("Close button works.")

        # Test Escape key
        page.click("text=NEW_FILE")
        page.wait_for_selector("role=dialog")
        page.keyboard.press("Escape")
        expect(page.locator("role=dialog")).not_to_be_visible()
        print("Escape key works.")

        browser.close()

if __name__ == "__main__":
    test_chapter_manager_modal()
