import os
import boto3
from botocore.config import Config
from flask_cors import CORS
from flask import Flask, request, jsonify

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET = os.getenv('BUCKET')
S3_REGION = 'sa-east-1'
REKOGNITION_REGION = 'us-east-1'

s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=S3_REGION)
rekognition_client = boto3.client('rekognition',
                                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                  region_name=REKOGNITION_REGION,
                                  config=Config(region_name=REKOGNITION_REGION))


@app.route('/photo', methods=['POST'])
def face_comparison():
    try:
        file = request.files.get('file')
        type(file)
        print(file)
        file_data = file.read()

        user_id = request.args.get('userId')

        s3_object_key = f'{user_id}.jpg'

        response = s3_client.get_object(
            Bucket=BUCKET, Key='public/' + s3_object_key)
        target_image_data = response['Body'].read()
        print(type(file_data))
        print(type(target_image_data))

        response = rekognition_client.compare_faces(SimilarityThreshold=80,
                                                    SourceImage={
                                                        'Bytes': file_data},
                                                    TargetImage={
                                                        'Bytes': target_image_data})

        if len(response['FaceMatches']) == 0:
            return jsonify({'error': 'No matches found'})

        similarity = response['FaceMatches'][0]['Similarity']

        return jsonify({'Similarity': similarity})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()
