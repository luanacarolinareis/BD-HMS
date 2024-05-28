from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from re import match
import psycopg2
import logging

app = Flask(__name__)

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = 'aY21z'
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
    try:
        db = psycopg2.connect(
            user='postgres',
            password='postgres',
            host='127.0.0.1',
            port='5432',
            database='HMS'
        )
        return db
    except Exception as e:
        return {"msg": str(e)}, 500


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
# OTHER FUNCTIONS
##########################################################
def validate_username(username):
    if not match(r'^[a-zA-Z0-9]+$', username):
        return "Username must contain only letters and numbers"
    return None


def validate_name(name):
    if any(char.isdigit() for char in name):
        return "Name must not contain numbers"
    return None


def validate_mobile_number(mobile_number):
    if not match(r'^\d{9}$', str(mobile_number)):
        return "Mobile number must contain exactly 9 digits"
    return None


def validate_date_format(date):
    if date is not None:
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return None
        except ValueError:
            return "Incorrect date format, should be YYYY-MM-DD"


def validate_email(email):
    if not match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return "Invalid email format"
    return None


def validate_date_time_format(time):
    try:
        datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        return None
    except ValueError:
        return "Incorrect time format, should be YYYY-MM-DD HH:MM:SS"


def validate_salary(salary):
    if not str(salary).isdigit():
        return "Salary must contain only digits"
    return None


def validate_id(check_id):
    if not str(check_id).isdigit():
        return "ID must contain only digits"
    return None


