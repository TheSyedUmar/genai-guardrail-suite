"""The same kind of UI check written with Selenium WebDriver."""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.ui


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)  # Selenium Manager downloads the driver automatically
    yield driver
    driver.quit()


def test_selenium_user_gets_an_answer(driver, app_url):
    driver.get(app_url)
    driver.find_element(By.ID, "message-input").send_keys("Which days are mandatory office days?")
    driver.find_element(By.ID, "send-btn").click()

    reply = WebDriverWait(driver, 60).until(  # explicit wait instead of time.sleep
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bot-message']"))
    )
    assert "tuesday" in reply.text.lower()
