import asyncio
from playwright.async_api import async_playwright

async def test_launch():
    print("Attempting to launch browser...")
    try:
        async with async_playwright() as p:
            # Spróbuj uruchomić przeglądarkę w trybie headless (często bardziej stabilny)
            browser = await p.chromium.launch(headless=True)
            print("Browser launched successfully.")
            page = await browser.new_page()
            print("New page created successfully.")
            print("Closing browser...")
            await browser.close()
            print("Browser closed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_launch())


QUERIES = {
    "blonde": "woman with blonde hair",
    "brunette": "woman with brown hair",
    "black": "woman with black hair",
    "redhead": "woman with red hair",
    "asian_people": "asian people",
    "black_people": "black people",
    "white_people": "white people"
}