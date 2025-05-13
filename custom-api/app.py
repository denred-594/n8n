from flask import Flask, request, jsonify, send_file
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import tempfile

app = Flask(__name__)

# Jinja2-Umgebung initialisieren
env = Environment(loader=FileSystemLoader('templates'))

@app.route('/api', methods=['POST'])
def api_endpoint():
    try:
        # JSON-Daten aus der Anfrage holen
        data = request.get_json()
        if not data:
            return jsonify({"message": "Keine Daten empfangen"}), 400

        # Template laden
        template = env.get_template('pCon-planner-angebot.html')

        # Daten für das Template vorbereiten
        template_data = {
            'contact_name': data.get('contact_name', 'Niklas Wille'),
            'contact_phone': data.get('contact_phone', '017621462491'),
            'contact_email': data.get('contact_email', '[email protected]'),
            'contact_office': data.get('contact_office', 'Pforzheim'),
            'offer_date': data.get('offer_date', '02.05.2025'),
            'offer_valid_until': data.get('offer_valid_until', '29.08.2025'),
            'offer_number': data.get('offer_number', '201556'),
            'recipient_name': data.get('recipient_name', '-'),
            'items': data.get('items', [{
                'position': 1,
                'description': 'pCon.planner PRO (named user license)<br>Preis pro Monat: 39,00 €<br>Laufzeit: 24 Monate ab Rechnungsstellung<br>Verlängerung: Automatisch um 12 Monate, sofern keine Kündigung eingegangen ist.<br>Kündigungsfrist: 3 Monate<br>Abrechnung: Bei Anschaffung anteilig zum Kalenderjahr. Anschließend jährlich /Vorschüssig zum Januar eines Kalenderjahres.<br>*Die Named-User-Lizenz wird durch eine Cloud-Lizenz über pCon.login bereitgestellt.(www.login.pcon-solutions.com) Zur Nutzung der Software ist ein pCon.login-Konto und eine ordnungsgemäße Internetverbindung erforderlich.<br>Im monatlichen Mietpreis sind sämtliche Kosten für die Software sowie Wartung und Updates inbegriffen. Der technische Support ist ebenfalls im Betrag inkludiert.',
                'unit': 'Monat',
                'unit_price': 39.00,
                'total_price': 39.00
            }]),
            'subtotal': data.get('subtotal', 39.00),
            'vat_rate': data.get('vat_rate', 19.00),
            'vat_amount': data.get('vat_amount', 7.41),
            'total': data.get('total', 46.41)
        }

        # Template rendern
        rendered_html = template.render(**template_data)

        # Temporäres PDF erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            HTML(string=rendered_html).write_pdf(tmp_file.name)
            pdf_path = tmp_file.name

        # PDF als Response senden
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'angebot_{template_data["offer_number"]}.pdf'
        )

    except Exception as e:
        # Fehlerbehandlung
        return jsonify({"message": f"Fehler bei der Verarbeitung: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)