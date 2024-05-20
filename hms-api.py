from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from re import match
import psycopg2
import logging

app = Flask(__name__)

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = 'aY21z'  # Chave secreta forte e segura
jwt = JWTManager(app)

# Lista de códigos de 'status'
StatusCodes = {
    'success': 200,
    'error: bad request (request error)': 400,
    'error: internal server error (API error)': 500
}


##########################################################
# DATABASE ACCESS
##########################################################
def db_connection():
    db = psycopg2.connect(
        user='postgres',
        password='postgres',
        host='127.0.0.1',
        port='5432',
        database='HMS'
    )
    return db


##########################################################
# START ENDPOINT
##########################################################

@app.route('/dbproj')
def landing_page():
    return """
    Welcome to the Hospital Management System!  <br/>
    <br/>
    BD 2023-2024 Project<br/>
    <br/>
    """


##########################################################
# LOGIN
##########################################################
@app.route('/dbproj/user', methods=['PUT'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    # Conectar ao banco de dados
    db = db_connection()
    cur = db.cursor()
    cur.execute('SELECT password FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
    user = cur.fetchone()
    cur.close()
    db.close()

    if user and check_password_hash(user[0], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


##########################################################
# ADD USER
##########################################################
@app.route('/dbproj/add/user', methods=['POST'])
def add_user():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    name = request.json.get('name', None)
    mobile_number = request.json.get('mobile_number', None)
    birth_date = request.json.get('birth_date', None)
    address = request.json.get('address', None)
    email = request.json.get('email', None)

    # Verificar se há campos vazios
    if not username or not password or not name or not mobile_number or not birth_date or not address or not email:
        return jsonify({"msg": "Missing required fields"}), 400

    # Verificar se o nome contém números
    if any(char.isdigit() for char in name):
        return jsonify({"msg": "Name should not contain numbers"}), 400

    # Verificar formato da data
    try:
        datetime.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"msg": "Incorrect date format, should be YYYY-MM-DD"}), 400

    # Verificar se o número de telemóvel contém exatamente 9 dígitos e apenas dígitos
    if not match(r'^\d{9}$', mobile_number):
        return jsonify({"msg": "Mobile number must contain exactly 9 digits and only digits"}), 400

    db = db_connection()
    cur = db.cursor()

    # Verificar unicidade de 'username', 'mobile_number' e 'email'
    cur.execute('SELECT username FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
    if cur.fetchone():
        return jsonify({"msg": "Username already exists"}), 400

    cur.execute('SELECT mobile_number FROM person WHERE mobile_number = %s', (mobile_number,))
    if cur.fetchone():
        return jsonify({"msg": "Mobile number already exists"}), 400

    cur.execute('SELECT email FROM person WHERE email = %s', (email,))
    if cur.fetchone():
        return jsonify({"msg": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)

    try:
        cur.execute('''
                INSERT INTO person (username, password, name, mobile_number, birth_date, address, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (username, hashed_password, name, mobile_number, birth_date, address, email))
        db.commit()
        return jsonify({"msg": "User added successfully"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# EXEMPLO DE ENDPOINT PROTEGIDO
##########################################################
@app.route('/dbproj/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


##########################################################
# SCHEDULE APPOINTMENT
##########################################################
@app.route('/dbproj/appointments', methods=['POST'])
def schedule_appointment():
    db = db_connection()
    cursor = db.cursor()
    # Logic to insert a new appointment in the database
    # ...
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success", "message": "Appointment scheduled"}), 200


# Make all endpoints
# ...


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: https://{host}:{port}')
