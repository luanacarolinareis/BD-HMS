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
    if not success:
        # Remover o 'user' da tabela 'person' se a inserção do contrato falhar
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
        return {"msg": error}, 500
    return None


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
    contract_error = contract_check(username, contract_data)
    if contract_error:
        return jsonify(contract_error), 500

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
@app.route('/dbproj/login', methods=['POST'])
def login():
    # Check if the request contains JSON
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Retrieve the user's password hash from the database
        cur.execute('SELECT password FROM person WHERE username = %s', (username,))
        user = cur.fetchone()

        if user and check_password_hash(user[0], password):
            # If the password matches, generate a JWT
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            # If the password does not match or user does not exist
            return jsonify({"msg": "Bad username or password"}), 401

    except Exception as e:
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
def schedule_appointment(data):
    db = db_connection()
    cur = db.cursor()

    # Extrai informações do pedido
    patient_username = data.get('patient_username')
    doctor_username = data.get('doctor_username')
    appointment_date = data.get('date')  # formato 'YYYY-MM-DD'
    appointment_time = data.get('time')  # formato 'HH:MM'
    default_begin_date = appointment_date  # Usando a data do agendamento como data padrão

    # Validações simples
    if not (patient_username and doctor_username and appointment_date and appointment_time):
        return {"msg": "All fields are required"}, 400

    # Verifica disponibilidade
    cur.execute('''
        SELECT * FROM appointments_hospitalizations_bills
        WHERE doctors_employee_contract_person_username = %s AND appointment_date = %s
    ''', (doctor_username, appointment_date + ' ' + appointment_time))
    if cur.fetchone() is not None:
        return {"msg": "This slot is already booked"}, 400

    # Insere a nova consulta no banco de dados
    try:
        cur.execute('''
            INSERT INTO appointments_hospitalizations_bills (
                doctors_employee_contract_person_username, patient_person_username,
                appointment_date, hospitalizations_bills_begin_date
            )
            VALUES (%s, %s, %s, %s)
        ''', (doctor_username, patient_username, appointment_date + ' ' + appointment_time, default_begin_date))
        db.commit()
        return {"msg": "Appointment scheduled successfully"}, 201
    except Exception as e:
        db.rollback()
        return {"msg": str(e)}, 500
    finally:
        cur.close()
        db.close()



@app.route('/dbproj/schedule/appointment', methods=['POST'])
def create_appointment():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()
    result, status = schedule_appointment(data)
    return jsonify(result), status

##########################################################
# SEE APPOINTMENTS
##########################################################
@app.route('/dbproj/view/appointments', methods=['GET'])
@jwt_required()
def view_appointments():
    current_user = get_jwt_identity()
    patient_username = request.args.get('patient_username')
    doctor_username = request.args.get('doctor_username')
    appointment_date = request.args.get('date')  # formato 'YYYY-MM-DD'

    db = db_connection()
    cur = db.cursor()

    query = 'SELECT * FROM appointments_hospitalizations_bills WHERE true'
    params = []

    if patient_username:
        query += ' AND patient_person_username = %s'
        params.append(patient_username)
    if doctor_username:
        query += ' AND doctors_employee_contract_person_username = %s'
        params.append(doctor_username)
    if appointment_date:
        query += ' AND appointment_date = %s'
        params.append(appointment_date)

    cur.execute(query, tuple(params))
    appointments = cur.fetchall()

    cur.close()
    db.close()

    appointments_data = [{
        'appointment_id': a[0],
        'doctor_username': a[1],
        'patient_username': a[2],
        'appointment_date': a[3]
    } for a in appointments]

    return jsonify(appointments_data), 200


