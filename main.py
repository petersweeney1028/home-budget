from flask import Flask, render_template, request, jsonify
import math

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

def calculate_max_home_price(max_monthly_payment, interest_rate, city, trust_fund_amount):
    annual_interest_rate = interest_rate / 100
    monthly_interest_rate = annual_interest_rate / 12
    loan_term_months = 30 * 12

    property_tax_rate = PROPERTY_TAX_RATES[city]
    monthly_hoa = HOA_FEES[city]

    # Calculate trust fund monthly return
    trust_fund_monthly_return = (trust_fund_amount * 0.04) / 12 if trust_fund_amount >= 1000000 else 0

    # Adjust max_monthly_payment to include trust fund return
    adjusted_max_monthly_payment = max_monthly_payment + trust_fund_monthly_return

    # Calculate the maximum loan amount
    max_loan_amount = (adjusted_max_monthly_payment * (1 - (1 + monthly_interest_rate) ** -loan_term_months)) / monthly_interest_rate

    # Calculate max home price (assuming 20% down payment)
    max_home_price = max_loan_amount / 0.8

    # Adjust for property tax, insurance, and HOA
    monthly_costs = (max_home_price * property_tax_rate / 12) + (max_home_price * 0.003 / 12) + monthly_hoa
    while (max_home_price * 0.8 * monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / ((1 + monthly_interest_rate) ** loan_term_months - 1) + monthly_costs - trust_fund_monthly_return > max_monthly_payment:
        max_home_price *= 0.99

    return max_home_price

def calculate_monthly_costs(home_price, city, interest_rate, trust_fund_amount, down_payment_info):
    annual_interest_rate = interest_rate / 100
    monthly_interest_rate = annual_interest_rate / 12
    loan_term_months = 30 * 12

    loan_amount = home_price * 0.8  # Assuming 20% down payment
    monthly_mortgage = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months) / ((1 + monthly_interest_rate) ** loan_term_months - 1)

    monthly_property_tax = (home_price * PROPERTY_TAX_RATES[city]) / 12
    monthly_insurance = (home_price * 0.003) / 12
    monthly_hoa = HOA_FEES[city]

    total_monthly = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_hoa

    remaining_trust_fund = down_payment_info['remaining_trust_fund']
    trust_fund_credit = 0
    if remaining_trust_fund >= 1000000:
        monthly_interest = (remaining_trust_fund * 0.04) / 12
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

def calculate_down_payment(home_price, total_savings, trust_fund_amount):
    required_down_payment = home_price * 0.2
    max_savings_for_down_payment = total_savings * 0.35

    down_payment_from_savings = min(max_savings_for_down_payment, required_down_payment)
    remaining_down_payment = required_down_payment - down_payment_from_savings

    down_payment_from_trust = min(trust_fund_amount, remaining_down_payment)
    remaining_trust_fund = trust_fund_amount - down_payment_from_trust

    total_down_payment = down_payment_from_savings + down_payment_from_trust
    shortfall = max(0, required_down_payment - total_down_payment)

    return {
        "total": round(total_down_payment, 2),
        "from_savings": round(down_payment_from_savings, 2),
        "from_trust": round(down_payment_from_trust, 2),
        "shortfall": round(shortfall, 2),
        "required": round(required_down_payment, 2),
        "remaining_trust_fund": round(remaining_trust_fund, 2)
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
    
    annual_income = int(data['annualIncome'])
    total_savings = int(data['totalSavings'])
    city = data['city']
    interest_rate = float(data['interestRate'])

    monthly_income = annual_income / 12
    max_monthly_payment = monthly_income * 0.28

    max_home_price_monthly = calculate_max_home_price(max_monthly_payment, interest_rate, city, trust_fund_amount)
    max_down_payment = (total_savings * 0.35) + trust_fund_amount
    max_home_price_down_payment = max_down_payment / 0.2

    home_price = min(max_home_price_monthly, max_home_price_down_payment)

    down_payment = calculate_down_payment(home_price, total_savings, trust_fund_amount)
    monthly_costs = calculate_monthly_costs(home_price, city, interest_rate, trust_fund_amount, down_payment)

    price_determination = "monthly payment limit" if home_price == max_home_price_monthly else "down payment limit"

    return jsonify({
        "homePrice": round(home_price, 2),
        "monthlyCosts": monthly_costs,
        "downPayment": down_payment,
        "priceDetermination": price_determination
    })

def test_calculation():
    annual_income = 250000
    total_savings = 250000
    trust_fund_amount = 5000000
    city = "NYC"
    interest_rate = 6

    print(f"Test Calculation Inputs:")
    print(f"Annual Income: ${annual_income:,}")
    print(f"Total Savings: ${total_savings:,}")
    print(f"Trust Fund Amount: ${trust_fund_amount:,}")
    print(f"City: {city}")
    print(f"Interest Rate: {interest_rate}%")
    print("\nCalculation Process:")

    monthly_income = annual_income / 12
    max_monthly_payment = monthly_income * 0.28
    print(f"Monthly Income: ${monthly_income:,.2f}")
    print(f"Max Monthly Payment (28% of monthly income): ${max_monthly_payment:,.2f}")

    max_home_price_monthly = calculate_max_home_price(max_monthly_payment, interest_rate, city, trust_fund_amount)
    print(f"\nMax home price based on monthly payment (including trust fund return): ${max_home_price_monthly:,.2f}")

    max_down_payment = (total_savings * 0.35) + trust_fund_amount
    max_home_price_down_payment = max_down_payment / 0.2
    print(f"Max down payment (35% of savings + trust fund): ${max_down_payment:,.2f}")
    print(f"Max home price based on down payment: ${max_home_price_down_payment:,.2f}")

    home_price = min(max_home_price_monthly, max_home_price_down_payment)
    print(f"\nFinal recommended home price: ${home_price:,.2f}")

    down_payment = calculate_down_payment(home_price, total_savings, trust_fund_amount)
    monthly_costs = calculate_monthly_costs(home_price, city, interest_rate, trust_fund_amount, down_payment)

    print(f"\nMonthly Costs Breakdown:")
    for key, value in monthly_costs.items():
        print(f"  {key.capitalize()}: ${value:,.2f}")
    
    print(f"\nDown Payment Breakdown:")
    for key, value in down_payment.items():
        print(f"  {key.capitalize()}: ${value:,.2f}")

if __name__ == "__main__":
    print("Running test calculation...")
    test_calculation()
    print("\nStarting Flask server...")
    app.run(host="0.0.0.0", port=5000)
