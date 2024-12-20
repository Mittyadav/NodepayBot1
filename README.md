
# NodepayBot - Ping Utility

NodepayBot is a Python-based tool designed to automate tasks for the Nodepay service, featuring token and proxy management, API interaction, and connection monitoring. This bot makes use of asynchronous programming for efficient operations and ensures a smooth automation experience.

---

## Features

- **Automated API Interactions**: Handles session initialization, pings, and connection states.
- **Proxy Support**: Enables using proxies for improved security and anonymity.
- **Token Management**: Reads and utilizes tokens for authenticated interactions.
- **Logging**: Real-time and colorful logs powered by `loguru` for better debugging and monitoring.
- **Customizable Settings**: Adjustable ping intervals and retry limits.

---

## Get NP_TOKEN
Retrieving `np_token`: A quick guide to find your `np_token`:

- Open the webpage in your browser.
- Press `F12` or use `Ctrl + Shift + I` (Windows/Linux) / `Cmd + Option + I` (Mac) to open the developer console.
- Go to the **Console** tab.
- Enter the following command:

     ```javascript
     localStorage.getItem('np_token');
     ```
- The value displayed is your `np_token`.
- Save `np_token` to `tokens.txt`

---

## Setup
**Clone this repository:**
   ```bash
   git clone https://github.com/Mittyadav/NodepayBot1.git
   ```
   ```bash
   cd NodepayBot1
   ```
   
---

## Requirements

Ensure you have Python 3.8 or newer installed.

Install the required dependencies:
```bash
pip install -r requirements.txt
```

Dependencies include:
- [cloudscraper](https://pypi.org/project/cloudscraper/)
- [curl-cffi](https://pypi.org/project/curl-cffi/)
- [fake-useragent](https://pypi.org/project/fake-useragent/)
- [loguru](https://loguru.readthedocs.io/)
- [pyfiglet](https://pypi.org/project/pyfiglet/)
- [requests](https://pypi.org/project/requests/)
- [termcolor](https://pypi.org/project/termcolor/)

---

## Usage
1. **Prepare Configuration Files:**
   - **`tokens.txt`:** A list of tokens for API authentication. One token per line.
   - **`proxies.txt` (optional):** A list of proxies in the format `protocol://user:pass@host:port`. One per line.

2. **Run the Script:**
```bash
python main.py
```

### Optional:
- Choose whether to use proxies when prompted.
- View real-time logs in the terminal, including ping successes, failures, and connection states.

## Need Proxy?
1. Sign up at [Proxies.fo](https://app.proxies.fo/ref/30b56a40-bacf-9c8a-9681-f9ba7628c585).
2. Go to [Plans](https://app.proxies.fo/plans) and only purchase the "ISP plan" (Residential plans don’t work).
3. Top up your balance, or you can directly buy a plan and pay with Crypto!
4. Go to the Dashboard, select your ISP plan, and click "Generate Proxy."
5. Set the proxy format to `protocol://username:password@hostname:port` and choose any number for the proxy count.
6. Paste the proxies into `proxies.txt`.

---

## Configuration

You can adjust the following parameters in the `main.py` file:

- `PING_INTERVAL`: Interval between pings (in seconds).
- `RETRIES_LIMIT`: Maximum retry attempts before declaring a failure.
- API endpoints are specified in the `DOMAIN_API_ENDPOINTS` dictionary.

---
## Fix Termux Error
- Copy [libcurl-impersonate-chrome.so.4](https://github.com/Enukio/NodepayBot/raw/refs/heads/main/libcurl-impersonate-chrome.so.4) To Folder /data/data/com.termux/files/usr/lib
- Example Command On Termux :
```bash
cp libcurl-impersonate-chrome.so.4 /data/data/com.termux/files/usr/lib
```
Make Sure Allowed Permission Storage On Setting Termux
- Install Python 3.10
```bash
pkg update && upgrade
pkg install tur-repo
pkg install python-is-python3.10
```
- Install Requirements
```bash
pip install --upgrade pip
pkg install -y rust binutils
CARGO_BUILD_TARGET="$(rustc -Vv | grep "host" | awk '{print $2}')" pip install maturin
pip install asyncio
pip install requests
pip install curl-cffi
pip install fake-useragent
pip install loguru
pip install pyfiglet
pip install termcolor
```
---

## License

This project is licensed under the [MIT License](LICENSE).
