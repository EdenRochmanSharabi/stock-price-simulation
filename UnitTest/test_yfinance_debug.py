#!/usr/bin/env python3

"""
YFinance Debug Test
------------------
This test file helps debug issues with yfinance data retrieval.
"""

import unittest
import yfinance as yf
import pandas as pd
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# List of tickers that are failing
PROBLEM_TICKERS = [
    "META", "NWS", "OMC", "PARA", "TMUS", "TTWO", "TKO", "VZ", "DIS", "WBD",
    "ABBV", "ALGN", "BAX", "TECH", "BSX", "CAH"
]

def fetch_ticker_data(ticker, period="2y"):
    """Fetch data for a single ticker and return success status."""
    try:
        print(f"Fetching {ticker}...", end="", flush=True)
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            print(f"EMPTY DATA")
            return (ticker, False, "Empty data returned")
        else:
            print(f"SUCCESS ({len(data)} rows)")
            return (ticker, True, f"{len(data)} rows of data")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return (ticker, False, str(e))


class TestYFinanceDebug(unittest.TestCase):
    """Test case for debugging yfinance issues."""
    
    def test_single_tickers(self):
        """Test each ticker individually."""
        print("\n====== TESTING INDIVIDUAL TICKERS ======")
        results = []
        
        for ticker in PROBLEM_TICKERS:
            ticker_result = fetch_ticker_data(ticker)
            results.append(ticker_result)
            # Add a delay to avoid hitting rate limits
            time.sleep(0.5)
        
        # Count successes
        successes = sum(1 for _, success, _ in results if success)
        print(f"\nSummary: {successes}/{len(PROBLEM_TICKERS)} tickers succeeded")
        
        # Print failures
        failures = [(t, reason) for t, success, reason in results if not success]
        if failures:
            print("\nFailed tickers:")
            for ticker, reason in failures:
                print(f"  - {ticker}: {reason}")
    
    def test_batch_download(self):
        """Test batch download of tickers."""
        print("\n====== TESTING BATCH DOWNLOAD ======")
        try:
            print(f"Downloading {len(PROBLEM_TICKERS)} tickers in batch...")
            start_time = time.time()
            data = yf.download(PROBLEM_TICKERS, period="2y", progress=True, auto_adjust=True, group_by='ticker')
            end_time = time.time()
            
            # Check which tickers have data
            successful_tickers = []
            failed_tickers = []
            
            for ticker in PROBLEM_TICKERS:
                if ticker in data.columns.levels[0]:
                    ticker_data = data[ticker]
                    if not ticker_data.empty:
                        rows = len(ticker_data)
                        successful_tickers.append((ticker, rows))
                    else:
                        failed_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            
            print(f"\nBatch download completed in {end_time - start_time:.2f} seconds")
            print(f"Successful tickers: {len(successful_tickers)}/{len(PROBLEM_TICKERS)}")
            
            for ticker, rows in successful_tickers:
                print(f"  - {ticker}: {rows} rows")
                
            print(f"\nFailed tickers: {len(failed_tickers)}")
            for ticker in failed_tickers:
                print(f"  - {ticker}")
            
        except Exception as e:
            print(f"Batch download failed: {str(e)}")
    
    def test_concurrent_downloads(self):
        """Test concurrent downloads using ThreadPoolExecutor."""
        print("\n====== TESTING CONCURRENT DOWNLOADS ======")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all ticker download tasks
            future_to_ticker = {
                executor.submit(fetch_ticker_data, ticker): ticker 
                for ticker in PROBLEM_TICKERS
            }
            
            # Collect results as they complete
            results = []
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"{ticker} generated an exception: {str(e)}")
                    results.append((ticker, False, str(e)))
        
        end_time = time.time()
        print(f"\nConcurrent downloads completed in {end_time - start_time:.2f} seconds")
        
        # Count successes
        successes = sum(1 for _, success, _ in results if success)
        print(f"Summary: {successes}/{len(PROBLEM_TICKERS)} tickers succeeded")
        
        # Print failures
        failures = [(t, reason) for t, success, reason in results if not success]
        if failures:
            print("\nFailed tickers:")
            for ticker, reason in failures:
                print(f"  - {ticker}: {reason}")


if __name__ == '__main__':
    unittest.main() 