##########################################################
# GET COMMON USER DATA
##########################################################
def get_common_user_data(common_data):
    # Obter nome de utilizador
    username = common_data.get('username', None)
    validation_error = validate_username(username)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter password
    password = common_data.get('password', None)

    # Obter nome
    name = common_data.get('name', None)
    validation_error = validate_name(name)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter número de telemóvel
    mobile_number = common_data.get('mobile_number', None)
    validation_error = validate_mobile_number(mobile_number)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter data de nascimento
    birth_date = common_data.get('birth_date', None)
    validation_error = validate_date_format(birth_date)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter morada
    address = common_data.get('address', None)

    # Obter email
    email = common_data.get('email', None)
    validation_error = validate_email(email)
    if validation_error:
        return {"msg": validation_error}, 400

    if not username or not password or not name or not mobile_number or not birth_date or not address or not email:
        return "All fields are required", 400

    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Verificar unicidade de 'username', 'mobile_number' e 'email'
    cur.execute('SELECT username FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
    result = cur.fetchone()
    if result is not None:
        return {"msg": "Username already exists"}, 400

    cur.execute('SELECT mobile_number FROM person WHERE mobile_number = %s', (mobile_number,))
    result = cur.fetchone()
    if result is not None:
        return {"msg": "Mobile number already exists"}, 400

    cur.execute('SELECT email FROM person WHERE email = %s', (email,))
    result = cur.fetchone()
    if result is not None:
        return {"msg": "Email already exists"}, 400

    add_common_data(username, password, name, mobile_number, birth_date, address, email)
    return username, 200


##########################################################
# GET EMPLOYEE CONTRACT DATA
##########################################################
def get_employee_contract_data(username, contract_data):
    # Obter salário
    salary = contract_data.get('salary')
    validation_error = validate_salary(salary)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter data de início
    start_date = contract_data.get('start_date')
    validation_error = validate_date_format(start_date)
    if validation_error:
        return {"msg": validation_error}, 400

    # Obter duração
    duration = contract_data.get('duration')

    # Obter data de fim
    end_date = contract_data.get('end_date')
    validation_error = validate_date_format(end_date)
    if validation_error:
        return {"msg": validation_error}, 400

    if not salary or not start_date:
        return {"msg": "Salary and start date are required"}, 400

    add_employee_data(salary, start_date, duration, end_date, username)
    return 200


##########################################################
# ADD COMMON USER DATA
##########################################################
def add_common_data(username, password, name, mobile_number, birth_date, address, email):
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Encriptar a password
    hashed_password = generate_password_hash(password)

    try:
        cur.execute('''
                INSERT INTO person (username, password, name, mobile_number, birth_date, address, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (username, hashed_password, name, mobile_number, birth_date, address, email))
        db.commit()
        return {"msg": "User added successfully", "username": username}, 200
    except Exception as e:
        db.rollback()
        return {"msg": str(e)}, 500
    finally:
        cur.close()
        db.close()


##########################################################
# ADD EMPLOYEE CONTRACT DATA
##########################################################
def add_employee_data(salary, start_date, duration, end_date, username):
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    try:
        cur.execute('''
                INSERT INTO employee_contract (contract_salary, contract_start_date, 
                contract_duration, contract_end_date, person_username)
                VALUES (%s, %s, %s, %s, %s)
            ''', (salary, start_date, duration, end_date, username))
        db.commit()
        return {"msg": "Contract added successfully"}, 200
    except Exception as e:
        db.rollback()
        return {"msg": str(e)}, 500
    finally:
        cur.close()
        db.close()


##########################################################
# REMOVE COMMON DATA IF CONTRACT DATA HAS ERRORS
##########################################################
def contract_check(username, contract_data):
    status = get_employee_contract_data(username, contract_data)
    if status != 200:
        db = db_connection()
        cur = db.cursor()
        try:
            cur.execute('DELETE FROM person WHERE LOWER(username) = LOWER(%s)', (username,))
            db.commit()
        except Exception as e:
            db.rollback()
            return {"msg": str(e)}, 500
        finally:
            cur.close()
            db.close()
        return {"msg": status}, 500
    return {"msg": "Contract added successfully"}, 200


##########################################################
# ADD PATIENT
##########################################################
@app.route('/dbproj/register/patient', methods=['POST'])
def register_patient():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Adicionar os dados comuns do user
    data = request.get_json()
    username, status = get_common_user_data(data)
    if status != 200:
        return jsonify(username), status

    # Adicionar o paciente
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO patient (person_username)
            VALUES (%s)
        ''', (username,))
        db.commit()
        return jsonify({"msg": "Patient added successfully", "username": username}), 200
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

    # Adicionar os dados comuns do user
    data = request.get_json()
    username, status = get_common_user_data(data)
    if status != 200:
        return jsonify(username), status

    # Adicionar os dados do contrato do assistente
    contract_data = data.get('contract', {})
    response, status = contract_check(username, contract_data)
    if status != 200:
        return jsonify(response), status

    # Adicionar o assistente
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO assistants (employee_contract_person_username)
            VALUES (%s)
        ''', (username,))
        db.commit()
        return jsonify({"msg": "Assistant added successfully", "username": username}), 200
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

    # Adicionar os dados do enfermeiro
    data = request.get_json()
    position = data.get('position', None)
    if not position:
        return jsonify({"msg": "Missing required field: position"}), 400

    # Adicionar os dados comuns do user
    username, status = get_common_user_data(data)
    if status != 200:
        return jsonify(username), status

    # Adicionar os dados do contrato do enfermeiro
    contract_data = data.get('contract', {})
    response, status = contract_check(username, contract_data)
    if status != 200:
        return jsonify(response), status

    # Adicionar o enfermeiro
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''
            INSERT INTO nurses (position, employee_contract_person_username)
            VALUES (%s, %s)
        ''', (position, username))
        db.commit()
        return jsonify({"msg": "Nurse added successfully", "username": username}), 200
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

    # Adicionar os dados do médico
    data = request.get_json()
    db = db_connection()
    cur = db.cursor()
    doctor_license = data.get('license_info', None)
    if not doctor_license:
        return jsonify({"msg": "Missing required field: license_info"}), 400
    specializations = data.get('specializations_ids', [])
    if not specializations:
        return jsonify({"msg": "At least one specialization must be specified"}), 400
    for specialization_id in specializations:
        if not str(specialization_id).isdigit():
            return jsonify({"msg": "Specialization ID must contain only digits"}), 400
        cur.execute('SELECT 1 FROM specializations WHERE specialization_id = %s', (specialization_id,))
        if cur.fetchone() is None:
            return jsonify({"msg": f"Specialization ID {specialization_id} does not exist"}), 400

    # Adicionar os dados comuns do user
    username, status = get_common_user_data(data)
    if status != 200:
        return jsonify(username), status

    # Adicionar os dados do contrato do médico
    contract_data = data.get('contract', {})
    response, status = contract_check(username, contract_data)
    if status != 200:
        return jsonify(response), status

    # Adicionar o médico
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
        return jsonify({"msg": "Doctor added successfully", "username": username}), 200
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

    # Obter username e password
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    # Conectar à base de dados e procurar o utilizador
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('SELECT password FROM person WHERE username = %s', (username,))
        user = cur.fetchone()
        if user is None:
            return jsonify({"msg": "Username not found"}), 400
        stored_password = user[0]

        # Verificar a password encriptada
        if check_password_hash(stored_password, password):
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"msg": "Bad username or password"}), 400
    finally:
        cur.close()
        db.close()


