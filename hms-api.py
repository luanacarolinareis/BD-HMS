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
# CHECK COMMON USER DATA
##########################################################
def validate_user_data(username, email, password, name, mobile_number, birth_date, address):
    if not username or not email or not password or not name or not mobile_number or not birth_date or not address:
        return "All fields are required"

    if not match(r'^[a-zA-Z0-9]+$', username):
        return "Username must contain only letters and numbers"

    if any(char.isdigit() for char in name):
        return "Name must not contain numbers"

    if not match(r'^\d{9}$', str(mobile_number)):
        return "Mobile number must contain exactly 9 digits"

    try:
        datetime.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        return "Incorrect date format, should be YYYY-MM-DD"

    if not match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return "Invalid email format"

    return None


##########################################################
# CHECK EMPLOYEE CONTRACT DATA
##########################################################
def validate_contract_data(salary, start_date, end_date):
    if not str(salary).isdigit():
        return "Salary must contain only digits"

    try:
        datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        return "Incorrect date format, should be YYYY-MM-DD"

    if end_date is not None:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return "Incorrect date format, should be YYYY-MM-DD"

    return None


##########################################################
# ADD COMMON USER DATA
##########################################################
def add_common_user_data(common_data):
    username = common_data.get('username', None)
    password = common_data.get('password', None)
    name = common_data.get('name', None)
    mobile_number = common_data.get('mobile_number', None)
    birth_date = common_data.get('birth_date', None)
    address = common_data.get('address', None)
    email = common_data.get('email', None)

    validation_error = validate_user_data(username, email, password, name, mobile_number, birth_date, address)
    if validation_error:
        return {"msg": validation_error}, 400

    db = db_connection()
    cur = db.cursor()

    # Verificar unicidade de 'username', 'mobile_number' e 'email'
    cur.execute('SELECT username FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
    if cur.fetchone():
        return {"msg": "Username already exists"}, 400

    cur.execute('SELECT mobile_number FROM person WHERE mobile_number = %s', (mobile_number,))
    if cur.fetchone():
        return {"msg": "Mobile number already exists"}, 400

    cur.execute('SELECT email FROM person WHERE email = %s', (email,))
    if cur.fetchone():
        return {"msg": "Email already exists"}, 400

    hashed_password = generate_password_hash(password)

    try:
        cur.execute('''
            INSERT INTO person (username, password, name, mobile_number, birth_date, address, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (username, hashed_password, name, mobile_number, birth_date, address, email))
        db.commit()
        return {"msg": "User added successfully", "username": username}, 201
    except Exception as e:
        db.rollback()
        return {"msg": str(e)}, 500
    finally:
        cur.close()
        db.close()


##########################################################
# ADD EMPLOYEE CONTRACT DATA
##########################################################
def add_employee_contract_data(username, contract_data):
    salary = contract_data.get('salary')
    start_date = contract_data.get('start_date')
    duration = contract_data.get('duration')
    end_date = contract_data.get('end_date')

    validation_result = validate_contract_data(salary, start_date, end_date)
    if validation_result:
        return False, validation_result

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
                INSERT INTO employee_contract (contract_salary, contract_start_date, 
                contract_duration, contract_end_date, person_username)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (salary, start_date, duration, end_date, username))
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        cur.close()
        db.close()


##########################################################
# REMOVER COMMON DATA IF CONTRACT DATA HAS ERRORS
##########################################################
def contract_check(username, contract_data):
    success, error = add_employee_contract_data(username, contract_data)

    # Remover o 'user' da tabela 'person' se a inserção do contrato falhar
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('DELETE FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()
    return jsonify({"msg": error}), 500


##########################################################
# ADD PATIENT
##########################################################
@app.route('/dbproj/register/patient', methods=['POST'])
def register_patient():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()
    response, status = add_common_user_data(data)
    if status != 201:
        return jsonify(response), status

    username = response["username"]

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO patient (person_username)
            VALUES (%s)
        ''', (username,))
        db.commit()
        return jsonify({"msg": "Patient added successfully", "username": username}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# ADD ASSISTANT
##########################################################
@app.route('/dbproj/register/assistant', methods=['POST'])
def register_assistant():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()

    # Adicionar os dados comuns do user
    response, status = add_common_user_data(data)
    if status != 201:
        return jsonify(response), status

    username = response["username"]

    # Adicionar os dados do contrato do assistente
    contract_data = data.get('contract', {})
    contract_check(username, contract_data)

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO assistants (employee_contract_person_username)
            VALUES (%s)
        ''', (username,))
        db.commit()
        return jsonify({"msg": "Assistant added successfully", "username": username}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# ADD NURSE
##########################################################
@app.route('/dbproj/register/nurse', methods=['POST'])
def register_nurse():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()

    # Adicionar os dados comuns do user
    response, status = add_common_user_data(data)
    if status != 201:
        return jsonify(response), status
    username = response["username"]

    # Adicionar os dados do enfermeiro
    position = data.get('position', None)
    if not position:
        return jsonify({"msg": "Missing required field: position"}), 400

    # Adicionar os dados do contrato do enfermeiro
    contract_data = data.get('contract', {})
    contract_check(username, contract_data)

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO nurses (position, employee_contract_person_username)
            VALUES (%s, %s)
        ''', (position, username))
        db.commit()
        return jsonify({"msg": "Nurse added successfully", "username": username}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# ADD DOCTOR
##########################################################
@app.route('/dbproj/register/doctor', methods=['POST'])
def register_doctor():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()

    # Adicionar os dados comuns do user
    response, status = add_common_user_data(data)
    if status != 201:
        return jsonify(response), status
    username = response["username"]

    # Adicionar os dados do médico
    doctor_license = data.get('license_info', None)
    if not doctor_license:
        return jsonify({"msg": "Missing required field: position"}), 400

    specializations = data.get('specializations_ids', [])
    if not specializations:
        return jsonify({"msg": "At least one specialization must be specified"}), 400
    for specialization_id in specializations:
        if not str(specialization_id).isdigit():
            return jsonify({"msg": "Specialization ID must contain only digits"}), 400

    # Adicionar os dados do contrato do médico
    contract_data = data.get('contract', {})
    contract_check(username, contract_data)

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO doctors (doctor_license, employee_contract_person_username)
            VALUES (%s, %s)
        ''', (doctor_license, username))

        for specialization_id in specializations:
            cur.execute('''
                INSERT INTO specializations_doctors (specializations_specialization_id,
                doctors_employee_contract_person_username)
                VALUES (%s, %s)
            ''', (specialization_id, username))

        db.commit()
        return jsonify({"msg": "Doctor added successfully", "username": username}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500
    finally:
        cur.close()
        db.close()


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

    # Verificar se o user existe e se a password está correta
    if user and check_password_hash(user[0], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401


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
