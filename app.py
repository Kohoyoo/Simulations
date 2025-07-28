
from flask_cors import CORS
from flask import Flask, request, jsonify   

app = Flask(__name__)
CORS(app)

@app.route('/bf_simulation', methods=['POST'])
def bf_simulation():
    try:
        # get JSON payload
        data = request.get_json()
        print('Received /bf_simulation payload:', data)
        ELR = data['ELR']
        RL = data['RL']
        LDF = data['LDF']
        EL = data.get('EL')
        Premium_Earned = data['Premium_Earned']

        if EL is None:
            EL = Premium_Earned * ELR

        BF = RL + (Premium_Earned * ELR * (1 - 1/LDF))

        return jsonify({
            "message": "Simulation processed successfully",
            "BF": BF,
            "formula": "BF = RL + (Premium_Earned * ELR * (1 - 1/LDF))",
            "inputs": {
                "RL": RL,
                "Premium_Earned": Premium_Earned,
                "ELR": ELR,
                "LDF": LDF,
                "EL": EL
            }
        }), 200
    except Exception as e:
        print('Error in /bf_simulation:', str(e))
        return jsonify({"error": str(e)}), 400
    
    app.route('/')