from flask import Flask, request, jsonify
import psycopg2
import openai
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='Students',  # Change this to your database name
            user='postgres',  # Your PostgreSQL username
            password='12345'  # Your PostgreSQL password
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")

# Get all students
@app.route('/api/students', methods=['GET'])
def get_all_students():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute('SELECT * FROM students')
        students = cur.fetchall()

        if not students:
            return jsonify({'message': 'No students found'}), 404

        return jsonify(students), 200
    except Exception as e:
        return jsonify({'error': f"Error fetching students: {e}"}), 500
    finally:
        cur.close()
        conn.close()

# Get a specific student by ID
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute('SELECT * FROM students WHERE id = %s', (id,))
        student = cur.fetchone()

        if student is None:
            return jsonify({'error': f'No student found with ID {id}'}), 404

        return jsonify(student), 200
    except Exception as e:
        return jsonify({'error': f"Error fetching student: {e}"}), 500
    finally:
        cur.close()
        conn.close()

# Add a new student
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()

    if not data or 'name' not in data or 'grade' not in data:
        return jsonify({'error': 'Missing required fields: name or grade'}), 400

    name = data['name']
    grade = data['grade']

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('INSERT INTO students (name, grade) VALUES (%s, %s) RETURNING id', (name, grade))
        new_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({'message': 'Student added successfully', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': f"Error adding student: {e}"}), 500
    finally:
        cur.close()
        conn.close()

# Update a student's information
@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json()

    if not data or 'name' not in data or 'grade' not in data:
        return jsonify({'error': 'Missing required fields: name or grade'}), 400

    name = data['name']
    grade = data['grade']

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('UPDATE students SET name = %s, grade = %s WHERE id = %s', (name, grade, id))

        if cur.rowcount == 0:
            return jsonify({'error': f'No student found with ID {id}'}), 404

        conn.commit()
        return jsonify({'message': f'Student with ID {id} updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f"Error updating student: {e}"}), 500
    finally:
        cur.close()
        conn.close()

# Partially update a student's information (PATCH)
@app.route('/api/students/<int:id>', methods=['PATCH'])
def patch_student(id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided for update'}), 400

    updates = []
    if 'name' in data:
        updates.append(('name', data['name']))
    if 'grade' in data:
        updates.append(('grade', data['grade']))

    if not updates:
        return jsonify({'error': 'No fields provided for update'}), 400

    update_query = ', '.join(f"{col} = %s" for col, _ in updates)
    values = [val for _, val in updates] + [id]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"UPDATE students SET {update_query} WHERE id = %s", values)

        if cur.rowcount == 0:
            return jsonify({'error': f'No student found with ID {id}'}), 404

        conn.commit()
        return jsonify({'message': f'Student with ID {id} updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Error updating student: {e}"}), 500
    finally:
        cur.close()
        conn.close()

# Delete a student by ID
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM students WHERE id = %s", (id,))

        if cur.rowcount == 0:
            return jsonify({'error': f'No student found with ID {id}'}), 404

        conn.commit()
        return jsonify({'message': f'Student with ID {id} deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Error deleting student: {e}"}), 500
    finally:
        cur.close()
        conn.close()
        
        
@app.route('/api/chatgpt', methods=['POST'])
def chatgpt():
    app.logger.setLevel('DEBUG')  

    data = request.get_json()

    if not data:
        app.logger.error("No JSON data received")
        return jsonify({'error': 'No JSON data received'}), 400

    if 'prompt' not in data:
        app.logger.error("Missing required field: prompt")
        return jsonify({'error': 'Missing required field: prompt'}), 400

    prompt = data['prompt']
    app.logger.info(f"Received prompt: {prompt}")

    try:
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        generated_message = response['choices'][0]['message']['content']
        return jsonify({'message': generated_message}), 200

    except Exception as e:
        app.logger.error(f"Error during OpenAI API call: {e}")
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500

