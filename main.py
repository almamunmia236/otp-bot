import os
import time
import asyncio
import pickle
from dotenv import load_dotenv
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from telegram.error import NetworkError
# Load environment variables

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("EMAIL:", EMAIL)
print("PASSWORD:", PASSWORD)
print("Token:", TELEGRAM_TOKEN)
print("CHAT_ID:", CHAT_ID)

request = HTTPXRequest(connect_timeout=10.0, read_timeout=20.0)  # default 5
bot = Bot(token=TELEGRAM_TOKEN, request=request)

COOKIE_FILE = "selenium_cookies.pkl"
otp_storage = []


def format_otp_msg(data):
    return f""" New OTP Found! ✨

📞 Number: `{data['number']}`

🔑 OTP Code: `{data['otp']}`

{data['message_line1']}

"""



async def send_worker():
    print("kaj hosse")

    try :

        if len(otp_storage)>0:
            text = otp_storage[0]
            print(text)
            try:
                await bot.send_message(chat_id=CHAT_ID, text=f"🔐 {text}",parse_mode=ParseMode.MARKDOWN)
                print(f"✅ Sent OTP: {text}")
                otp_storage.clear()


            except Exception as e:
                print(f"❌ Failed to send OTP: {e}")
        else:
            print("no code")
    except:
        pass

    

def save_cookies(driver):
    with open(COOKIE_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    if os.path.exists(COOKIE_FILE):
        cookies = pickle.load(open(COOKIE_FILE, 'rb'))
        for c in cookies:
            driver.add_cookie(c)
        return True
    return False

def init_driver():
    print("try to open browser")
    options = webdriver.ChromeOptions()
    profile_path = "/tmp/simcode"
    os.makedirs(profile_path, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service("/usr/bin/chromedriver"),
        options=options
    )
    return driver



def login(driver):
    print("starting log in")
    driver.get("https://www.ivasms.com/login")
    
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    time.sleep(10)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )

    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    print("email send")

    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    print("password send")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(10)
    driver.get("https://www.ivasms.com/portal/live/my_sms")
    print(driver.current_url)

    print("✅ Logged in successfully.")
    save_cookies(driver)

def fetch_messages(driver):


    wait = WebDriverWait(driver, 3)
    driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
    driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")
    try:
        # tergetNumber='//tbody[@id="LiveTestSMS"]//tr[.//p[text()="2250153708770"]]/td[5]'

        xpathnumber = '//tbody[@id="LiveTestSMS"]//p[contains(@class, "CopyText")]'
        elemNumber = wait.until(EC.presence_of_element_located((By.XPATH, xpathnumber)))
        Number = elemNumber.text
        
        smsxpath = "//tbody[@id=\"LiveTestSMS\"]//tr[1]//td[5]"
        fullsms = wait.until(EC.presence_of_element_located((By.XPATH, smsxpath)))
        fullSms = fullsms.text

        match = re.search(r"\b(\d{4,10})\b", fullSms)  

        if match:
            code = match.group(1)
            print("OTP Code:", code)
        else:
            code="None"

        new_data = {
                    "number": Number,
                    "otp": code,
                    "message_line1": fullSms,
                }

        newSms=format_otp_msg(new_data)

        print(newSms)

        return newSms
    
    except:
        print("❌ No code found")
        return None

async def main():
    if not all([EMAIL, PASSWORD, TELEGRAM_TOKEN, CHAT_ID]):
        print("❗ Missing environment variables!")
        return

    driver = init_driver()
    print("🌐 Checking network...")
    driver.get("https://example.com")
    print("✅ Got example.com")

    # Load cookies or login
    driver.get("https://www.ivasms.com/portal/live/my_sms")

    print("✅ Got ivas.com")


    if load_cookies(driver):
        driver.refresh()
        driver.get("https://www.ivasms.com/portal/live/my_sms")
        time.sleep(5)
        print(driver.current_url)

        if "/portal/live/my_sms" not in driver.current_url:
            print("🔄 Session expired, logging in...")
            login(driver)
    else:
        print("🔄 No cookies, logging in...")
        login(driver)

    seen = set()
    refresh_count = 0

    print("✅ Starting SMS monitor...")

    # Start background telegram sender

    try:
        driver.get("https://www.ivasms.com/portal/live/my_sms")
        wait = WebDriverWait(driver, 2)

        try:
            xpath='//button[@class=\"driver-popover-next-btn\"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
            print("clicked sikp button 1")
        except:
            print("no clicked sikp button 2")

        try:
            xpath='//button[normalize-space(text())=\"Done\"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
            print("clicked sikp button 2")
        except:
            print("no clicked sikp button 2")


        while True:


            msg = fetch_messages(driver)
            print(msg)
            if msg and msg not in seen: 
                otp_storage.append(msg)
                seen.add(msg)

            time.sleep(1)
            await send_worker()
            if refresh_count % 10 == 0:
                driver.refresh()

            refresh_count += 1

    except KeyboardInterrupt:
        print("🛑 Interrupted by user, exiting.")
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
