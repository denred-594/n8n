from flask import Flask, request, jsonify, send_file
from jinja2 import Environment, FileSystemLoader
import pyppeteer
import asyncio
import uvloop
import os
import tempfile

uvloop.install()
app = Flask(__name__)

# Jinja2-Umgebung initialisieren
env = Environment(loader=FileSystemLoader('templates'),
    auto_reload=True,  # Add this line to auto-reload templates
    cache_size=0       # Disable template caching
)

# Pyppeteer PDF-Erstellung
async def convert_with_pyppeteer(html, output_path):
    try:
        browser = await pyppeteer.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        page = await browser.newPage()
        await page.setContent(html)
        await page.waitForSelector("body", timeout=10000)  # Warte auf Body
        await asyncio.sleep(1)  # Kurze Pause für Rendering
        await page.pdf({
            "path": output_path,
            "format": "A4",
            "width": "210mm",
            "height": "297mm",
            "printBackground": False,
            "displayHeaderFooter": False,
            "margin": {
                "top": "0mm",
                "bottom": "0mm",
                "left": "10mm",
                "right": "10mm"
            }
        })
        print(f"Pyppeteer: PDF erstellt unter {output_path}")
        return output_path
    except Exception as e:
        raise Exception(f"Fehler bei Pyppeteer: {str(e)}")
    finally:
        if 'browser' in locals():
            await browser.close()

@app.route('/api', methods=['POST'])
def api_endpoint():
    try:
        # JSON-Daten aus der Anfrage holen
        data = request.get_json()
        if not data:
            return jsonify({"message": "Keine Daten empfangen"}), 400

        # Erforderliche Variablen prüfen
        required_fields = ['name', 'nachname', 'firma', 'email', 'straße', 'stadt', 'anrede', 'datum', 'gültigbisdatum', 'offer_number', 'greeting']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"message": f"Fehlende Felder: {', '.join(missing_fields)}"}), 400

        # Daten für das Template vorbereiten
        template_data = {
            'name': str(data['name']),
            'nachname': str(data['nachname']),
            'firma': str(data['firma']),
            'email': str(data['email']),
            'strasse': str(data['straße']),
            'stadt': str(data['stadt']),
            'anrede': str(data['anrede']),
            'datum': str(data['datum']),
            'gueltigbisdatum': str(data['gültigbisdatum']),
            'offer_number': str(data['offer_number']),
	    'greeting': str(data['greeting'])
        }

        # Template laden und rendern
        template = env.get_template('pCon-planner-angebot.html')
        rendered_html = template.render(**template_data)

        # Temporäres PDF erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = asyncio.run(convert_with_pyppeteer(rendered_html, tmp_file.name))

        # PDF als Response senden
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='angebot.pdf'
        )

    except Exception as e:
        # Fehlerbehandlung
        return jsonify({"message": f"Fehler bei der Verarbeitung: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
