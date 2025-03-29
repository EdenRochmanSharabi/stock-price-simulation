# Stock Price Simulation - GitHub Pages Edition

This repository contains a static website version of the Stock Price Simulation project, designed to be hosted on GitHub Pages.

## About the Project

This project displays pre-computed Monte Carlo simulation results for S&P 500 stocks using a hybrid model that combines:

- Geometric Brownian Motion (GBM)
- Jump Diffusion
- Regime Switching (Volatility Clustering)

The simulations were run with the following parameters:
- 10,000 simulations per stock
- 21 trading days time horizon
- Daily time steps (dt = 1/252)
- Hybrid model combining all three approaches

## Features

- Browse simulation results for S&P 500 stocks
- View top-performing stocks ranked by expected return, Sharpe ratio, and Sortino ratio
- Examine detailed statistics for each stock
- Visualize the distribution of potential final values

## Viewing the Website

You can access the static website at: [https://yourusername.github.io/your-repo-name](https://yourusername.github.io/your-repo-name)

## Local Development

To run this website locally:

1. Clone the repository
   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Open `docs/index.html` in your web browser

## How it Works

This is a static website that uses HTML, CSS, and JavaScript to display pre-computed simulation results. No server-side processing is required, making it perfect for GitHub Pages hosting.

The data was generated using the full Stock Price Simulation engine, with results saved as JSON files that are loaded by the front-end JavaScript.

## Deploying to GitHub Pages

1. Push this repository to GitHub
2. Go to repository Settings → Pages
3. Select the "main" branch and "/docs" folder
4. Click Save

GitHub will automatically deploy the site and provide you with a URL.

## Customizing

- Edit the files in the `docs` directory to customize the website
- Run the simulation script to generate new data
- Update the data files in `docs/data` with your new results

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
