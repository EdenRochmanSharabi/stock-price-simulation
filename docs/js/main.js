// Main JavaScript file for the Stock Simulation website

// Global variables
let allStocks = [];
let displayedStocks = [];
const stocksPerPage = 12;
let currentPage = 1;

// DOM elements
const stockCardsContainer = document.getElementById('stockCards');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const stockSearch = document.getElementById('stockSearch');
const searchButton = document.getElementById('searchButton');
const loading = document.getElementById('loading');

// Initialize charts
let returnsChart = null;
let sharpeChart = null;
let sortinoChart = null;

// Event listeners
document.addEventListener('DOMContentLoaded', initializePage);
loadMoreBtn.addEventListener('click', loadMoreStocks);
searchButton.addEventListener('click', searchStocks);
stockSearch.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchStocks();
    }
});

// Initialize the page
async function initializePage() {
    try {
        // Load all results data
        const response = await fetch('data/all_results.json');
        if (!response.ok) {
            throw new Error('Failed to load stock data');
        }
        
        allStocks = await response.json();
        console.log(`Loaded data for ${allStocks.length} stocks`);
        
        // Load rankings data
        const rankingsResponse = await fetch('data/rankings.json');
        if (rankingsResponse.ok) {
            const rankings = await rankingsResponse.json();
            populateRankingTables(rankings);
            createRankingCharts(rankings);
        }
        
        // Display initial stocks
        displayStocks();
        
        // Hide loading indicator
        loading.style.display = 'none';
    } catch (error) {
        console.error('Error initializing page:', error);
        loading.innerHTML = `<p class="text-danger">Error loading data: ${error.message}</p>`;
    }
}

// Populate ranking tables
function populateRankingTables(rankings) {
    // Returns table
    const returnsTable = document.getElementById('returnsTable').getElementsByTagName('tbody')[0];
    rankings.top_returns.forEach((stock, index) => {
        const row = returnsTable.insertRow();
        row.innerHTML = `
            <td>${index + 1}</td>
            <td><a href="#" class="stock-link" data-ticker="${stock.ticker}">${stock.ticker}</a></td>
            <td>${(stock.mean_return * 100).toFixed(2)}%</td>
        `;
    });
    
    // Sharpe ratio table
    const sharpeTable = document.getElementById('sharpeTable').getElementsByTagName('tbody')[0];
    rankings.top_sharpe.forEach((stock, index) => {
        const row = sharpeTable.insertRow();
        row.innerHTML = `
            <td>${index + 1}</td>
            <td><a href="#" class="stock-link" data-ticker="${stock.ticker}">${stock.ticker}</a></td>
            <td>${stock.sharpe_ratio.toFixed(2)}</td>
        `;
    });
    
    // Sortino ratio table
    const sortinoTable = document.getElementById('sortinoTable').getElementsByTagName('tbody')[0];
    rankings.top_sortino.forEach((stock, index) => {
        const row = sortinoTable.insertRow();
        row.innerHTML = `
            <td>${index + 1}</td>
            <td><a href="#" class="stock-link" data-ticker="${stock.ticker}">${stock.ticker}</a></td>
            <td>${stock.sortino_ratio.toFixed(2)}</td>
        `;
    });
    
    // Add event listeners to stock links
    document.querySelectorAll('.stock-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const ticker = this.dataset.ticker;
            showStockModal(ticker);
        });
    });
}

// Create charts for rankings
function createRankingCharts(rankings) {
    // Returns chart
    const returnsCtx = document.getElementById('returnsChart').getContext('2d');
    returnsChart = new Chart(returnsCtx, {
        type: 'bar',
        data: {
            labels: rankings.top_returns.map(stock => stock.ticker),
            datasets: [{
                label: 'Expected Return (%)',
                data: rankings.top_returns.map(stock => stock.mean_return * 100),
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Stocks by Expected Return'
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Return: ${context.raw.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Expected Return (%)'
                    }
                }
            }
        }
    });
    
    // Sharpe ratio chart
    const sharpeCtx = document.getElementById('sharpeChart').getContext('2d');
    sharpeChart = new Chart(sharpeCtx, {
        type: 'bar',
        data: {
            labels: rankings.top_sharpe.map(stock => stock.ticker),
            datasets: [{
                label: 'Sharpe Ratio',
                data: rankings.top_sharpe.map(stock => stock.sharpe_ratio),
                backgroundColor: 'rgba(25, 135, 84, 0.7)',
                borderColor: 'rgba(25, 135, 84, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Stocks by Sharpe Ratio'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Sharpe Ratio'
                    }
                }
            }
        }
    });
    
    // Sortino ratio chart
    const sortinoCtx = document.getElementById('sortinoChart').getContext('2d');
    sortinoChart = new Chart(sortinoCtx, {
        type: 'bar',
        data: {
            labels: rankings.top_sortino.map(stock => stock.ticker),
            datasets: [{
                label: 'Sortino Ratio',
                data: rankings.top_sortino.map(stock => stock.sortino_ratio),
                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                borderColor: 'rgba(220, 53, 69, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Stocks by Sortino Ratio'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Sortino Ratio'
                    }
                }
            }
        }
    });
}

