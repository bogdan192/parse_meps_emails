# MEP Email Scraper

A Python script to scrape MEPs' emails from the European Parliament website using Playwright.

## Prerequisites

- Python 3.8+
- pip package installer

## Installation

1.  **Clone the repository:**

    ```
    git clone https://github.com/bogdan192/parse_meps_emails.git
    cd parse_meps_emails
    ```
2.  **Install the Python dependencies:**

    ```
    pip install playwright fake-useragent
    ```
3.  **Install Playwright Browsers:**

    ```
    python -m playwright install
    ```

    > Playwright requires browser binaries to operate.  The script will not function correctly if this step is skipped.

## Usage

To run the scraper:
    ```python parse_meps_emails/get_emails_from_site_playwright.py```


## Details

This script:

- Uses Playwright to automate browser interactions.
- Randomizes User-Agent headers to prevent bot detection.
- Applies rate limiting to avoid overloading the target website.

## Troubleshooting

If you encounter errors related to browser binaries, ensure that you have executed:
```python -m playwright install```
This command downloads the necessary browser binaries for Playwright to control.
