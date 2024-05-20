from flask import Flask, jsonify
import logging
import psycopg2

app = Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
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

@app.route('/')
def landing_page():
    return """

    Welcome to the Hospital Management System!  <br/>
    <br/>
    BD 2023-2024 Project<br/>
    <br/>
    """


##########################################################
# SCHEDULE APPOINTMENT
##########################################################
@app.route('/appointments', methods=['POST'])
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
