
from flask_cors import CORS
from flask import Flask, request, jsonify   
import numpy as np
import math as math 

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
        return jsonify({"error": str(e)}), 400
    
app.route('/CapeCod', methods=['POST'])
def cap_cod():
    try: 
        data = request.get_json()
        year = data['year']
        Earned_Premiums = data['Earned_Premiums']
        CDF = data['CDF']
        reported_losses = data['report_loss']

        weighted_losses = np.array(reported_losses) / np.array(CDF)

        expected_ultimate_loss = weighted_losses * Earned_Premiums[year]

        IBNR = expected_ultimate_loss - reported_losses[year]

        return jsonify({
            "message": "Cape Cod method processed successfully",
            "IBNR": IBNR,
            "expected_ultimate_loss": expected_ultimate_loss.tolist(),
            }
        ), 200
    except Exception as e: 
        return jsonify({"error": str(e)}), 400
    
@app.route('/monte_carlo', methods=['POST'])
def monte_carlo():
    try:
        to_send = {}
        data = request.get_json()
        uncertainties = data['uncertainties']
        for x in uncertainties:
            to_send[x] = []
            for y in uncertainties[x]: ## for now only recongnizes normal lognormal poisson uniform
                if uncertainties[x][y]['type'] == 'normal':
                    mean = uncertainties[x][y]['mean']
                    std_dev = uncertainties[x][y]['std_dev']
                    samples = np.random.normal(mean, std_dev, 10000)
                elif uncertainties[x][y]['type'] == 'lognormal':
                    mean = uncertainties[x][y]['mean']
                    std_dev = uncertainties[x][y]['std_dev']
                    samples = np.random.lognormal(mean, std_dev, 10000)
                elif uncertainties[x][y]['type'] == 'poisson':
                    lam = uncertainties[x][y]['lambda']
                    samples = np.random.poisson(lam, 10000)
                elif uncertainties[x][y]['type'] == 'uniform':
                    low = uncertainties[x][y]['low']
                    high = uncertainties[x][y]['high']
                    samples = np.random.uniform(low, high, 10000)
                else:
                    return jsonify({"error": "Unsupported uncertainty type"}), 400
                Mean = np.mean(samples)
                std = np.std(samples)
                min_val = np.min(samples)
                max_val = np.max(samples)
                percentiles = np.percentile(samples, [5, 25, 50, 75, 95])
                to_send[x].append({
                    "type": uncertainties[x][y]['type'],
                    "mean": Mean,
                    "std_dev": std,
                    "min": min_val,
                    "max": max_val,
                    "percentiles": percentiles.tolist()
                })
        return jsonify({
            "message": "Monte Carlo simulation processed successfully",
            "results": to_send
        }), 200
                

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/mack_model', methods=['POST'])
def mack_model():
    try:
        data = request.get_json()
        claims_triangle = data['claims_triangle']
        year = data['year'] # 1 = 1st year, 2 = 2nd year, etc.
        months = data['months'] # 1 = 12 months, 2 = 24 months, etc.
        factors_link = []  
        accident_years_ultimate = []
        # Calculate link ratios
        for y in claims_triangle[0]:
            temp_num = 0
            temp_denom = 0
            for x in claims_triangle:
                if claims_triangle[x][y] is not None and claims_triangle[x][y+1] is not None:
                    temp_num += claims_triangle[x][y+1]
                    temp_denom += claims_triangle[x][y]
            factors_link[y] = temp_num / temp_denom if temp_denom != 0 else 0
        # Calculate ultimate claims for each accident year
        for x in range(len(claims_triangle)):
            c = len(claims_triangle) - x - 1
            linked_unfinished = claims_triangle[x][c]
            for y in range(c, len(factors_link)):
                linked_unfinished *= factors_link[y]
        accident_years_ultimate.append(linked_unfinished)
        # Latest reported claims
        latest_reported_claims = []
        for x in claims_triangle:
            latest = None
            for y in x:
                if y is not None:
                    latest = y
            latest_reported_claims.append(latest)
        # Calculate reserve             
        reserve = sum(accident_years_ultimate) - sum(latest_reported_claims)
        # Residuals
        for y in claims_triangle[0]:
            temporary = []
            i = 0
            for x in claims_triangle:
                if claims_triangle[x][y] is not None and claims_triangle[x][y+1]:
                    predicted = claims_triangle[x][y] * factors_link[y] 
                    residual = claims_triangle[x][y+1] - predicted
                    square = residual**2/claims_triangle[x][y]
                    temporary.append(square)
                    i+=1
            Variance_estimate = sum(temporary) / (i-1)
        # Variance of reserves
        variance_sum = 0
        for k in range(months, len((claims_triangle[0])-1)):
            if k == months:
                product = 1
            else:
                product = math.prod(factors_link[months:k])
            variance_sum += Variance_estimate[k] * product
        Calculated = latest_reported_claims[year]**2 *variance_sum
        # Return results
        return jsonify({
            "message": "Mack model processed successfully",
            "reserve": reserve,
            "variance": Calculated,
            "inputs": {
                "claims_triangle": claims_triangle,
                "year": year,
                "months": months
            }
        }), 200
            
    except Exception as e:  
        return jsonify({"error": str(e)}), 400 

if __name__ == '__main__':
    app.run(debug=True)