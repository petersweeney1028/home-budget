from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

def calculate_home_price(annual_income, has_trust_fund, trust_fund_amount, city, interest_rate):
    base_price = annual_income * 4
    
    city_factors = {
        "NYC": 2.0,
        "Greenwich CT": 1.8,
        "Nassau County": 1.6,
        "Ridgewood NJ": 1.5,
        "Summit NJ": 1.7
    }
    
    city_factor = city_factors.get(city, 1.0)
    
    adjusted_price = base_price * city_factor * (1 - (interest_rate / 100))
    
    return round(adjusted_price, 2)

def calculate_monthly_costs(home_price, city, interest_rate, trust_fund_amount):
    monthly_mortgage = (home_price * (interest_rate / 100 / 12)) / (1 - (1 + (interest_rate / 100 / 12)) ** -360)
    monthly_property_tax = (home_price * PROPERTY_TAX_RATES[city]) / 12
    monthly_insurance = (home_price * 0.003) / 12
    monthly_hoa = HOA_FEES[city]
    
    total_monthly = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_hoa
    
    trust_fund_credit = 0
    if trust_fund_amount >= 1000000:
        monthly_interest = (trust_fund_amount * 0.04) / 12
        trust_fund_credit = min(monthly_interest, total_monthly)
        total_monthly -= trust_fund_credit
    
    return {
        "mortgage": round(monthly_mortgage, 2),
        "property_tax": round(monthly_property_tax, 2),
        "insurance": round(monthly_insurance, 2),
        "hoa": monthly_hoa,
        "trust_fund_credit": round(trust_fund_credit, 2),
        "total": round(total_monthly, 2)
    }

def calculate_down_payment(home_price, annual_income, total_savings, trust_fund_amount):
    required_down_payment = home_price * 0.2
    
    max_savings_for_down_payment = min(total_savings * 0.2, required_down_payment)
    down_payment_from_savings = min(max_savings_for_down_payment, required_down_payment)
    remaining_down_payment = required_down_payment - down_payment_from_savings
    
    down_payment_from_income = min(annual_income * 0.2, remaining_down_payment)
    remaining_down_payment -= down_payment_from_income
    
    down_payment_from_trust = 0
    if trust_fund_amount < 1000000:
        down_payment_from_trust = min(trust_fund_amount, remaining_down_payment)
    else:
        down_payment_from_trust = min(trust_fund_amount * 0.2, remaining_down_payment)
    
    total_down_payment = down_payment_from_savings + down_payment_from_income + down_payment_from_trust
    shortfall = max(0, required_down_payment - total_down_payment)
    
    return {
        "total": round(total_down_payment, 2),
        "from_savings": round(down_payment_from_savings, 2),
        "from_income": round(down_payment_from_income, 2),
        "from_trust": round(down_payment_from_trust, 2),
        "shortfall": round(shortfall, 2),
        "required": round(required_down_payment, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    
    errors = {}
    
    if not data.get('annualIncome') or not data['annualIncome'].isdigit():
        errors['annualIncome'] = "Please enter a valid annual income."
    
    if not data.get('totalSavings') or not data['totalSavings'].isdigit():
        errors['totalSavings'] = "Please enter a valid total savings amount."
    
    has_trust_fund = data.get('hasTrustFund') == 'yes'
    trust_fund_amount = 0
    if has_trust_fund:
        if not data.get('trustFundAmount') or not data['trustFundAmount'].isdigit():
            errors['trustFundAmount'] = "Please enter a valid trust fund amount."
        else:
            trust_fund_amount = int(data['trustFundAmount'])
    
    if not data.get('city') or data['city'] not in VALID_CITIES:
        errors['city'] = "Please select a valid city."
    
    try:
        interest_rate = float(data.get('interestRate', ''))
        if interest_rate < 5.5 or interest_rate > 15:
            raise ValueError
    except ValueError:
        errors['interestRate'] = "Please enter a valid interest rate between 5.5% and 15%."
    
    if errors:
        return jsonify({"errors": errors}), 400
    
    home_price = calculate_home_price(
        int(data['annualIncome']),
        has_trust_fund,
        trust_fund_amount,
        data['city'],
        float(data['interestRate'])
    )
    
    monthly_costs = calculate_monthly_costs(
        home_price,
        data['city'],
        float(data['interestRate']),
        trust_fund_amount
    )
    
    down_payment = calculate_down_payment(
        home_price,
        int(data['annualIncome']),
        int(data['totalSavings']),
        trust_fund_amount
    )
    
    return jsonify({
        "homePrice": home_price,
        "monthlyCosts": monthly_costs,
        "downPayment": down_payment
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
