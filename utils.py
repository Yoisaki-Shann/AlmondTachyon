import os
import json
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- ⚙️ CONFIGURATION ⚙️ ---
CLUB_MAP = {
    "1": 1, "lunasoul": 1, "main": 1,
    "2": 2, "umaclover": 2, "sub": 2
}

CLUB_FILENAMES = {
    1: "lunasoul",   
    2: "umaclover"    
}

# --- 2. CLUB ID RESOLVER ---
def resolve_club_id(user_input):
    if user_input is None: return 1
    key = str(user_input).lower()
    return CLUB_MAP.get(key, 1)

# --- 3. FILE PATHS ---
JSON_PATH = "Data/json/"
CSV_PATH = "Data/csv/"
os.makedirs(JSON_PATH, exist_ok=True)
os.makedirs(CSV_PATH, exist_ok=True)


def get_filenames(club_id):
    real_name = CLUB_FILENAMES.get(club_id, f"club{club_id}")
    prefix = f"{real_name}_"
    return {
        "bind": f"{JSON_PATH}{prefix}bindings.json",
        "json": f"{JSON_PATH}{prefix}weekly_start.json",
        "csv": f"{CSV_PATH}{prefix}weekly_history.csv"
    }

# --- 4. PERMISSION CHECKER ---
def is_manager(ctx):
    if ctx.author.guild_permissions.administrator: return True
    allowed_roles = ["mod", "staff", "ls uma officer", "umaclover leader"]
    for role in ctx.author.roles:
        if role.name.lower() in allowed_roles: return True
    return False

# --- 5. JSON LOADER & SAVERS ---
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def save_weekly_csv(filename, data_list, previous_data):
    file_exists = os.path.isfile(filename)
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Name", "Total Fans", "Weekly Gain", "Daily Avg"])
        for p in data_list:
            gain = p['fans'] - previous_data.get(p['name'], p['fans'])
            if gain < 0: gain = 0
            writer.writerow([date_str, p['name'], p['fans'], gain, int(gain/7)])

# --- 6. BACKGROUND REFRESHER (Runs every 1 hour) ---
def perform_background_refresh(port_number):
    print(f"🔄 Background Refresh: Port {port_number}...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port_number}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # REFRESH HAPPENS HERE ONLY
        driver.refresh()
        time.sleep(5) # Wait for load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        print(f"✅ Port {port_number} Refreshed.")
    except Exception as e:
        print(f"⚠️ Refresh Failed on Port {port_number}: {e}")

# --- 7. THE READER (Runs when you type !profile) ---
def read_browser_and_sort(port_number):
    
    # Notice: NO REFRESH CODE HERE! It just looks at what is already there.
    print(f"👀 Reading Chrome on Port {port_number}...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port_number}")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        try: 
            full_title = driver.title
            if "|" in full_title:
                club_name = full_title.split("|")[0].strip()
            else:
                club_name = "Club"
        except: club_name = "Club"
        
        rows = driver.find_elements(By.CLASS_NAME, "club-member-row-container")
        if not rows: return None, "No members found (Browser might be refreshing? Try again in 5s)."
        
        raw_data = []
        for row in rows:
            try:
                name = row.find_element(By.CLASS_NAME, "club-profile-name").text.strip()
                stats = row.find_elements(By.CLASS_NAME, "club-profile-cell-reg-span")
                if len(stats) >= 3:
                    fan_number = int(stats[0].text.replace(",", ""))
                    daily_str = stats[1].text.replace(",", "")
                    daily_avg = int(daily_str) if daily_str.isdigit() else 0
                    login_time = stats[2].text
                    raw_data.append({'name': name, 'fans': fan_number, 'daily': daily_avg, 'login': login_time})
            except: continue 
        return club_name, sorted(raw_data, key=lambda x: x['fans'], reverse=True)
    except Exception as e:
        return None, f"Error: Port {port_number} not found. ({e})"