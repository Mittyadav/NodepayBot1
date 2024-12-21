import asyncio
import json
import os
import random
import sys
import time
import uuid
from urllib.parse import urlparse

import cloudscraper
import requests
from curl_cffi import requests
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

def ask_user_for_proxy():
    while (user_input := input("Do you want to use proxy? (yes/no)? ").strip().lower()) not in ['yes', 'no']:
        print("Invalid input. Please enter 'yes' or 'no'.")

    print(f"You selected: {'Yes' if user_input == 'yes' else 'No'}, ENJOY!\n")

    if user_input == 'yes':
        proxies = load_proxies()
        if not proxies:
            logger.error("<red>No proxies found in 'proxies.txt'. Please add valid proxies.</red>")
            return []
        return proxies
    else:
        return []

def load_file(filename, split_lines=True):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            return content.splitlines() if split_lines else content
    except FileNotFoundError:
        logger.error(f"<red>File '{filename}' not found. Please ensure it exists.</red>")
        return []

def load_proxies():
    return load_file('proxies.txt')

def assign_proxies_to_tokens(tokens, proxies, sessions_per_token=3):
    if not proxies:
        proxies = [None] * (len(tokens) * sessions_per_token)  # No proxies available

    assigned_pairs = []
    for token in tokens:
        for _ in range(sessions_per_token):
            proxy = proxies.pop(0) if proxies else None
            assigned_pairs.append((token, proxy))
    
    return assigned_pairs

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
        response = requests.post(url, json=data, headers=headers, impersonate="safari15_5", proxies={"http": proxy, "https": proxy}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during API call to {url}: {e}") if SHOW_REQUEST_ERROR_LOG else None
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

async def start_ping(token, account_info, proxy, ping_interval, browser_id=None):
    global last_ping_time, RETRIES, status_connect
    browser_id = browser_id or str(uuid.uuid4())
    url_index = 0

    while True:
        if not DOMAIN_API["PING"]:
            logger.error("<red>No PING URLs available in DOMAIN_API['PING'].</red>")
            return

        url = DOMAIN_API["PING"][url_index]
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,
            "timestamp": int(time.time()),
            "version": "2.2.7"
        }

        try:
            response = await call_api(url, data, token, proxy=proxy, timeout=120)
            if response and response.get("data"):
                logger.info(f"<green>Ping Successful</green>")
            else:
                logger.warning(f"<yellow>Invalid or no response from {url}</yellow>")

            url_index = (url_index + 1) % len(DOMAIN_API["PING"])

        except Exception as e:
            logger.error(f"<red>Error during ping: {e}</red>")
        await asyncio.sleep(ping_interval)

async def process_account(token, use_proxy, proxies=None, ping_interval=2.0, browser_id=None):
    proxies = proxies or []
    proxy = proxies[0] if proxies else None

    account_info = await get_account_info(token, proxy=proxy)
    if not account_info:
        logger.error(f"<red>Account info not found for token: {token[-10:]}</red>")
        return

    await start_ping(token, account_info, proxy, ping_interval, browser_id=browser_id)

async def create_tasks(token_proxy_pairs, sessions_per_token=3):
    tasks = []
    for token, proxy in token_proxy_pairs:
        for session_num in range(sessions_per_token):
            browser_id = str(uuid.uuid4())  # Unique browser ID per session
            tasks.append(
                process_account(token, use_proxy=bool(proxy), proxies=[proxy] if proxy else [], ping_interval=4.0, browser_id=browser_id)
            )
    return tasks

async def main():
    sessions_per_token = 3  # Define how many sessions per account you want
    tokens = load_file("tokens.txt")
    if not tokens:
        return logger.error("<red>No tokens found in 'tokens.txt'. Exiting.</red>")

    proxies = ask_user_for_proxy()
    token_proxy_pairs = assign_proxies_to_tokens(tokens, proxies, sessions_per_token)

    logger.info(f"Running {sessions_per_token} sessions per token...")
    tasks = await create_tasks(token_proxy_pairs, sessions_per_token)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"<red>Task failed: {result}</red>")

if __name__ == '__main__':
    try:
        print_header()
        print_file_info()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully...")
    finally:
        print("Cleaning up resources before exiting.")
