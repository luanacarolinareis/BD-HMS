from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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
    if birth_date is not None:
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
    if start_date is not None:
        validation_error = validate_date_format(start_date)
        if validation_error:
            return {"msg": validation_error}, 400

    # Obter duração
    duration = contract_data.get('duration')

    # Obter data de fim
    end_date = contract_data.get('end_date')
    if end_date is not None:
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
            return jsonify({"msg": "Bad password"}), 400
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

    # Verificar se o utilizador é um paciente
    cur.execute("SELECT 1 FROM patient WHERE LOWER(person_username) = LOWER(%s)", (patient_user,))
    is_patient = cur.fetchone()
    if is_patient is None:
        return jsonify({"msg": "Access denied. Only patients can schedule appointments."}), 400

    # Obter o 'id' do médico para o qual o paciente quer marcar a consulta
    doctor_user = request.json.get('doctor_id')
    cur.execute("SELECT 1 FROM doctors WHERE LOWER(employee_contract_person_username) = LOWER(%s)", (doctor_user,))
    doctor = cur.fetchone()
    if doctor is None:
        return jsonify({"msg": "Doctor not found"}), 400

    # Obter a data e hora da consulta
    date = request.json.get('date')
    if date is not None:
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

    # Verificar se o paciente já tem uma consulta marcada para a data e hora pretendida
    cur.execute("""
            SELECT 1 
            FROM appointments
            WHERE LOWER(patient_person_username) = LOWER(%s) 
            AND appointment_date = %s
        """, (patient_user, date))
    appointment_exists = cur.fetchone()
    if appointment_exists is not None:
        return jsonify({"msg": "Patient already has an appointment scheduled at the given date and time"}), 400

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
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Obter o nome do paciente ou assistente que está a fazer o pedido
    current_user = get_jwt_identity()

    # Verificar se o utilizador é um paciente ou um assistente
    cur.execute("SELECT 1 FROM patient WHERE LOWER(person_username) = LOWER(%s)", (current_user,))
    is_patient = cur.fetchone()
    if is_patient is None:
        cur.execute("SELECT 1 FROM assistants WHERE LOWER(employee_contract_person_username) = LOWER(%s)",
                    (current_user,))
        is_assistant = cur.fetchone()
        if is_assistant is None:
            return jsonify({"msg": "Access denied. Only assistants/target patient can see appointments."}), 400

    # Obter username do paciente a consultar
    cur.execute("SELECT person_username FROM patient WHERE patient_id = %s", (patient_user_id,))
    patient_name_result = cur.fetchone()
    if patient_name_result is None:
        return jsonify({"msg": "Patient not found"}), 400
    patient_name = patient_name_result[0]

    # Devolver as consultas marcadas para o paciente
    try:
        cur.execute('''SELECT appointment_id, doctors_employee_contract_person_username, appointment_date
                       FROM appointments WHERE LOWER(patient_person_username) = LOWER(%s)''', (patient_name,))
        appointments = cur.fetchall()
        if appointments is None:
            return jsonify({"msg": "No appointments found"}), 400
        results = [{"id": appt[0], "doctor_id": appt[1], "date": appt[2]} for appt in appointments]
        return jsonify({"status": 200, "results": results}), 200
    finally:
        cur.close()
        db.close()


