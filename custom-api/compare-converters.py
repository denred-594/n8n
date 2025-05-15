import os
import asyncio
from jinja2 import Environment, FileSystemLoader
import pyppeteer

# Pfade
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = "pCon-planner-angebot.html"
OUTPUT_DIR = "output"

# Testdaten
data = {
    "name": "Max",
    "nachname": "Mustermann",
    "firma": "Muster GmbH",
    "email": "max@example.com",
    "straße": "Musterstraße 1",
    "stadt": "Musterstadt",
    "anrede": "Herr",
    "datum": "2025-05-14",
    "gültigbisdatum": "2025-06-14"
}

# Jinja2 Template-Rendering
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template(TEMPLATE_FILE)
html_content = template.render(**data)

# Output-Verzeichnis
os.makedirs(OUTPUT_DIR, exist_ok=True)

# PDF-Erstellung mit Pyppeteer
async def convert_with_pyppeteer(html, output_path):
    try:
        browser = await pyppeteer.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.newPage()
        await page.setContent(html)
        await page.waitForSelector("body")  # Optional: wartet bis Body da ist
        await asyncio.sleep(1)  # Kurze Pause für Netzwerkelemente

        await page.pdf({
            "path": output_path,
            "format": "A4",
            "printBackground": True,
            "margin": {
                "top": "20mm",
                "bottom": "20mm",
                "left": "20mm",
                "right": "20mm"
            }
        })
        print(f"PDF erfolgreich erstellt unter: {output_path}")
    except Exception as e:
        print(f"Fehler bei PDF-Erstellung mit Pyppeteer: {e}")
    finally:
        if 'browser' in locals():
            await browser.close()

# Hauptfunktion
if __name__ == "__main__":
    output_pdf = os.path.join(OUTPUT_DIR, "angebot_pyppeteer.pdf")
    asyncio.run(convert_with_pyppeteer(html_content, output_pdf))
