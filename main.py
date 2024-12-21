import asyncio
import logging
import requests
import uuid
import time

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CONNECTION_STATES = {"CONNECTED": True, "DISCONNECTED": False}
DOMAIN_API = {
    "PING": [
        "https://nw.nodepay.org/api/network/ping",
        "https://backup.nodepay.org/api/network/ping"
    ]
}
RETRIES = 3  # Number of retries for failed pings

# Helper function for API calls
async def call_api(url, data, token, proxy=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=data, headers=headers, proxies=proxy, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"API call failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        return None

# Validate the proxy
def validate_proxy(proxy):
    try:
        response = requests.get("https://api.ipify.org?format=json", proxies=proxy, timeout=5)
        if response.status_code == 200:
            logger.info(f"Proxy validation successful: {proxy}")
            return True
        else:
            logger.warning(f"Proxy validation failed: {proxy}")
            return False
    except Exception as e:
        logger.error(f"Proxy validation error: {e}")
        return False

# Start pinging the API
async def start_ping(token, account_info, proxy, ping_interval, browser_id=None):
    browser_id = browser_id or str(uuid.uuid4())
    url_index = 0

    # Validate proxy before starting
    if proxy and not validate_proxy(proxy):
        logger.error("Invalid proxy. Exiting.")
        return

    while True:
        url = DOMAIN_API["PING"][url_index]
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,
            "timestamp": int(time.time()),
            "version": "2.2.7"
        }

        success = False
        for attempt in range(RETRIES):
            logger.info(f"[{browser_id}] Attempting ping to {url} (Attempt {attempt + 1}/{RETRIES})")
            try:
                response = await call_api(url, data, token, proxy)
                if response and "data" in response:
                    ip_score = response["data"].get("ip_score", "N/A")
                    logger.info(f"[{browser_id}] Ping successful: Network Quality: {ip_score}, Proxy: {proxy}")
                    success = True
                    break
                else:
                    logger.warning(f"[{browser_id}] Ping failed: {response}")
            except Exception as e:
                logger.error(f"[{browser_id}] Ping error: {e}")

            await asyncio.sleep(5)  # Retry delay

        if not success:
            logger.error(f"[{browser_id}] Ping failed after retries. Switching to next URL.")

        # Rotate URL for redundancy
        url_index = (url_index + 1) % len(DOMAIN_API["PING"])

        # Delay before next ping
        await asyncio.sleep(ping_interval)

# Main function to run multiple instances
async def main():
    token = "YOUR_API_TOKEN"  # Replace with your token
    account_info = {"uid": "USER_ID"}  # Replace with user account info

    # Define proxies and browser IDs for multiple instances
    instances = [
        {"proxy": {"http": "http://proxy1:8000", "https": "http://proxy1:8000"}, "browser_id": str(uuid.uuid4())},
        {"proxy": {"http": "http://proxy2:8000", "https": "http://proxy2:8000"}, "browser_id": str(uuid.uuid4())},
        {"proxy": {"http": "http://proxy3:8000", "https": "http://proxy3:8000"}, "browser_id": str(uuid.uuid4())},
    ]

    tasks = []
    for instance in instances:
        tasks.append(start_ping(token, account_info, instance["proxy"], 60, instance["browser_id"]))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
