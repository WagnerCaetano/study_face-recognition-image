import os
import boto3
from botocore.config import Config
from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import pytz

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='./')
CORS(app)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET = os.getenv('BUCKET')
BRAZIL = 'sa-east-1'
REKOGNITION_REGION = 'us-east-1'
TABLE_NAME_ALUNO = os.getenv('TABLE_NAME_ALUNO')
TABLE_NAME_CALENDARIO = os.getenv('TABLE_NAME_CALENDARIO')
WEEK_DAYS_MAP = {
    "monday": "segunda",
    "tuesday": "terça",
    "wednesday": "quarta",
    "thursday": "quinta",
    "friday": "sexta",
    "saturday": "sábado",
    "sunday": "domingo"
}

s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=BRAZIL)
dynamodb_resource = boto3.resource('dynamodb',
                                   aws_access_key_id=AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                   region_name=BRAZIL)
rekognition_client = boto3.client('rekognition',
                                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                  region_name=REKOGNITION_REGION,
                                  config=Config(region_name=REKOGNITION_REGION))


def doesTodayHaveClasses():
    table = dynamodb_resource.Table(TABLE_NAME_CALENDARIO)

    # Get the current day of the week
    today = datetime.now(pytz.timezone(
        'America/Sao_Paulo')).strftime('%A').lower()
    today = WEEK_DAYS_MAP[today]
    response = table.get_item(
        Key={
            'lista-dias-aulas': today
        }
    )
    class_schedule = response.get('Item')

    return class_schedule


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/photos', methods=['POST'])
def face_comparison():
    try:
        classesToday = doesTodayHaveClasses()
        if classesToday is not None:
            class_time = datetime.strptime(classesToday['horario'], '%H:%M').replace(
                tzinfo=pytz.timezone('America/Sao_Paulo'))
            current_time = datetime.now(pytz.timezone('America/Sao_Paulo'))
            if True:
                file = request.files.get('file')
                file_data = file.read()
                print(file_data)
                listImages = s3_client.list_objects(Bucket=BUCKET)['Contents']
                match = False
                personDetectMatricula = ""
                for image in listImages:
                    if ".jpg" in image['Key']:
                        response = s3_client.get_object(
                            Bucket=BUCKET, Key=image['Key'])
                        target_image_data = response['Body'].read()

                        response = rekognition_client.compare_faces(SimilarityThreshold=80,
                                                                    SourceImage={
                                                                        'Bytes': file_data},
                                                                    TargetImage={
                                                                        'Bytes': target_image_data})
                        if len(response['FaceMatches']) > 0 and response['FaceMatches'][0]['Similarity'] >= 80:
                            match = True
                            personDetectMatricula = image['Key'].split("/")[1].split(".")[
                                0]
                            break
                if not match:
                    return jsonify({'message': "Nao foi possivel identificar", "status": 400})
                else:
                    table = dynamodb_resource.Table(TABLE_NAME_ALUNO)
                    response = table.get_item(
                        Key={
                            'matricula': personDetectMatricula
                        }
                    )
                    student = response['Item']

                    if not student:
                        # No students found
                        raise StudentsNotFoundException("No students found")

                    # Perform attendance check for each student
                    history = student['historico']
                    today = datetime.now(pytz.timezone(
                        'America/Sao_Paulo')).strftime('%d/%m/%Y')

                    # Check if attendance record exists for today
                    attendance_exists = False
                    for entry in history:
                        if entry['data'] == today:
                            attendance_exists = True
                            break

                    # Update attendance record if absent
                    if not attendance_exists:
                        new_entry = {
                            "data": today,
                            "dia": WEEK_DAYS_MAP[datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%A').lower()],
                            "hora": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M'),
                            "id_historico": str(len(history) + 1),
                            "presente": True
                        }
                        history.append(new_entry)

                        # Update the student's attendance record in the database
                        table.update_item(
                            Key={
                                'matricula': student['matricula']
                            },
                            UpdateExpression="SET historico = :h",
                            ExpressionAttributeValues={
                                ":h": history
                            }
                        )
                        return jsonify({'message': "Presente:", "matricula": personDetectMatricula, "status": 201})
                    else:
                        return jsonify({'message': "Ja esta presente", "status": 200})
            return jsonify({'message': "Ja foi o tempo de marcar presença", "status": 409})
        return jsonify({'message': "Nao ha aulas hoje", "status": 404})

    except Exception as e:
        print(e)
        return jsonify({'message': str(e), "status": 500})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
