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

        # Erforderliche Variablen prüfen
        required_fields = ['name', 'nachname', 'firma', 'email', 'straße', 'stadt', 'anrede', 'datum', 'gültigbisdatum']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"message": f"Fehlende Felder: {', '.join(missing_fields)}"}), 400

        # Daten für das Template vorbereiten
        template_data = {
            'name': str(data['name']),
            'nachname': str(data['nachname']),
            'firma': str(data['firma']),
            'email': str(data['email']),
            'straße': str(data['straße']),
            'stadt': str(data['stadt']),
            'anrede': str(data['anrede']),
            'datum': str(data['datum']),
            'gültigbisdatum': str(data['gültigbisdatum'])
        }

        # Template laden
        template = env.get_template('./templates/pCon-planner-angebot.html')

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
            download_name='angebot.pdf'
        )

    except Exception as e:
        # Fehlerbehandlung
        return jsonify({"message": f"Fehler bei der Verarbeitung: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)