##########################################################
# SCHEDULE SURGERY
##########################################################
@app.route('/dbproj/surgery', methods=['POST'])
@app.route('/dbproj/surgery/<int:hospitalization_id>', methods=['POST'])
@jwt_required()
def schedule_surgery(hospitalization_id=None):
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Obter o nome do assistente que está a fazer o pedido
    current_user = get_jwt_identity()

    # Verificar se o utilizador é um assistente
    cur.execute('SELECT 1 FROM assistants WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (current_user,))
    is_assistant = cur.fetchone()
    if is_assistant is None:
        return jsonify({"msg": "Access denied. Only assistants can schedule surgeries."}), 400

    # Obter os dados da cirurgia
    patient_id = request.json.get('patient_id')
    validation_error = validate_username(patient_id)
    if validation_error:
        return jsonify({"msg": validation_error}), 400
    cur.execute('SELECT 1 FROM patient WHERE LOWER(person_username) = LOWER(%s)', (patient_id,))
    patient_exists = cur.fetchone()
    if patient_exists is None:
        return jsonify({"msg": "Patient not found"}), 400

    doctor = request.json.get('doctor')
    validation_error = validate_username(doctor)
    if validation_error:
        return jsonify({"msg": validation_error}), 400
    cur.execute('SELECT 1 FROM doctors WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (doctor,))
    doctor_exists = cur.fetchone()
    if doctor_exists is None:
        return jsonify({"msg": "Doctor not found"}), 400

    nurses = request.json.get('nurses')
    for nurse in nurses:
        validation_error = validate_username(nurse[0])
        if validation_error:
            return jsonify({"msg": validation_error}), 400
        cur.execute('SELECT 1 FROM nurses WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (nurse[0],))
        nurse_exists = cur.fetchone()
        if nurse_exists is None:
            return jsonify({"msg": "Nurse not found"}), 400

    date = request.json.get('date')
    if date is not None:
        validation_error = validate_date_time_format(date)
        if validation_error:
            return jsonify({"msg": validation_error}), 400

    if not patient_id or not doctor or not nurses or not date:
        return jsonify({"msg": "All fields are required"}), 400

    # Verificar se o médico está disponível na data e hora pretendida
    cur.execute("""
        SELECT 1 
        FROM surgeries
        WHERE LOWER(doctors_employee_contract_person_username) = LOWER(%s) 
        AND surgery_date = %s
    """, (doctor, date))
    surgery_exists = cur.fetchone()
    if surgery_exists is not None:
        return jsonify({"msg": "Doctor is not available at the given date and time"}), 400

    # Verificar se o 'id' de hospitalização é válido
    if hospitalization_id is not None:
        cur.execute('SELECT 1 FROM hospitalizations WHERE hospitalization_id = %s', (hospitalization_id,))
        hospitalization_exists = cur.fetchone()
        if hospitalization_exists is None:
            return jsonify({"msg": "Hospitalization not found"}), 400

    try:
        # Se ainda não existir uma hospitalização associada, criar uma
        if hospitalization_id is None:
            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            begin_date_obj = date_obj - timedelta(days=3)
            end_date_obj = date_obj + timedelta(days=3)

            cur.execute('''INSERT INTO hospitalizations (begin_date, end_date, patient_person_username, 
            assistants_employee_contract_person_username, nurses_employee_contract_person_username)
            VALUES (%s, %s, %s, %s, %s) RETURNING hospitalization_id''',
                        (begin_date_obj.strftime('%Y-%m-%d %H:%M:%S'),
                         end_date_obj.strftime('%Y-%m-%d %H:%M:%S'), patient_id, current_user, nurses[0][0]))
            hospitalization_id = cur.fetchone()[0]

        # Inserir a cirurgia
        cur.execute('''INSERT INTO surgeries (surgery_date, hospitalizations_hospitalization_id, 
        doctors_employee_contract_person_username) VALUES (%s, %s, %s) RETURNING surgery_id''',
                    (date, hospitalization_id, doctor))
        surgery_id = cur.fetchone()[0]

        # Inserir os enfermeiros associados à cirurgia
        for nurse in nurses:
            cur.execute('''INSERT INTO nurses_surgeries (nurses_employee_contract_person_username, surgeries_surgery_id)
                                   VALUES (%s, %s)''', (nurse[0], surgery_id))

        db.commit()
        return jsonify({"status": 200, "results": {"hospitalization_id": hospitalization_id, "surgery_id": surgery_id,
                                                   "patient_id": patient_id, "doctor_id": doctor,
                                                   "date": date}}), 200
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
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Verificar se o 'id' do paciente é válido
    cur.execute('SELECT person_username FROM patient WHERE patient_id = %s', (person_id,))
    patient_exists = cur.fetchone()
    if patient_exists is None:
        return jsonify({"msg": "Patient not found"}), 400
    patient_username = patient_exists[0]

    try:
        cur.execute('''
                   SELECT p.prescription_id, p.prescription_date, pos.dosage, pos.frequency, m.medicine_name
                   FROM prescriptions p
                   JOIN hospitalizations_prescriptions hp ON p.prescription_id = hp.prescriptions_prescription_id
                   JOIN hospitalizations h ON hp.hospitalizations_hospitalization_id = h.hospitalization_id
                   JOIN posology pos ON p.prescription_id = pos.prescriptions_prescription_id
                   JOIN medicines m ON pos.medicines_medicine_name = m.medicine_name
                   WHERE h.patient_person_username = %s
                   UNION
                   SELECT p.prescription_id, p.prescription_date, pos.dosage, pos.frequency, m.medicine_name
                   FROM prescriptions p
                   JOIN appointments_prescriptions ap ON p.prescription_id = ap.prescriptions_prescription_id
                   JOIN appointments a ON ap.appointments_appointment_id = a.appointment_id
                   JOIN posology pos ON p.prescription_id = pos.prescriptions_prescription_id
                   JOIN medicines m ON pos.medicines_medicine_name = m.medicine_name
                   WHERE a.patient_person_username = %s
               ''', (patient_username, patient_username))

        prescriptions = cur.fetchall()
        results = [
            {
                "id": pres[0],
                "validity": pres[1],
                "posology": [
                    {
                        "dose": pres[2],
                        "frequency": pres[3],
                        "medicine": pres[4]
                    }
                ]
            }
            for pres in prescriptions
        ]
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
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    # Obter os dados da prescrição
    req_type = request.json.get('type')  # "hospitalization" or "appointment"
    if req_type not in ['hospitalization', 'appointment']:
        return jsonify({"msg": "Invalid request type"}), 400

    event_id = request.json.get('event_id')
    if not str(event_id).isdigit():
        return jsonify({"msg": "Event ID must contain only digits"}), 400

    validity = request.json.get('validity')
    validation_error = validate_date_format(validity)
    if validation_error:
        return jsonify({"msg": validation_error}), 400

    medicines = request.json.get('medicines')
    for med in medicines:
        cur.execute('SELECT 1 FROM medicines WHERE LOWER(medicine_name) = LOWER(%s)', (med.get('medicine'),))
        med_exists = cur.fetchone()
        if med_exists is None:
            return jsonify({"msg": "Medicine not found"}), 400

    if not req_type or not event_id or not validity or not medicines:
        return jsonify({"msg": "All fields are required"}), 400

    current_user = get_jwt_identity()

    # Verificar se o utilizador é um médico
    cur.execute('SELECT 1 FROM doctors WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (current_user,))
    if not cur.fetchone():
        return jsonify({"msg": "Only doctors can add prescriptions"}), 400

    try:
        # Inserir prescrição
        cur.execute('INSERT INTO prescriptions (prescription_date) VALUES (%s) RETURNING prescription_id', (validity,))
        prescription_id = cur.fetchone()[0]

        # Inserir posologia e eventos associados
        for medicine in medicines:
            medicine_name = medicine.get('medicine')
            posology_dose = medicine.get('posology_dose')
            posology_frequency = medicine.get('posology_frequency')

            # Inserir detalhes de posologia
            cur.execute(
                'INSERT INTO posology (dosage, frequency, prescriptions_prescription_id, medicines_medicine_name)'
                'VALUES (%s, %s, %s, %s)', (posology_dose, posology_frequency, prescription_id, medicine_name))

        # Associar a prescrição ao evento associado
        if req_type == 'hospitalization':
            cur.execute(
                'INSERT INTO hospitalizations_prescriptions (hospitalizations_hospitalization_id, '
                'prescriptions_prescription_id)'' VALUES (%s, %s)', (event_id, prescription_id))
        elif req_type == 'appointment':
            cur.execute(
                'INSERT INTO appointments_prescriptions (appointments_appointment_id, prescriptions_prescription_id) '
                'VALUES (%s, %s)', (event_id, prescription_id))
        db.commit()
        return jsonify({"status": 200, "results": {"prescription_id": prescription_id}}), 200
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
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    current_user = get_jwt_identity()

    # Obter os dados do pagamento
    amount = request.json.get('amount')
    payment_method = request.json.get('payment_method')

    if amount is None or payment_method is None:
        return jsonify({"status": 400, "errors": "Missing payment details"}), 400

    # Verificar se o 'bill_id' é válido
    cur.execute('SELECT 1 FROM bills WHERE bill_id = %s', (bill_id,))
    if not cur.fetchone():
        return jsonify({"msg": "Bill not found"}), 400

    try:
        # Verificar se o utilizador é o dono da fatura
        cur.execute('''
                    SELECT b.total_price, COALESCE(SUM(p.payment_amount), 0) AS total_paid, pa.person_username
                    FROM bills b
                    LEFT JOIN payments p ON b.bill_id = p.payment_id
                    LEFT JOIN appointments_bills ab ON b.bill_id = ab.appointments_appointment_id
                    LEFT JOIN appointments a ON ab.appointments_appointment_id = a.appointment_id
                    LEFT JOIN patient pa ON a.patient_person_username = pa.person_username
                    WHERE b.bill_id = %s
                    GROUP BY b.bill_id, b.total_price, pa.person_username
                ''', (bill_id,))
        bill = cur.fetchone()

        if not bill:
            return jsonify({"status": 404, "errors": "Bill not found"}), 404

        total_price, total_paid, bill_owner = bill

        if bill_owner != current_user:
            return jsonify({"status": 401, "errors": "Unauthorized"}), 401

        # Calcular o valor restante
        new_remaining_value = total_price - amount
        if new_remaining_value < 0:
            return jsonify({"status": 400, "errors": "Payment exceeds the remaining bill amount"}), 400

        # Inserir o pagamento
        cur.execute('''
                    INSERT INTO payments (payment_amount, deadline_date)
                    VALUES (%s, NOW())
                ''', (amount,))

        # Atualizar o estado do pagamento, se totalmente pago
        cur.execute('UPDATE bills SET total_price = %s WHERE bill_id = %s', (new_remaining_value, bill_id))
        if new_remaining_value == 0:
            cur.execute('UPDATE bills SET payment_method = %s WHERE bill_id = %s', (payment_method, bill_id))

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
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    current_user = get_jwt_identity()

    # Verificar se o utilizador é um assistente
    cur.execute('SELECT 1 FROM assistants WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (current_user,))
    if not cur.fetchone():
        return jsonify({"msg": "Only assistants can see top 3"}), 400

    try:
        cur.execute('''
            SELECT p.person_username, SUM(pa.payment_amount) AS total_spent, 
                   json_agg(json_build_object('id', a.appointment_id, 
                                              'doctor_id', a.doctors_employee_contract_person_username, 
                                              'date', a.appointment_date)) AS procedures
            FROM patient p 
            LEFT JOIN appointments a ON p.person_username = a.patient_person_username
            LEFT JOIN payments pa ON a.appointment_id = pa.payment_id
            WHERE EXTRACT(MONTH FROM pa.deadline_date) = EXTRACT(MONTH FROM CURRENT_DATE)
            GROUP BY p.person_username
            ORDER BY total_spent DESC
            LIMIT 3
        ''')
        top_patients = cur.fetchall()
        results = [{"person_username": pat[0], "amount_spent": pat[1], "procedures": pat[2]} for pat in top_patients]
        return jsonify({"status": 200, "results": results}), 200
    except Exception as e:
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# DAILY SUMMARY
##########################################################
@app.route('/dbproj/daily/<date>', methods=['GET'])
@jwt_required()
def daily_summary(date):
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    current_user = get_jwt_identity()

    # Verificar se o utilizador é um assistente
    cur.execute('SELECT 1 FROM assistants WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (current_user,))
    if not cur.fetchone():
        return jsonify({"msg": "Only assistants can see daily summary"}), 400

    try:
        # Verificar se a data está no formato correto (YYYY-MM-DD)
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"status": 400, "errors": "Invalid date format. Please use YYYY-MM-DD."}), 400

        cur.execute('''
            SELECT 
                COALESCE(SUM(b.total_price), 0) as amount_spent, 
                COUNT(DISTINCT s.surgery_id) as surgeries, 
                COUNT(DISTINCT p.prescription_id) as prescriptions
            FROM hospitalizations h
            LEFT JOIN surgeries s ON h.hospitalization_id = s.hospitalizations_hospitalization_id
            LEFT JOIN hospitalizations_prescriptions hp ON h.hospitalization_id = hp.hospitalizations_hospitalization_id
            LEFT JOIN prescriptions p ON hp.prescriptions_prescription_id = p.prescription_id
            LEFT JOIN bills b ON h.hospitalization_id = b.hospitalizations_hospitalization_id
            WHERE h.entry_date = %s
        ''', (date,))

        summary = cur.fetchone()
        results = {"amount_spent": summary[0], "surgeries": summary[1], "prescriptions": summary[2]}

        return jsonify({"status": 200, "results": results}), 200
    except Exception as e:
        return jsonify({"status": 500, "errors": str(e)}), 500
    finally:
        cur.close()
        db.close()


##########################################################
# GENERATE A MONTHLY REPORT
##########################################################
@app.route('/dbproj/report', methods=['GET'])
@jwt_required()
def generate_monthly_report():
    # Conectar à base de dados
    db = db_connection()
    cur = db.cursor()

    current_user = get_jwt_identity()

    # Verificar se o utilizador é um assistente
    cur.execute('SELECT 1 FROM assistants WHERE LOWER(employee_contract_person_username) = LOWER(%s)', (current_user,))
    if not cur.fetchone():
        return jsonify({"msg": "Only assistants can generate a monthly report"}), 400

    try:
        # Sample SQL to get monthly report for doctors with most surgeries
        cur.execute('''
        SELECT EXTRACT(MONTH FROM surgery_date) as month, doctors.doctor_name, COUNT(surgery_id) as total_surgeries
        FROM surgeries 
        JOIN doctors ON surgeries.doctors_employee_contract_person_username = doctors.employee_contract_person_username
        WHERE surgery_date > current_date - INTERVAL '1 YEAR'
        GROUP BY month, doctors.doctor_name
        ORDER BY month, total_surgeries DESC
        ''')
        reports = cur.fetchall()
        results = [{"month": int(report[0]), "doctor": report[1], "surgeries": report[2]} for report in reports]
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
