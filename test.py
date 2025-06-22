from selenium_driverless import webdriver
import asyncio


async def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-features=DisableLoadExtensionCommandLineSwitch")

    async with webdriver.Chrome(options=options) as driver:
        context_1 = driver.current_context
        context_2 = await driver.new_context()
        
        await context_1.current_target.get("https://google.com")
        await asyncio.sleep(3)
        await context_2.get("https://github.com")
        await asyncio.sleep(5)


asyncio.run(main())