##########################################################
# SCHEDULE APPOINTMENT
##########################################################
@app.route('/dbproj/appointment', methods=['POST'])
@jwt_required()
def schedule_appointment():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Obter o nome do paciente que está a fazer o pedido
    patient_user = get_jwt_identity()

    # Obter o 'id' do médico para o qual o paciente quer marcar a consulta
    doctor_user = request.json.get('doctor_id')
    cur.execute("SELECT 1 FROM doctors WHERE LOWER(employee_contract_person_username) = LOWER(%s)", (doctor_user,))
    doctor = cur.fetchone()
    if doctor is None:
        return jsonify({"msg": "Doctor not found"}), 400

    # Obter a data e hora da consulta
    date = request.json.get('date')
    validation_error = validate_date_time_format(date)
    if validation_error:
        return jsonify({"msg": validation_error}), 400

    if not doctor_user or not date:
        return jsonify({"msg": "All fields are required"}), 400

    # Verificar se o médico está disponível na data e hora pretendida
    cur.execute("""
        SELECT 1 
        FROM appointments
        WHERE LOWER(doctors_employee_contract_person_username) = LOWER(%s) 
        AND appointment_date = %s
    """, (doctor_user, date))
    appointment_exists = cur.fetchone()
    if appointment_exists is not None:
        return jsonify({"msg": "Doctor is not available at the given date and time"}), 400

    # Marcar a consulta
    try:
        cur.execute("""
                    INSERT INTO appointments (
                        appointment_date, 
                        patient_person_username, 
                        doctors_employee_contract_person_username
                    ) VALUES (%s, %s, %s) RETURNING appointment_id
                """, (date, patient_user, doctor_user))
        appointment_id = cur.fetchone()[0]
        db.commit()
        return jsonify({"status": 200, "results": appointment_id}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# SEE APPOINTMENTS
##########################################################
@app.route('/dbproj/appointments/<int:patient_user_id>', methods=['GET'])
@jwt_required()
def see_appointments(patient_user_id):
    # Verify the identity and rights to access this patient's appointments
    current_user = get_jwt_identity()
    if current_user != patient_user_id:
        return jsonify({"status": 401, "errors": "Unauthorized access"}), 401

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''SELECT appointment_id, doctors_employee_contract_person_username, appointment_date
                       FROM appointments WHERE patient_person_username = %s''', (patient_user_id,))
        appointments = cur.fetchall()
        results = [{"id": appt[0], "doctor_id": appt[1], "date": appt[2]} for appt in appointments]
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


##########################################################
# SCHEDULE SURGERY
##########################################################
@app.route('/dbproj/surgery', methods=['POST'])
@jwt_required()
def schedule_surgery():
    patient_id = request.json.get('patient_id')
    doctor_id = request.json.get('doctor')
    nurses = request.json.get('nurses')  # List of [nurse_id, role]
    date = request.json.get('date')

    db = db_connection()
    cur = db.cursor()
    try:
        # Insert the surgery and perhaps a new hospitalization
        cur.execute('''INSERT INTO surgeries (patient_id, doctor_id, date)
                       VALUES (%s, %s, %s) RETURNING surgery_id''', (patient_id, doctor_id, date))
        surgery_id = cur.fetchone()[0]
        # Insert nurses involved in the surgery
        for nurse in nurses:
            cur.execute('''INSERT INTO surgery_nurses (surgery_id, nurse_id, role)
                           VALUES (%s, %s, %s)''', (surgery_id, nurse[0], nurse[1]))
        db.commit()
        return jsonify({"status": 201, "results": {"surgery_id": surgery_id}}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# GET PRESCRIPTIONS
##########################################################
@app.route('/dbproj/prescriptions/<int:person_id>', methods=['GET'])
@jwt_required()
def get_prescriptions(person_id):
    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('''SELECT prescription_id, validity, dosage, frequency, medicine_name
                       FROM prescriptions WHERE person_id = %s''', (person_id,))
        prescriptions = cur.fetchall()
        results = [{"id": pres[0], "validity": pres[1], "posology": {"dose": pres[2], "frequency": pres[3],
                                                                     "medicine": pres[4]}} for pres in prescriptions]
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


##########################################################
# ADD PRESCRIPTIONS
##########################################################
@app.route('/dbproj/prescription/', methods=['POST'])
@jwt_required()
def add_prescription():
    event_id = request.json.get('event_id')
    req_type = request.json.get('type')  # "hospitalization" or "appointment"
    validity = request.json.get('validity')
    medicines = request.json.get('medicines')  # List of medicine details

    db = db_connection()
    cur = db.cursor()
    try:
        for medicine in medicines:
            cur.execute('''INSERT INTO prescriptions (event_id, type, validity, medicine_name, dosage, frequency)
                           VALUES (%s, %s, %s, %s, %s, %s) RETURNING prescription_id''',
                        (event_id, req_type, validity, medicine['medicine'], medicine['posology_dose'],
                         medicine['posology_frequency']))
        db.commit()
        return jsonify({"status": 201, "results": "Prescription added"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# EXECUTE PAYMENT
##########################################################
@app.route('/dbproj/bills/<int:bill_id>', methods=['POST'])
@jwt_required()
def execute_payment(bill_id):
    current_user = get_jwt_identity()  # Assuming the identity is the patient's username
    amount = request.json.get('amount')
    payment_method = request.json.get('payment_method')

    db = db_connection()
    cur = db.cursor()
    try:
        cur.execute('SELECT patient_person_username, total_amount FROM bills WHERE bill_id = %s', (bill_id,))
        bill = cur.fetchone()
        if not bill:
            return jsonify({"status": 404, "errors": "Bill not found"}), 404
        if bill[0] != current_user:
            return jsonify({"status": 401, "errors": "Unauthorized"}), 401

        new_remaining_value = bill[1] - amount
        if new_remaining_value <= 0:
            cur.execute('UPDATE bills SET status = %s WHERE bill_id = %s', ('paid', bill_id))
        cur.execute('INSERT INTO payments (bill_id, amount, payment_method) VALUES (%s, %s, %s)',
                    (bill_id, amount, payment_method))
        db.commit()
        return jsonify({"status": 200, "results": new_remaining_value}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# LIST TOP 3 PATIENTS
##########################################################
@app.route('/dbproj/top3', methods=['GET'])
@jwt_required()
def list_top_three_patients():
    db = db_connection()
    cur = db.cursor()
    try:
        # Sample SQL to list top 3 spending patients
        cur.execute('''
        SELECT patient_name, SUM(amount) as total_spent
        FROM payments JOIN patients ON payments.patient_id = patients.id
        WHERE payment_date >= date_trunc('month', current_date)
        GROUP BY patient_name
        ORDER BY total_spent DESC
        LIMIT 3
        ''')
        top_patients = cur.fetchall()
        results = [{"patient_name": pat[0], "amount_spent": pat[1]} for pat in top_patients]
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


##########################################################
# DAILY SUMMARY
##########################################################
@app.route('/dbproj/daily/<date>', methods=['GET'])
@jwt_required()
def daily_summary(date):
    db = db_connection()
    cur = db.cursor()
    try:
        # Sample SQL to get daily summary
        cur.execute('''
        SELECT SUM(amount) as amount_spent, COUNT(DISTINCT surgery_id) as surgeries, 
        COUNT(DISTINCT prescription_id) as prescriptions
        FROM hospitalizations
        WHERE entry_date = %s
        ''', (date,))
        summary = cur.fetchone()
        results = {"amount_spent": summary[0], "surgeries": summary[1], "prescriptions": summary[2]}
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


##########################################################
# GENERATE A MONTHLY REPORT
##########################################################
@app.route('/dbproj/report', methods=['GET'])
@jwt_required()
def generate_monthly_report():
    db = db_connection()
    cur = db.cursor()
    try:
        # Sample SQL to get monthly report for doctors with most surgeries
        cur.execute('''
        SELECT EXTRACT(MONTH FROM surgery_date) as month, doctor_name, COUNT(surgery_id) as total_surgeries
        FROM surgeries JOIN doctors ON surgeries.doctor_id = doctors.id
        WHERE surgery_date > current_date - INTERVAL '1 YEAR'
        GROUP BY month, doctor_name
        ORDER BY month, total_surgeries DESC
        ''')
        reports = cur.fetchall()
        results = [{"month": report[0], "doctor": report[1], "surgeries": report[2]} for report in reports]
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


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
