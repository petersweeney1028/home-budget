document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('budgetForm');
    const resultDiv = document.getElementById('result');
    const interestRateSlider = document.getElementById('interestRate');
    const interestRateValue = document.getElementById('interestRateValue');
    const hasTrustFundSelect = document.getElementById('hasTrustFund');
    const trustFundAmountGroup = document.getElementById('trustFundAmountGroup');

    interestRateSlider.addEventListener('input', function() {
        interestRateValue.textContent = this.value;
    });

    hasTrustFundSelect.addEventListener('change', function() {
        trustFundAmountGroup.style.display = this.value === 'yes' ? 'block' : 'none';
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        document.querySelectorAll('.error').forEach(el => el.textContent = '');
        
        const formData = {
            annualIncome: document.getElementById('annualIncome').value,
            totalSavings: document.getElementById('totalSavings').value,
            hasTrustFund: document.getElementById('hasTrustFund').value,
            trustFundAmount: document.getElementById('trustFundAmount').value,
            city: document.getElementById('city').value,
            interestRate: interestRateSlider.value
        };

        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.errors) {
                for (const [key, value] of Object.entries(data.errors)) {
                    const errorElement = document.getElementById(`${key}Error`);
                    if (errorElement) {
                        errorElement.textContent = value;
                    }
                }
                resultDiv.innerHTML = '';
            } else {
                resultDiv.innerHTML = `
                    <h2>Home Buying Budget Estimate</h2>
                    <p>Recommended home price: $${data.homePrice.toLocaleString()}</p>
                    
                    <h3>Down Payment Breakdown</h3>
                    <ul>
                        <li>Required Down Payment (20%): $${data.downPayment.required.toLocaleString()}</li>
                        <li>Down Payment from Savings: $${data.downPayment.from_savings.toLocaleString()}</li>
                        <li>Down Payment from Income: $${data.downPayment.from_income.toLocaleString()}</li>
                        <li>Down Payment from Trust Fund: $${data.downPayment.from_trust.toLocaleString()}</li>
                        <li><strong>Total Down Payment: $${data.downPayment.total.toLocaleString()}</strong></li>
                        ${data.downPayment.shortfall > 0 ? `<li class="text-danger">Shortfall: $${data.downPayment.shortfall.toLocaleString()}</li>` : ''}
                    </ul>
                    
                    <h3>Monthly Costs Breakdown</h3>
                    <ul>
                        <li>Mortgage (P&I): $${data.monthlyCosts.mortgage.toLocaleString()}</li>
                        <li>Property Tax: $${data.monthlyCosts.property_tax.toLocaleString()}</li>
                        <li>Homeowners Insurance: $${data.monthlyCosts.insurance.toLocaleString()}</li>
                        <li>HOA Fees: $${data.monthlyCosts.hoa.toLocaleString()}</li>
                        <li>Trust Fund Credit: -$${data.monthlyCosts.trust_fund_credit.toLocaleString()}</li>
                        <li><strong>Total Monthly Payment: $${data.monthlyCosts.total.toLocaleString()}</strong></li>
                    </ul>
                    
                    <h3>Assumptions Used</h3>
                    <ul>
                        <li>Annual Income: $${formData.annualIncome}</li>
                        <li>Total Savings: $${formData.totalSavings}</li>
                        <li>Trust Fund: ${formData.hasTrustFund === 'yes' ? '$' + formData.trustFundAmount : 'None'}</li>
                        <li>City: ${formData.city}</li>
                        <li>Interest Rate: ${formData.interestRate}%</li>
                        <li>Property Tax Rate: ${(data.monthlyCosts.property_tax * 12 / data.homePrice * 100).toFixed(2)}%</li>
                        <li>Homeowners Insurance: 0.3% of home price annually</li>
                        <li>HOA Fees: $${data.monthlyCosts.hoa} per month</li>
                    </ul>
                    
                    <h3>Explanation</h3>
                    <p>This estimate is based on a calculation that takes into account your annual income, total savings, trust fund (if applicable), the selected city's cost of living, current interest rates, property taxes, homeowners insurance, and HOA fees.</p>
                    <p>The recommended home price is calculated as a multiple of your annual income, adjusted for local market conditions and available funds.</p>
                    <p>The down payment is calculated assuming a 20% requirement. It first uses your total savings, then considers your annual income (up to 20% of annual income), and finally uses the trust fund if applicable.</p>
                    <p>The monthly costs breakdown includes the mortgage payment (principal and interest), property taxes, homeowners insurance, and HOA fees specific to the selected city.</p>
                    ${formData.hasTrustFund === 'yes' ? `
                    <p><strong>Trust Fund Calculation:</strong> ${
                        parseInt(formData.trustFundAmount) >= 1000000 ?
                        `Your trust fund of $${parseInt(formData.trustFundAmount).toLocaleString()} is being used to supplement your monthly payments. We've calculated a 4% annual return on your trust fund, which contributes up to the total monthly payment amount as a credit.` :
                        `Your trust fund of $${parseInt(formData.trustFundAmount).toLocaleString()} is less than $1,000,000, so it's not included in the monthly payment calculations. However, it has been applied to the down payment calculation if needed.`
                    }</p>
                    ` : ''}
                    <p><strong>Note:</strong> This is an estimate intended for initial planning purposes only. For a more accurate assessment of your home buying budget, please consult with a financial advisor and a local real estate professional who can provide personalized advice based on your specific financial situation and local market conditions.</p>
                `;
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            resultDiv.innerHTML = '<p>An error occurred. Please try again later.</p>';
        });
    });
});
