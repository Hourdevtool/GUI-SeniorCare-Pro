import asyncio
from playwright.async_api import async_playwright
import tempfile
import os
import subprocess

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

        open_or_print(heartpdf_file, print_file=True)  # เลือกว่าจะเปิดหรือพิมพ์
        print(f"PDF สร้างเสร็จแล้ว: {heartpdf_file}")


async def generahistory_pdf(id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(f"http://medic.ctnphrae.com/history.php?id={id}", wait_until="load", timeout=60000)
        await page.goto(f"http://medic.ctnphrae.com/history(print).php?id={id}", wait_until="networkidle")

        await page.pdf(path=historypdf_file, format="A4")
        await browser.close()

        open_or_print(historypdf_file, print_file=True)
        print(f"PDF สร้างเสร็จแล้ว: {historypdf_file}")


def open_or_print(filepath, print_file=False):
    if os.name == "nt":  # Windows
         os.startfile(filepath) 
    else:  # Linux / Debian
         try:
            if print_file:
                subprocess.run(["lp", filepath])   # สั่งพิมพ์ไฟล์
            else:
                subprocess.run(["xdg-open", filepath])  # เปิดไฟล์
         except Exception as e:
            print(f"ไม่สามารถเปิด/พิมพ์ไฟล์ได้: {e}")


def generate_pdf_sync(id, advices=None):
    if not advices:
        asyncio.run(generahistory_pdf(id))
    else:
        asyncio.run(generateheart_pdf(id))
