import os
import re
import sys
from loguru import logger
from textwrap import fill
from colorama import Fore, Style, init

# Simulated DEBUG flag for logging
DEBUG = True

# Initialize colorama
init(autoreset=True)

# Gradient text generator
def gradient_text(text):
    colors = [91, 93, 92, 96, 94, 95]  # ANSI color codes for gradient
    gradient_text = ""
    for index, char in enumerate(text):
        if char.strip():  # Ignore spaces
            gradient_text += f"\033[{colors[index % len(colors)]}m{char}\033[0m"
        else:
            gradient_text += char
    return gradient_text

# Banner function
def banner(total_tokens, total_proxies):
    raw_banner = f"""
    _   __          __  Version 2.0 by dark life
   / | / /___  ____/ /__  ____  ____ ___  __
  /  |/ / __ \\/ __  / _ \\/ __ \\/ __ `/ / / /
 / /|  / /_/ / /_/ /  __/ /_/ / /_/ / /_/ / 
/_/ |_/\\____/\\__,_/\\___/ .___/\\__,_/\\__, /  
                      /_/          /____/   

Welcome to NodepayBot - Automate your tasks effortlessly!
Max 3 connections per account. Too many proxies may cause issues.

------------------------------------------------------------
Total Tokens: {total_tokens}     |     Total Proxies: {total_proxies}
------------------------------------------------------------
"""
    return gradient_text(raw_banner)

# Counts lines in a file
def count_lines(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return sum(1 for line in file if line.strip())
        return 0
    except Exception:
        return 0
    
    message_without_color = re.sub(r'\033\[.*?m', '', record["message"])
    wrapped_message = fill(message_without_color, width=120)
    record["message"] = wrapped_message
    
    return True

# Setup logging configuration
def setup_logging():
    logger.remove()
    log_level = "DEBUG" if DEBUG else "INFO"
    logger.add(
        sink=sys.stdout,
        format="<magenta>[Nodepay]</magenta> | {time:YYYY-MM-DD HH:mm:ss} | {message}",
        colorize=True,
        enqueue=True,
        filter=wrap_message,
        level=log_level
    )

# Function to display the startup art
def startup_art():
    total_tokens = count_lines('tokens.txt')
    total_proxies = count_lines('proxies.txt')
    
    formatted_start_text = start_text.format(
        total_tokens=total_tokens,
        total_proxies=total_proxies
    )
    
    print(f"\n{Fore.LIGHTCYAN_EX}{formatted_start_text}{Style.RESET_ALL}\n")
