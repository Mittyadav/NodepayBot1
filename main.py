import asyncio
import json
import os
import random
import sys
import time
import uuid
from urllib.parse import urlparse

import cloudscraper
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
    print(colored("by Enukio", color="cyan", attrs=["bold"]))
    print("\nWelcome to NodepayBot - Automate your tasks effortlessly!")

def load_file(filename, split_lines=True):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            return content.splitlines() if split_lines else content
    except FileNotFoundError:
        logger.error(f"<red>File '{filename}' not found. Please ensure it exists.</red>")
        return []

def assign_proxies_to_tokens(tokens, proxies):
    if not proxies:
        proxies = [None] * len(tokens)
    paired = list(zip(tokens, proxies))
    return paired

async def call_api(url, data, token, proxy=None, timeout=60):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": f"Mozilla/5.0 (Windows NT {random.randint(7, 11)}.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100, 130)}.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://app.nodepay.ai",
        "Referer": "https://app.nodepay.ai/",
    }

    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        response = requests.post(url, json=data, headers=headers, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if SHOW_REQUEST_ERROR_LOG:
            logger.error(f"API call failed: {e}")
        return None

async def get_account_info(token, proxy=None):
    url = DOMAIN_API["SESSION"]
    try:
        response = await call_api(url, {}, token, proxy)
        if response and response.get("code") == 0:
            data = response["data"]
            return {
                "name": data.get("name", "Unknown"),
                "uid": data.get("uid", "Unknown"),
                **data
            }
    except Exception as e:
        logger.error(f"<red>Error fetching account info for token {token[-10:]}: {e}</red>")
    return None

async def start_ping(token, account_info, proxy, ping_interval, browser_id=None):
    global last_ping_time, status_connect
    browser_id = browser_id or str(uuid.uuid4())
    url_index = 0

    while True:
        url = DOMAIN_API["PING"][url_index]
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,
            "timestamp": int(time.time()),
            "version": "2.2.7"
        }

        try:
            response = await call_api(url, data, token, proxy)
            if response and response.get("data"):
                status_connect = CONNECTION_STATES["CONNECTED"]
                ip_score = response["data"].get("ip_score", "N/A")
                logger.info(f"<green>Ping successful</green>, Network Quality: <cyan>{ip_score}</cyan>, Proxy: <cyan>{proxy}</cyan>")
            else:
                logger.warning("<yellow>Ping failed or invalid response</yellow>")

            url_index = (url_index + 1) % len(DOMAIN_API["PING"])
        except Exception as e:
            logger.error(f"<red>Error during pinging: {e}</red>")

        await asyncio.sleep(ping_interval)

async def claim_daily_reward(token, proxy=None):
    url = DOMAIN_API["DAILY_CLAIM"]
    data = {"mission_id": "daily"}

    try:
        response = await call_api(url, data, token, proxy)
        if response and response.get("code") == 0:
            logger.info(f"<green>Daily reward claimed successfully.</green>")
        else:
            logger.warning("<yellow>Failed to claim daily reward.</yellow>")
    except Exception as e:
        logger.error(f"<red>Error claiming daily reward: {e}</red>")

async def process_account(token, proxy):
    browser_id = str(uuid.uuid4())
    account_info = await get_account_info(token, proxy)
    if account_info:
        await start_ping(token, account_info, proxy, PING_INTERVAL, browser_id)
        await claim_daily_reward(token, proxy)

async def main():
    print_header()

    tokens = load_file("tokens.txt")
    if not tokens:
        logger.error("<red>No tokens found in 'tokens.txt'. Exiting.</red>")
        return

    proxies = load_file("proxies.txt")
    token_proxy_pairs = assign_proxies_to_tokens(tokens, proxies)

    tasks = [process_account(token, proxy) for token, proxy in token_proxy_pairs]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted. Exiting gracefully...")
