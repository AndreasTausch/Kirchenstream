import time
import pyautogui

def handle_cookie_banner(driver):
    try:
        script = """
            const btn = document.querySelector('button[data-testid="uc-accept-all-button"]');
            if (btn) { btn.click(); return true; } else { return false; }
        """
        result = driver.execute_script(script)
        if result:
            return
    except:
        pass

    time.sleep(2)
    for _ in range(6):
        pyautogui.press('tab')
        time.sleep(0.2)
    pyautogui.press('enter')
