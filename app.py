import sqlite3
from flask import Flask, render_template, request, jsonify, g
from datetime import datetime

app = Flask(__name__)
DATABASE = 'database.db'

# --- DATABASE FORBINDELSE ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- INITIALISERING AF TABELLER ---
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Opret Borger tabel (Rettet stavefejl her: EXISTS)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS borger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                navn TEXT NOT NULL,
                adresse TEXT NOT NULL
            )
        ''')
        
        # Opret Maaling tabel
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maaling (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puls INTEGER NOT NULL,
                fald_registreret BOOLEAN NOT NULL,
                tidspunkt TEXT NOT NULL,
                borger_id INTEGER NOT NULL,
                FOREIGN KEY (borger_id) REFERENCES borger (id)
            )
        ''')
        
        # Opret test-borger hvis tabellen er tom
        cursor.execute('SELECT count(*) FROM borger')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO borger (navn, adresse) VALUES (?, ?)', 
                           ("Jens Hansen", "Omsorgsvej 1, Frederikssund"))
            db.commit()
            print("Database initialiseret med test-borger.")
        
        db.commit()

# Kør initialisering
init_db()

# --- RUTER (Sider og API) ---

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    
    # [cite_start]Hent alle borgere [cite: 55]
    cursor.execute('SELECT * FROM borger')
    borgere_db = cursor.fetchall()
    
    data_view = []
    for b in borgere_db:
        # Hent seneste måling
        cursor.execute('SELECT * FROM maaling WHERE borger_id = ? ORDER BY tidspunkt DESC LIMIT 1', (b['id'],))
        seneste = cursor.fetchone()
        
        status = "Normal"
        puls_visning = "Ingen data"
        fald_visning = "Nej"
        tid_visning = "-"
        
        if seneste:
            puls_visning = seneste['puls']
            fald_visning = "JA" if seneste['fald_registreret'] else "Nej"
            tid_visning = seneste['tidspunkt']
            
            # [cite_start]Logik fra projektbeskrivelse [cite: 56]
            if seneste['fald_registreret']:
                status = "KRITISK: FALD!"
            elif seneste['puls'] < 40 or seneste['puls'] > 130:
                status = "ADVARSEL: Uregelmæssig puls"
        
        data_view.append({
            "navn": b['navn'],
            "adresse": b['adresse'],
            "puls": puls_visning,
            "fald": fald_visning,
            "status": status,
            "tid": tid_visning
        })

    return render_template('dashboard.html', borgere=data_view)

@app.route('/api/data', methods=['POST'])
def modtag_data():
    data = request.json
    if not data: return jsonify({"error": "Ingen data"}), 400

    borger_id = data.get('borger_id')
    puls = data.get('puls')
    fald = 1 if data.get('fald') else 0
    nu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    try:
        # Rettet SQL syntax og stavefejl herunder
        db.execute('INSERT INTO maaling (puls, fald_registreret, tidspunkt, borger_id) VALUES (?, ?, ?, ?)', 
                   (puls, fald, nu, borger_id))
        db.commit()
        return jsonify({"message": "Gemt"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/opret', methods=['GET', 'POST'])
def opret_borger():
    if request.method == 'POST':
        navn = request.form['navn']
        adresse = request.form['adresse']

        db = get_db()
        db.execute('INSERT INTO borger (navn, adresse) VALUES (?,?)', (navn, adresse))
        db.commit()
        return render_template('opret_borger.html', besked="Borger oprettet!")
    
    return render_template('opret_borger.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

