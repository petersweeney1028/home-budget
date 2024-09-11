document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('budgetForm');
    const resultDiv = document.getElementById('result');
    const interestRateSlider = document.getElementById('interestRate');
    const interestRateValue = document.getElementById('interestRateValue');
    const hasTrustFundSelect = document.getElementById('hasTrustFund');
    const trustFundAmountGroup = document.getElementById('trustFundAmountGroup');
    let monthlyCostsChart = null;

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
                    <p>This price was determined by the ${data.priceDetermination}.</p>
                    
                    <h3>Down Payment Breakdown</h3>
                    <ul>
                        <li>Required Down Payment (20%): $${data.downPayment.required.toLocaleString()}</li>
                        <li>Down Payment from Savings: $${data.downPayment.from_savings.toLocaleString()}</li>
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
                    <p>The recommended home price is calculated as the lower of two values:</p>
                    <ol>
                        <li>The maximum home price based on a monthly payment limit of 28% of your monthly income.</li>
                        <li>The maximum home price based on a down payment limit of 35% of your total savings plus your trust fund amount (if applicable).</li>
                    </ol>
                    <p>The down payment is calculated as 20% of the home price, using up to 35% of your total savings and your trust fund amount if needed.</p>
                    <p>The monthly costs breakdown includes the mortgage payment (principal and interest), property taxes, homeowners insurance, and HOA fees specific to the selected city.</p>
                    ${formData.hasTrustFund === 'yes' ? `
                    <p><strong>Trust Fund Calculation:</strong> ${
                        parseInt(formData.trustFundAmount) >= 1000000 ?
                        `Your trust fund of $${parseInt(formData.trustFundAmount).toLocaleString()} is being used to supplement your monthly payments. We've calculated a 4% annual return on your trust fund, which contributes up to the total monthly payment amount as a credit.` :
                        `Your trust fund of $${parseInt(formData.trustFundAmount).toLocaleString()} is included in the down payment calculation.`
                    }</p>
                    ` : ''}
                    <p><strong>Note:</strong> This is an estimate intended for initial planning purposes only. For a more accurate assessment of your home buying budget, please consult with a financial advisor and a local real estate professional who can provide personalized advice based on your specific financial situation and local market conditions.</p>
                `;

                // Create or update the monthly costs chart
                createMonthlyCostsChart(data.monthlyCosts);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            resultDiv.innerHTML = '<p>An error occurred. Please try again later.</p>';
        });
    });

    function createMonthlyCostsChart(monthlyCosts) {
        const ctx = document.getElementById('monthlyCostsChart').getContext('2d');
        
        // Prepare data for the chart
        const chartData = {
            labels: ['Mortgage (P&I)', 'Property Tax', 'Homeowners Insurance', 'HOA Fees'],
            datasets: [{
                data: [
                    monthlyCosts.mortgage,
                    monthlyCosts.property_tax,
                    monthlyCosts.insurance,
                    monthlyCosts.hoa
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        };

        // Destroy existing chart if it exists
        if (monthlyCostsChart) {
            monthlyCostsChart.destroy();
        }

        // Create new chart
        monthlyCostsChart = new Chart(ctx, {
            type: 'pie',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Monthly Costs Breakdown'
                    }
                }
            }
        });
    }
});
