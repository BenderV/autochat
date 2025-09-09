#!/usr/bin/env python3
"""
Minimalist test script to test the PlaywrightNavigator screenshot functionality with AI analysis
Uses the Playwright async API to avoid calling sync_playwright inside an active event loop.
"""

from io import BytesIO
from PIL import Image
from autochat import Autochat, Message, MessagePart
from typing import Optional
from playwright.async_api import Browser, Page, async_playwright
from base64 import b64encode
import asyncio
from concurrent.futures import ThreadPoolExecutor


def run_agent_conversation(navigator):
    """Run the agent conversation in a separate thread to avoid event loop conflicts"""
    agent = Autochat(
        name="Screenshot-Analyzer",
        instruction="""When given a screenshot of a webpage, describe the website purpose and
        analyze it and provide insights about the colors used, the photo quality,
        the layout structure, and overall design aesthetics.  Describe main CTA buttons and their text/colors.
        
        Use the navigate and scroll tool. Scroll to bottom of page. Iterate until you have a good understanding of the page.""",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    )

    agent.add_tool(navigator)

    initial_msg = Message(role="user", content="Go to https://shopaction.myriade.ai/")

    for msg in agent.run_conversation(initial_msg):
        print(msg.to_markdown())


async def test_screenshot_functionality():
    """Test the __llm__ method with screenshot capture and AI analysis"""

    print("🔧 Initializing PlaywrightNavigator...")

    class PlaywrightNavigator(Autochat):
        """Simple navigation and interaction tool (async)"""

        name = "navigator"
        description = (
            "Navigate to URLs, take screenshots and analyze colors, layout and design"
        )

        def __init__(
            self,
            site_name: Optional[str] = None,
        ):
            self.browser: Optional[Browser] = None
            self.page: Optional[Page] = None
            self.captured_events = []
            self.screenshots = []  # store raw image bytes (jpeg)
            self.site_name = site_name
            self.report_folder: Optional[str] = None
            self.screenshots_folder: Optional[str] = None
            self._playwright = None  # Store Playwright context to keep it alive

        async def __llm__(self):
            """Show current state with integrated analysis using last captured screenshot"""
            if not self.page:
                return "Browser Status: No page loaded. Use navigate() to start."

            if not self.screenshots:
                return "Browser Status: No screenshots captured yet. Use navigate() to start."

            screenshot_taken = await self.page.screenshot(type="jpeg", quality=75)
            screenshot = Image.open(BytesIO(screenshot_taken))
            print(
                f"DEBUG: Screenshot size - width: {screenshot.width}, height: {screenshot.height}"
            )
            # Logs screen file size for debugging
            buffered = BytesIO()
            screenshot.save(buffered, format="jpeg")
            img_str = b64encode(buffered.getvalue()).decode()
            print(f"DEBUG: Screenshot file size - {len(img_str)} bytes")

            messages = [
                MessagePart(type="image", image=screenshot),
                MessagePart(
                    type="text",
                    content=f"Browser Status: GOOD",
                ),
            ]

            return messages

        async def navigate(self, url: str):
            """Navigate to a URL using the async Playwright API"""
            if not self._playwright:
                self._playwright = await async_playwright().start()
                # Use webkit for parity with original code, change as needed
                self.browser = await self._playwright.webkit.launch(headless=False)
                self.page = await self.browser.new_page()

            if self.page:
                await self.page.goto(url)
                # wait for network to be idle similar to real navigator
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    # continue even if waiting fails
                    pass

        async def scroll(self, direction: str = "down", distance: int = 1000):
            """Scroll the page and capture a new screenshot"""
            if not self.page:
                return
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {distance})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{distance})")
            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=75)
            self.screenshots.append(screenshot_bytes)

        # Helper methods retained if needed for the above
        def _escape_attr_value(self, value: str) -> str:
            """Escape attribute value for safe use in CSS selectors"""
            return value.replace('"', '\\"').replace("'", "\\'")

        def _make_locator(
            self,
            *,
            selector: Optional[str] = None,
            data_testid: Optional[str] = None,
            role: Optional[str] = None,
            name: Optional[str] = None,
            text: Optional[str] = None,
            exact: bool = False,
            aria_label: Optional[str] = None,
            element_id: Optional[str] = None,
        ):
            """Create a locator using the best available strategy"""
            if not self.page:
                return None

            # Prefer stable selectors first
            if selector:
                return self.page.locator(selector)

            if data_testid:
                return self.page.get_by_test_id(data_testid)

            if element_id:
                return self.page.locator(f"#{element_id}")

            if aria_label:
                return self.page.get_by_label(aria_label)

            if role and name:
                return self.page.get_by_role(role, name=name, exact=exact)  # pyright: ignore[reportArgumentType]

            if role and text:
                return self.page.get_by_role(role, name=text, exact=exact)  # pyright: ignore[reportArgumentType]

        async def cleanup(self):
            """Cleanup browser and playwright context"""
            try:
                if self.browser:
                    await self.browser.close()
                if self._playwright:
                    await self._playwright.stop()
            except Exception:
                pass

    navigator = PlaywrightNavigator()

    print("🤖 Initializing AI agent for image analysis...")

    try:
        # Run agent conversation in a separate thread to avoid event loop conflicts
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_agent_conversation, navigator)
            future.result()  # Wait for completion

    except Exception as e:
        print(f"❌ Error during agent conversation: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("🧹 Cleaning up...")
        try:
            await navigator.cleanup()
        except Exception:
            pass
        print("✅ Test completed!")


def main():
    """Main entry point"""
    asyncio.run(test_screenshot_functionality())


if __name__ == "__main__":
    main()