##########################################################
# SCHEDULE SURGERY
##########################################################
@app.route('/dbproj/schedule/surgery', methods=['POST'])
@jwt_required()
def schedule_surgery():
    # Check if the request body is JSON
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()
    surgery_date = data.get('date')  # Format 'YYYY-MM-DD HH:MM:SS'
    start_time = data.get('start_time')  # Format 'HH:MM'
    end_time = data.get('end_time')  # Format 'HH:MM'
    doctor_username = data.get('doctor_username')
    patient_username = data.get('patient_username')

    if not all([surgery_date, start_time, end_time, doctor_username, patient_username]):
        return jsonify({"msg": "Missing required fields"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Check if the doctor is available
        cur.execute('''
            SELECT COUNT(*)
            FROM surgeries
            WHERE doctors_employee_contract_person_username = %s AND start_time BETWEEN %s AND %s
        ''', (doctor_username, surgery_date + ' ' + start_time, surgery_date + ' ' + end_time))
        if cur.fetchone()[0] > 0:
            return jsonify({"msg": "Doctor is not available at the selected time"}), 400

        # Insert the new surgery into the database
        cur.execute('''
            INSERT INTO surgeries (start_time, end_time, doctors_employee_contract_person_username, patient_person_username)
            VALUES (%s, %s, %s, %s)
            RETURNING surgery_id
        ''', (surgery_date + ' ' + start_time, surgery_date + ' ' + end_time, doctor_username, patient_username))
        surgery_id = cur.fetchone()[0]
        db.commit()
        return jsonify({"msg": "Surgery scheduled successfully", "surgery_id": surgery_id}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500

    finally:
        cur.close()
        db.close()

##########################################################
# GET PRESCRIPTIONS
##########################################################
@app.route('/dbproj/get/prescriptions', methods=['GET'])
@jwt_required()
def get_prescriptions():
    # Obter o usuário logado
    current_user = get_jwt_identity()

    # Extrair parâmetros de consulta (query parameters)
    patient_username = request.args.get('patient_username')
    date = request.args.get('date')  # formato 'YYYY-MM-DD'

    db = db_connection()
    cur = db.cursor()

    # Montar a consulta SQL baseada nos parâmetros fornecidos
    query = '''
    SELECT p.prescription_id, p.prescription_date, pos.dosage, pos.frequency, m.medicine_name
    FROM prescriptions p
    JOIN posology pos ON p.prescription_id = pos.prescriptions_prescription_id
    JOIN medicines m ON pos.medicines_medicine_name = m.medicine_name
    WHERE true
    '''
    params = []

    if patient_username:
        query += ' AND p.patient_username = %s'
        params.append(patient_username)
    if date:
        query += ' AND p.prescription_date = %s'
        params.append(date)

    # Executar a consulta
    cur.execute(query, tuple(params))
    prescriptions = cur.fetchall()
    cur.close()
    db.close()

    # Formatar a resposta
    prescriptions_data = [{
        'prescription_id': pres[0],
        'prescription_date': pres[1],
        'medicine_name': pres[4],
        'dosage': pres[2],
        'frequency': pres[3]
    } for pres in prescriptions]

    return jsonify(prescriptions_data), 200


##########################################################
# ADD PRESCRIPTIONS
##########################################################
@app.route('/dbproj/add/prescription', methods=['POST'])
@jwt_required()
def add_prescription():
    # Verifica se o pedido é JSON
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Extrai dados do JSON
    data = request.get_json()
    patient_username = data.get('patient_username')
    prescription_date = data.get('prescription_date')  # formato 'YYYY-MM-DD'
    medicines = data.get('medicines')  # Lista de dicionários {medicine_name, dosage, frequency}

    if not patient_username or not prescription_date or not medicines:
        return jsonify({"msg": "Missing required fields"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Insere a prescrição na tabela de prescrições
        cur.execute('''
            INSERT INTO prescriptions (prescription_date, patient_person_username)
            VALUES (%s, %s) RETURNING prescription_id
        ''', (prescription_date, patient_username))
        prescription_id = cur.fetchone()[0]

        # Insere detalhes dos medicamentos na tabela de posologia
        for medicine in medicines:
            medicine_name = medicine['medicine_name']
            dosage = medicine['dosage']
            frequency = medicine['frequency']

            # Verifica se o medicamento existe
            cur.execute('SELECT medicine_name FROM medicines WHERE medicine_name = %s', (medicine_name,))
            if cur.fetchone() is None:
                # Insere o medicamento se não existir
                cur.execute('INSERT INTO medicines (medicine_name) VALUES (%s)', (medicine_name,))

            # Insere a posologia
            cur.execute('''
                INSERT INTO posology (prescriptions_prescription_id, medicines_medicine_name, dosage, frequency)
                VALUES (%s, %s, %s, %s)
            ''', (prescription_id, medicine_name, dosage, frequency))

        db.commit()
        return jsonify({"msg": "Prescription added successfully", "prescription_id": prescription_id}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500

    finally:
        cur.close()
        db.close()

##########################################################
# EXECUTE PAYMENT
##########################################################
from flask import request, jsonify
from flask_jwt_extended import jwt_required
import psycopg2

@app.route('/dbproj/execute/payment', methods=['POST'])
@jwt_required()
def execute_payment():
    # Verifica se o pedido é JSON
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Extrai dados do JSON
    data = request.get_json()
    appointment_id = data.get('appointment_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')

    if not appointment_id or not amount or payment_method is None:
        return jsonify({"msg": "Missing required fields"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Insere o pagamento na tabela de pagamentos
        cur.execute('''
            INSERT INTO payments (amount, deadline_date, payment_method, appointments_hospitalizations_bills_appointment_id)
            VALUES (%s, NOW(), %s, %s) RETURNING payment_id
        ''', (amount, payment_method, appointment_id))
        payment_id = cur.fetchone()[0]
        db.commit()
        return jsonify({"msg": "Payment processed successfully", "payment_id": payment_id}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"msg": str(e)}), 500

    finally:
        cur.close()
        db.close()

##########################################################
# LIST TOP 3 PATIENTS
##########################################################
@app.route('/dbproj/top3/patients', methods=['GET'])
@jwt_required()
def top_three_patients():
    db = db_connection()
    cur = db.cursor()

    try:
        # Executa uma consulta SQL para encontrar os top 3 pacientes com mais compromissos
        cur.execute('''
            SELECT patient_person_username, COUNT(*) as total_appointments
            FROM appointments_hospitalizations_bills
            GROUP BY patient_person_username
            ORDER BY total_appointments DESC
            LIMIT 3
        ''')
        results = cur.fetchall()

        # Prepara a resposta
        top_patients = [
            {"patient_username": result[0], "total_appointments": result[1]}
            for result in results
        ]

        return jsonify(top_patients), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 500

    finally:
        cur.close()
        db.close()

##########################################################
# DAILY SUMMARY
##########################################################
@app.route('/dbproj/daily_summary', methods=['GET'])
@jwt_required()
def daily_summary():
    # Fetch the date from query parameters or use current date
    summary_date = request.args.get('date')

    if not summary_date:
        return jsonify({"msg": "Date is required for the daily summary"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Gathering summary data
        # Number of appointments
        cur.execute('''
            SELECT COUNT(*)
            FROM appointments_hospitalizations_bills
            WHERE CAST(appointment_date AS DATE) = %s
        ''', (summary_date,))
        appointments_count = cur.fetchone()[0]

        # Number of surgeries
        cur.execute('''
            SELECT COUNT(*)
            FROM surgeries
            WHERE CAST(start_time AS DATE) = %s
        ''', (summary_date,))
        surgeries_count = cur.fetchone()[0]

        # Number of prescriptions issued
        cur.execute('''
            SELECT COUNT(*)
            FROM prescriptions
            WHERE CAST(prescription_date AS DATE) = %s
        ''', (summary_date,))
        prescriptions_count = cur.fetchone()[0]

        # Total payments received
        cur.execute('''
            SELECT SUM(amount)
            FROM payments
            WHERE CAST(deadline_date AS DATE) = %s
        ''', (summary_date,))
        payments_total = cur.fetchone()[0] or 0  # Handle None if no payments

        # Compile the results into a single summary
        summary = {
            "date": summary_date,
            "total_appointments": appointments_count,
            "total_surgeries": surgeries_count,
            "total_prescriptions": prescriptions_count,
            "total_payments_received": payments_total
        }

        return jsonify(summary), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 500

    finally:
        cur.close()
        db.close()

##########################################################
# GENERATE A MONTHLY REPORT
##########################################################
@app.route('/dbproj/monthly_report', methods=['GET'])
@jwt_required()
def monthly_report():
    # Fetch the month and year from query parameters
    month = request.args.get('month')
    year = request.args.get('year')

    if not month or not year:
        return jsonify({"msg": "Both month and year are required for generating the monthly report"}), 400

    db = db_connection()
    cur = db.cursor()

    try:
        # Gathering data for the report
        # Number of appointments
        cur.execute('''
            SELECT COUNT(*)
            FROM appointments_hospitalizations_bills
            WHERE EXTRACT(MONTH FROM appointment_date) = %s AND EXTRACT(YEAR FROM appointment_date) = %s
        ''', (month, year))
        appointments_count = cur.fetchone()[0]

        # Number of surgeries
        cur.execute('''
            SELECT COUNT(*)
            FROM surgeries
            WHERE EXTRACT(MONTH FROM start_time) = %s AND EXTRACT(YEAR FROM start_time) = %s
        ''', (month, year))
        surgeries_count = cur.fetchone()[0]

        # Total payments received
        cur.execute('''
            SELECT SUM(amount)
            FROM payments
            WHERE EXTRACT(MONTH FROM deadline_date) = %s AND EXTRACT(YEAR FROM deadline_date) = %s
        ''', (month, year))
        payments_total = cur.fetchone()[0] or 0  # Handle None if no payments

        # Compile the results into a single report
        report = {
            "month": month,
            "year": year,
            "total_appointments": appointments_count,
            "total_surgeries": surgeries_count,
            "total_payments_received": payments_total
        }

        return jsonify(report), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 500

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
