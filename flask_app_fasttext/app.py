import fasttext
import os
from flask import Flask, jsonify, request
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

# This is what you get when you do model.save_model("model_fasttext.bin")
model = fasttext.load_model('model_fasttext.bin')

class MakePrediction(Resource):
    @staticmethod
    def post():
        posted_data = request.get_json()
        txn_desc = posted_data['transaction_description']

        prediction = model.predict([txn_desc])
        print(prediction)

        return jsonify({
            'Prediction': prediction[0][0][0].split('__')[2],
            'Prediction probability': str(prediction[1][0][0])
        })

api.add_resource(MakePrediction, '/predict')


if __name__ == '__main__':
    app.run(debug=True)