// Display stocks in the grid
function displayStocks() {
    // Clear loading indicator if it exists
    if (loading) {
        loading.style.display = 'none';
    }
    
    // Show the initial set of stocks
    const startIndex = (currentPage - 1) * stocksPerPage;
    const endIndex = Math.min(startIndex + stocksPerPage, allStocks.length);
    
    // Create array of stocks to display
    const stocksToDisplay = allStocks.slice(startIndex, endIndex);
    displayedStocks = displayedStocks.concat(stocksToDisplay);
    
    // Create HTML cards for each stock
    stocksToDisplay.forEach(stock => {
        const stockCard = document.createElement('div');
        stockCard.className = 'col-md-4 col-lg-3';
        stockCard.innerHTML = `
            <div class="card stock-card mb-4">
                <div class="card-header">
                    ${stock.ticker}
                </div>
                <div class="card-body">
                    <div class="metric-item">
                        <span class="metric-label">Expected Return:</span>
                        <span class="metric-value ${stock.mean_return >= 0 ? 'positive' : 'negative'}">
                            ${(stock.mean_return * 100).toFixed(2)}%
                        </span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Sharpe Ratio:</span>
                        <span class="metric-value">${stock.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Risk (Std Dev):</span>
                        <span class="metric-value">${(stock.std_return * 100).toFixed(2)}%</span>
                    </div>
                    <button class="btn btn-primary btn-sm w-100 mt-3 view-details" data-ticker="${stock.ticker}">
                        View Details
                    </button>
                </div>
            </div>
        `;
        stockCardsContainer.appendChild(stockCard);
    });
    
    // Add event listeners to view details buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', function() {
            const ticker = this.dataset.ticker;
            showStockModal(ticker);
        });
    });
    
    // Hide load more button if all stocks are displayed
    if (endIndex >= allStocks.length) {
        loadMoreBtn.style.display = 'none';
    }
}

// Load more stocks when the button is clicked
function loadMoreStocks() {
    currentPage++;
    displayStocks();
}

// Search for stocks by ticker
function searchStocks() {
    const searchTerm = stockSearch.value.trim().toUpperCase();
    
    if (searchTerm === '') {
        // Reset to show all stocks
        resetStockDisplay();
        return;
    }
    
    // Filter stocks based on search term
    const filteredStocks = allStocks.filter(stock => 
        stock.ticker.includes(searchTerm)
    );
    
    // Reset display and show filtered results
    resetStockDisplay();
    
    if (filteredStocks.length === 0) {
        stockCardsContainer.innerHTML = `
            <div class="col-12 text-center">
                <p>No stocks found matching "${searchTerm}"</p>
            </div>
        `;
        loadMoreBtn.style.display = 'none';
    } else {
        allStocks = filteredStocks;
        displayStocks();
    }
}

// Reset the stock display
function resetStockDisplay() {
    stockCardsContainer.innerHTML = '';
    displayedStocks = [];
    currentPage = 1;
    loadMoreBtn.style.display = 'block';
}

// Show stock details in modal
function showStockModal(ticker) {
    const stock = allStocks.find(s => s.ticker === ticker);
    
    if (!stock) {
        console.error(`Stock not found: ${ticker}`);
        return;
    }
    
    // Set modal title
    document.getElementById('stockModalTitle').textContent = `${ticker} Simulation Results`;
    
    // Populate stats
    const statsContainer = document.getElementById('stockModalStats');
    statsContainer.innerHTML = `
        <table class="table table-sm">
            <tr>
                <th>Expected Return:</th>
                <td class="${stock.mean_return >= 0 ? 'text-success' : 'text-danger'}">
                    ${(stock.mean_return * 100).toFixed(2)}%
                </td>
            </tr>
            <tr>
                <th>Risk (Std Dev):</th>
                <td>${(stock.std_return * 100).toFixed(2)}%</td>
            </tr>
            <tr>
                <th>Sharpe Ratio:</th>
                <td>${stock.sharpe_ratio.toFixed(2)}</td>
            </tr>
            <tr>
                <th>Sortino Ratio:</th>
                <td>${stock.sortino_ratio.toFixed(2)}</td>
            </tr>
            <tr>
                <th>Max Drawdown:</th>
                <td>${(stock.max_drawdown * 100).toFixed(2)}%</td>
            </tr>
            <tr>
                <th>Value at Risk (95%):</th>
                <td>${(stock.var_95 * 100).toFixed(2)}%</td>
            </tr>
            <tr>
                <th>Conditional VaR (95%):</th>
                <td>${(stock.cvar_95 * 100).toFixed(2)}%</td>
            </tr>
        </table>
    `;
    
    // Set chart image
    const chartImg = document.getElementById('stockModalChart');
    chartImg.src = `images/${ticker}_final_dist.png`;
    chartImg.alt = `${ticker} Final Value Distribution`;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('stockModal'));
    modal.show();
} 