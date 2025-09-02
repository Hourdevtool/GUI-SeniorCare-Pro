import asyncio
from playwright.async_api import async_playwright
import tempfile
import os

heartpdf_file = os.path.join(tempfile.gettempdir(), "heart_report.pdf")
historypdf_file = os.path.join(tempfile.gettempdir(), "history_report.pdf")
async def generateheart_pdf(id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()


        await page.goto(f"http://medic.ctnphrae.com/heart_report.php?id={id}", wait_until="load", timeout=60000)


        await page.goto(f"http://medic.ctnphrae.com/heart_report_print.php?id={id}", wait_until="networkidle")


        await page.pdf(path=heartpdf_file, format="A4")
        await browser.close()

        if os.name == "nt":
            os.startfile(heartpdf_file)
        print(f"PDF สร้างเสร็จแล้ว: {heartpdf_file}")


async def generahistory_pdf(id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # รอบแรก: เข้าหน้า history.php
        await page.goto(f"http://medic.ctnphrae.com/history.php?id={id}", wait_until="load", timeout=60000)

        # รอบสอง: เข้าหน้า history(print).php
        await page.goto(f"http://medic.ctnphrae.com/history(print).php?id={id}", wait_until="networkidle")

        # สร้าง PDF ของหน้า history(print)
        await page.pdf(path=historypdf_file, format="A4")
        await browser.close()

        if os.name == "nt":
            os.startfile(historypdf_file)
        print(f"PDF สร้างเสร็จแล้ว: {historypdf_file}")
def generate_pdf_sync(id,adivces=None):

    if not adivces:
        asyncio.run(generahistory_pdf(id))
    else:
        asyncio.run(generateheart_pdf(id))


