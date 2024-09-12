from flask import Flask, render_template, request, jsonify, session
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key in production

VALID_CITIES = ["NYC", "Greenwich CT", "Nassau County", "Ridgewood NJ", "Summit NJ"]

PROPERTY_TAX_RATES = {
    "NYC": 0.009,
    "Greenwich CT": 0.011,
    "Nassau County": 0.021,
    "Ridgewood NJ": 0.025,
    "Summit NJ": 0.024
}

HOA_FEES = {
    "NYC": 1000,
    "Greenwich CT": 400,
    "Nassau County": 300,
    "Ridgewood NJ": 250,
    "Summit NJ": 200
}

def calculate_max_home_price(max_monthly_payment, interest_rate, city, trust_fund_amount, total_savings):
    annual_interest_rate = interest_rate / 100
    monthly_interest_rate = annual_interest_rate / 12
    loan_term_months = 30 * 12

    property_tax_rate = PROPERTY_TAX_RATES[city]
    monthly_hoa = HOA_FEES[city]

    # Calculate trust fund monthly return
    trust_fund_monthly_return = (trust_fund_amount * 0.04) / 12 if trust_fund_amount >= 1000000 else 0

    # Adjust max_monthly_payment to include trust fund return
    adjusted_max_monthly_payment = max_monthly_payment + trust_fund_monthly_return

    # Calculate the maximum loan amount based on monthly payment
    max_loan_amount = (adjusted_max_monthly_payment * (1 - (1 + monthly_interest_rate) ** -loan_term_months)) / monthly_interest_rate

    # Calculate max home price based on monthly payment (assuming 20% down payment)
    max_price_monthly = max_loan_amount / 0.8

    # Calculate max home price based on down payment
    max_price_down_payment = (total_savings + trust_fund_amount) / 0.2

    # Determine the limiting factor
    if max_price_monthly <= max_price_down_payment:
        limiting_factor = "monthly payment"
        max_home_price = max_price_monthly
    else:
        limiting_factor = "down payment"
        max_home_price = max_price_down_payment

    # Adjust for property tax, insurance, and HOA
    monthly_costs = (max_home_price * property_tax_rate / 12) + (max_home_price * 0.003 / 12) + monthly_hoa
    while (max_home_price * 0.8 * monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / ((1 + monthly_interest_rate) ** loan_term_months - 1) + monthly_costs - trust_fund_monthly_return > max_monthly_payment:
        max_home_price *= 0.99

    return max_home_price, limiting_factor

def calculate_monthly_costs(home_price, city, interest_rate, trust_fund_amount, down_payment):
    annual_interest_rate = interest_rate / 100
    monthly_interest_rate = annual_interest_rate / 12
    loan_term_months = 30 * 12
    loan_amount = home_price * 0.8

    mortgage_payment = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / ((1 + monthly_interest_rate) ** loan_term_months - 1)
    property_tax = (home_price * PROPERTY_TAX_RATES[city]) / 12
    insurance = (home_price * 0.003) / 12
    hoa = HOA_FEES[city]
    remaining_trust_fund = trust_fund_amount - down_payment['from_trust']
    trust_fund_credit = (remaining_trust_fund * 0.04) / 12 if remaining_trust_fund >= 1000000 else 0

    total = mortgage_payment + property_tax + insurance + hoa - trust_fund_credit

    return {
        "mortgage": round(mortgage_payment, 2),
        "property_tax": round(property_tax, 2),
        "insurance": round(insurance, 2),
        "hoa": hoa,
        "trust_fund_credit": round(trust_fund_credit, 2),
        "total": round(total, 2)
    }

def calculate_down_payment(home_price, total_savings, trust_fund_amount):
    required = home_price * 0.2
    max_from_savings = min(total_savings * 0.35, required)
    from_savings = min(max_from_savings, required)
    remaining_required = required - from_savings
    
    max_from_trust = min(trust_fund_amount * 0.2, remaining_required)
    from_trust = min(max_from_trust, remaining_required)
    
    total_down_payment = from_savings + from_trust
    shortfall = max(0, required - total_down_payment)
    
    return {
        "total": round(total_down_payment, 2),
        "from_savings": round(from_savings, 2),
        "from_trust": round(from_trust, 2),
        "shortfall": round(shortfall, 2),
        "required": round(required, 2),
        "remaining_trust_fund": round(trust_fund_amount - from_trust, 2),
        "remaining_savings": round(total_savings - from_savings, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    
    # Calculate max monthly payment
    annual_income = float(data['annualIncome'])
    max_monthly_payment = (annual_income / 12) * 0.28
    
    # Convert interest rate to float
    interest_rate = float(data['interestRate'])
    
    # Convert trust fund amount to float if it exists
    trust_fund_amount = float(data['trustFundAmount']) if data['hasTrustFund'] == 'yes' else 0
    
    # Convert total savings to float
    total_savings = float(data['totalSavings'])
    
    home_price, limiting_factor = calculate_max_home_price(max_monthly_payment, interest_rate, data['city'], trust_fund_amount, total_savings)
    down_payment = calculate_down_payment(home_price, total_savings, trust_fund_amount)
    monthly_costs = calculate_monthly_costs(home_price, data['city'], interest_rate, trust_fund_amount, down_payment)
    
    result = {
        "homePrice": round(home_price, 2),
        "monthlyCosts": monthly_costs,
        "downPayment": down_payment,
        "limitingFactor": limiting_factor,
        "assumptions": {
            "Property Tax Rate": f"{PROPERTY_TAX_RATES[data['city']] * 100:.2f}%",
            "Insurance Rate": "0.3% of home value annually",
            "HOA Fee": f"${HOA_FEES[data['city']]} per month",
            "Loan Term": "30 years",
            "Down Payment": "20% of home price"
        },
        "explanations": [
            "The maximum home price is calculated based on your monthly income and other financial factors.",
            f"We assume a {PROPERTY_TAX_RATES[data['city']] * 100:.2f}% annual property tax rate for {data['city']}.",
            "Homeowners insurance is estimated at 0.3% of the home value annually.",
            f"HOA fees for {data['city']} are estimated at ${HOA_FEES[data['city']]} per month.",
            "We assume a 30-year fixed-rate mortgage with a 20% down payment.",
            "The maximum monthly housing cost is calculated as 28% of your gross monthly income."
        ]
    }
    
    # Generate a unique ID for this scenario
    scenario_id = str(uuid.uuid4())
    
    # Store the scenario in the session
    if 'scenarios' not in session:
        session['scenarios'] = {}
    session['scenarios'][scenario_id] = {
        "inputs": data,
        "result": result
    }
    session.modified = True
    
    return jsonify({**result, "scenarioId": scenario_id})

@app.route('/scenarios', methods=['GET', 'POST'])
def scenarios():
    if request.method == 'GET':
        return jsonify(session.get('scenarios', {}))
    elif request.method == 'POST':
        data = request.json
        scenario_id = str(uuid.uuid4())
        if 'scenarios' not in session:
            session['scenarios'] = {}
        session['scenarios'][scenario_id] = data
        session.modified = True
        return jsonify({"message": "Scenario saved successfully", "scenarioId": scenario_id})

@app.route('/scenario/<scenario_id>', methods=['GET', 'DELETE'])
def scenario(scenario_id):
    if request.method == 'GET':
        scenario = session.get('scenarios', {}).get(scenario_id)
        if scenario:
            return jsonify(scenario)
        return jsonify({"error": "Scenario not found"}), 404
    elif request.method == 'DELETE':
        if 'scenarios' in session and scenario_id in session['scenarios']:
            del session['scenarios'][scenario_id]
            session.modified = True
            return jsonify({"message": "Scenario deleted successfully"})
        return jsonify({"error": "Scenario not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
