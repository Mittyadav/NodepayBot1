import asyncio
import json
import random
import sys
import time
import uuid
from urllib.parse import urlparse

import requests
import cloudscraper
from loguru import logger
from pyfiglet import figlet_format
from termcolor import colored

# Global configuration
SHOW_REQUEST_ERROR_LOG = False
PING_INTERVAL = 60
RETRIES = 60

DOMAIN_API = {
    "SESSION": "http://api.nodepay.ai/api/auth/session",
    "PING": ["https://nw.nodepay.org/api/network/ping"],
    "DAILY_CLAIM": "https://api.nodepay.org/api/mission/complete-mission",
    "DEVICE_NETWORK": "https://api.nodepay.org/api/network/device-networks"
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

status_connect = CONNECTION_STATES
account_info = {}
last_ping_time = {}
token_status = {}
browser_id = None

# Setup logger
logger.remove()
logger.add(
    sink=sys.stdout,
    format="<r>[Nodepay]</r> | <white>{time:YYYY-MM-DD HH:mm:ss}</white> | "
           "<level>{level: ^7}</level> | <cyan>{line: <3}</cyan> | {message}",
    colorize=True
)
logger = logger.opt(colors=True)

def print_header():
    ascii_art = figlet_format("NodepayBot", font="slant")
    colored_art = colored(ascii_art, color="cyan")
    border = "=" * 40

    print(border)
    print(colored_art)
    print(colored("by dark life", color="cyan", attrs=["bold"]))
    print("\nWelcome to NodepayBot - Automate your tasks effortlessly!")

def print_file_info():
    tokens = load_file('tokens.txt')
    proxies = load_file('proxies.txt')
    border = "=" * 40

    print(border)
    print(
        f"\nTokens: {len(tokens)} - Loaded {len(proxies)} proxies"
        "\nNodepay only supports 3 connections per account. Using too many proxies may cause issues.\n"
        f"\n{border}"
    )

def load_file(filename, split_lines=True):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            return content.splitlines() if split_lines else content
    except FileNotFoundError:
        logger.error(f"<red>File '{filename}' not found. Please ensure it exists.</red>")
        return []

def assign_proxies_to_tokens(tokens, proxies):
    if proxies is None:
        proxies = []
    paired = list(zip(tokens[:len(proxies)], proxies))
    remaining = [(token, None) for token in tokens[len(proxies):]]
    return paired + remaining

def get_ip_address(proxy=None):
    try:
        url = "https://api.ipify.org?format=json"
        response = cloudscraper.create_scraper().get(url, proxies={"http": proxy, "https": proxy} if proxy else None)
        return response.json().get("ip", "Unknown") if response.status_code == 200 else "Unknown"
    except Exception as e:
        logger.error(f"<red>Failed to fetch IP address: {e}</red>")
    return "Unknown"

async def call_api(url, data, token, proxy=None, timeout=60):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://app.nodepay.ai/",
        "Accept": "application/json, text/plain, */*",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm",
        "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cors-site"
    }

    response = None

    try:
        # Perform API request with proxy if available
        response = requests.post(url, json=data, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during API call to {url}: {e}") if SHOW_REQUEST_ERROR_LOG else None
        if response and response.status_code == 403:
            logger.error("<red>Access denied (HTTP 403). Possible invalid token or blocked IP/proxy.</red>")
            return None
        elif response and response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            logger.warning(f"<yellow>Rate limit hit (HTTP 429). Retry after {retry_after} seconds.</yellow>")
            time.sleep(int(retry_after) if retry_after != "unknown" else 5)
        else:
            logger.error(f"Request failed: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from {url}: {e}") if SHOW_REQUEST_ERROR_LOG else None
    except Exception as e:
        logger.error(f"Unexpected error during API call: {e}") if SHOW_REQUEST_ERROR_LOG else None

    return None

async def get_account_info(token, proxy=None):
    url = DOMAIN_API["SESSION"]
    try:
        response = await call_api(url, {}, token, proxy)
        if response and response.get("code") == 0:
            data = response["data"]
            return {
                "name": data.get("name", "Unknown"),
                "ip_score": data.get("ip_score", "N/A"),
                **data
            }
    except Exception as e:
        logger.error(f"<red>Error fetching account info for token {token[-10:]}: {e}</red>")
    return None

async def start_ping(token, account_info, proxy):
    url = DOMAIN_API["PING"][0]  # Use the first URL in the list
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    while True:
        try:
            response = requests.post(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=15)
            if response.status_code == 200:
                logger.info(f"<green>Ping successful</green>")
                last_ping_time[token] = time.time()
                account_info[token]["ping"] = time.time()  # update ping time
            else:
                logger.warning(f"<yellow>Ping failed with status code {response.status_code}</yellow>")
        except Exception as e:
            logger.error(f"<red>Error during ping: {e}</red>")

        await asyncio.sleep(PING_INTERVAL)

async def process_account(token, proxies, ping_interval=2.0):
    proxy = random.choice(proxies) if proxies else None  # Use a random proxy from the list

    account_info = await get_account_info(token, proxy)

    if not account_info:
        logger.error(f"<red>Account info not found for token {token}</red>")
        return

    logger.info(f"Processing account: {account_info['name']}")

    # Start ping task
    await start_ping(token, account_info, proxy)

    # Perform daily claim if possible
    if dailyclaim(token):
        logger.info(f"<green>Daily claim successful for {account_info['name']}</green>")

    # Add more tasks as needed (e.g., refreshing data, performing other API actions)
    await asyncio.sleep(ping_interval)

async def main():
    tokens = load_file('tokens.txt')
    proxies = load_file('proxies.txt')

    # Assign proxies to tokens
    paired_tokens = assign_proxies_to_tokens(tokens, proxies)

    tasks = []
    for token, proxy in paired_tokens:
        tasks.append(process_account(token, proxies))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    print_header()
    print_file_info()
    asyncio.run(main())
