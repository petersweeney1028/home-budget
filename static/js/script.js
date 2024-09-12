document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('budgetForm');
    const resultDiv = document.getElementById('result');
    const interestRateSlider = document.getElementById('interestRate');
    const interestRateValue = document.getElementById('interestRateValue');
    const hasTrustFundSelect = document.getElementById('hasTrustFund');
    const trustFundAmountGroup = document.getElementById('trustFundAmountGroup');
    const scenariosList = document.getElementById('scenariosList');
    let monthlyCostsChart = null;

    // Handle trust fund input visibility
    hasTrustFundSelect.addEventListener('change', function() {
        if (this.value === 'yes') {
            trustFundAmountGroup.style.display = 'block';
        } else {
            trustFundAmountGroup.style.display = 'none';
        }
    });

    // Update the interest rate value display
    interestRateSlider.addEventListener('input', function() {
        interestRateValue.textContent = this.value + '%';
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
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
                console.error('Errors:', data.errors);
                resultDiv.innerHTML = '<p>Please correct the errors and try again.</p>';
            } else {
                displayResult(data);
                createMonthlyCostsChart(data.monthlyCosts);
                saveScenario(data);
                loadScenarios();
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            resultDiv.innerHTML = '<p>An error occurred. Please try again later.</p>';
        });
    });

    function displayResult(data) {
        resultDiv.innerHTML = `
            <h2>Home Buying Budget Estimate</h2>
            <p>Recommended home price: $${data.homePrice.toLocaleString()}</p>
            <p>Limiting factor: ${data.limitingFactor}</p>
            <p>Monthly payment: $${data.monthlyCosts.total.toLocaleString()}</p>
            
            <h3>Down Payment Breakdown:</h3>
            <ul>
                <li>Required Down Payment: $${data.downPayment.required.toLocaleString()}</li>
                <li>Total Down Payment: $${data.downPayment.total.toLocaleString()}</li>
                <li>From Savings (max 35%): $${data.downPayment.from_savings.toLocaleString()}</li>
                <li>From Trust Fund (max 20%): $${data.downPayment.from_trust.toLocaleString()}</li>
                <li>Shortfall: $${data.downPayment.shortfall.toLocaleString()}</li>
                <li>Remaining Savings: $${data.downPayment.remaining_savings.toLocaleString()}</li>
                <li>Remaining Trust Fund: $${data.downPayment.remaining_trust_fund.toLocaleString()}</li>
            </ul>
            
            <h3>Monthly Costs Breakdown:</h3>
            <ul>
                <li>Mortgage: $${data.monthlyCosts.mortgage.toLocaleString()}</li>
                <li>Property Tax: $${data.monthlyCosts.property_tax.toLocaleString()}</li>
                <li>Insurance: $${data.monthlyCosts.insurance.toLocaleString()}</li>
                <li>HOA: $${data.monthlyCosts.hoa.toLocaleString()}</li>
                <li>Trust Fund Credit: $${data.monthlyCosts.trust_fund_credit.toLocaleString()}</li>
            </ul>
            
            <h3>Assumptions:</h3>
            <ul>
                ${Object.entries(data.assumptions).map(([key, value]) => `<li>${key}: ${value}</li>`).join('')}
            </ul>
            
            <h3>Explanations:</h3>
            <ul>
                ${data.explanations.map(explanation => `<li>${explanation}</li>`).join('')}
            </ul>
        `;
    }

    function createMonthlyCostsChart(monthlyCosts) {
        const ctx = document.getElementById('monthlyCostsChart').getContext('2d');
        
        if (monthlyCostsChart) {
            monthlyCostsChart.destroy();
        }

        monthlyCostsChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Mortgage', 'Property Tax', 'Insurance', 'HOA'],
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
                    ]
                }]
            },
            options: {
                responsive: true,
                title: {
                    display: true,
                    text: 'Monthly Costs Breakdown'
                }
            }
        });
    }

    function saveScenario(data) {
        const scenarioName = prompt("Enter a name for this scenario:");
        if (scenarioName) {
            data.name = scenarioName;
            fetch('/scenarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(() => {
                loadScenarios();
            })
            .catch(error => console.error('Error:', error));
        }
    }

    function loadScenarios() {
        fetch('/scenarios')
        .then(response => response.json())
        .then(scenarios => {
            scenariosList.innerHTML = '';
            for (const [id, scenario] of Object.entries(scenarios)) {
                const scenarioElement = document.createElement('div');
                scenarioElement.className = 'scenario';
                scenarioElement.innerHTML = `
                    <h3>${scenario.name || 'Unnamed Scenario'}</h3>
                    <p>Home Price: $${scenario.result.homePrice.toLocaleString()}</p>
                    <p>Monthly Payment: $${scenario.result.monthlyCosts.total.toLocaleString()}</p>
                    <p>Limiting Factor: ${scenario.result.limitingFactor}</p>
                    <button class="btn btn-sm btn-info compare-btn" data-id="${id}">Compare</button>
                    <button class="btn btn-sm btn-danger delete-btn" data-id="${id}">Delete</button>
                `;
                scenariosList.appendChild(scenarioElement);
            }
            attachScenarioListeners();
        })
        .catch(error => console.error('Error:', error));
    }

    function attachScenarioListeners() {
        document.querySelectorAll('.compare-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const scenarioId = this.getAttribute('data-id');
                compareScenario(scenarioId);
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const scenarioId = this.getAttribute('data-id');
                deleteScenario(scenarioId);
            });
        });
    }

    function compareScenario(scenarioId) {
        fetch(`/scenario/${scenarioId}`)
        .then(response => response.json())
        .then(scenario => {
            displayResult(scenario.result);
            createMonthlyCostsChart(scenario.result.monthlyCosts);
        })
        .catch(error => console.error('Error:', error));
    }

    function deleteScenario(scenarioId) {
        fetch(`/scenario/${scenarioId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(() => {
            loadScenarios();
        })
        .catch(error => console.error('Error:', error));
    }

    // Load saved scenarios on page load
    loadScenarios();
});
