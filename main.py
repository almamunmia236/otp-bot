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
# Load environment variables
load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("Token:", TELEGRAM_TOKEN)

bot = Bot(token=TELEGRAM_TOKEN)

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
    options = webdriver.ChromeOptions()
    profile_path = os.path.abspath(os.path.join("user_data", "simcode"))
    os.makedirs(profile_path, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless') 
    driver = webdriver.Chrome(
        service = Service(ChromeDriverManager().install(), port=9515),
        options=options
    )
    driver.implicitly_wait(10)
    return driver

def login(driver):
    driver.get("https://www.ivasms.com/login")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    driver.find_element(By.NAME, "email").send_keys(EMAIL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    driver.get("https://www.ivasms.com/portal/live/my_sms")
    print("✅ Logged in successfully.")
    save_cookies(driver)

def fetch_messages(driver):


    wait = WebDriverWait(driver, 5)
    driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
    time.sleep(3)
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
            print("Code not found")

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

    # Load cookies or login
    driver.get("https://www.ivasms.com/portal/live/my_sms")
    if load_cookies(driver):
        driver.refresh()
        driver.get("https://www.ivasms.com/portal/live/my_sms")
        time.sleep(5)
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

        while True:


            msg = fetch_messages(driver)
            print(msg)
            if msg and msg not in seen: 
                otp_storage.append(msg)
                seen.add(msg)

            refresh_count += 1
            time.sleep(1)
            await send_worker()
            if refresh_count % 30 == 0:
                print("refreshing")
                driver.refresh()

    except KeyboardInterrupt:
        print("🛑 Interrupted by user, exiting.")
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
