import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector

# Set up Selenium WebDriver (using Chrome in this example)
driver = webdriver.Chrome()

# URL of the webpage to scrape
url = "https://play.ballybet.com/sports#event/1020820781"
driver.get(url)

def rearrange_name(full_name):
    parts = [part.strip() for part in full_name.split(' ')]
    new_parts = [parts[-1]] + parts[:-1]
    proper_name = ' '.join(new_parts).replace(',', '')
    return proper_name

try:
    # Wait until the "Matchups" link is clickable
    matchups_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//a[text()="Matchups"]'))
    )
    matchups_link.click()

    # Wait until the content is loaded
    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'KambiBC-outcomes-list__column')))

    # Once the content is loaded, get the page source and parse with BeautifulSoup
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table containing the data
    table = soup.find('div', class_='KambiBC-outcomes-list__column')

    # Find all buttons within the table
    buttons = table.find_all('button')

    # List to hold the extracted data
    matchups = []

    # Iterate over buttons in pairs
    for i in range(0, len(buttons), 2):
        button1 = buttons[i]
        button2 = buttons[i + 1]

        driver_name_div1 = button1.find('div', class_='sc-fqkvVR cyiQDV')
        odds_div1 = button1.find('div', class_='sc-kAyceB gIMtGL')

        driver_name_div2 = button2.find('div', class_='sc-fqkvVR cyiQDV')
        odds_div2 = button2.find('div', class_='sc-kAyceB gIMtGL')

        if driver_name_div1 and odds_div1 and driver_name_div2 and odds_div2:
            driver_name1 = rearrange_name(driver_name_div1.text.strip())
            odds1 = odds_div1.text.strip()

            driver_name2 = rearrange_name(driver_name_div2.text.strip())
            odds2 = odds_div2.text.strip()

            if (driver_name2 < driver_name1):
                temp = driver_name1
                tempOdds = odds1
                driver_name1 = driver_name2
                odds1 = odds2
                driver_name2 = temp
                odds2 = tempOdds

            matchup = {
                'driver1': driver_name1,
                'odds1': odds1,
                'driver2': driver_name2,
                'odds2': odds2
            }
            matchups.append(matchup)

    # Close the WebDriver
    driver.quit()

    # Connect to MySQL database
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='mets5229',
            database='F1Database'
        )
        if conn.is_connected():
            print('Connected to MySQL database')

            # Iterate through matchups and insert into MySQL table
            cursor = conn.cursor()
            for matchup in matchups:
                driver1 = matchup['driver1']
                odds1 = matchup['odds1']
                driver2 = matchup['driver2']
                odds2 = matchup['odds2']

                # Insert query
                insert_query = """
                INSERT INTO F1Matchups (Matchup, Bet, Sportsbook, Odds)
                VALUES (%s, %s, %s, %s)
                """

                # Execute the insert query with data
                cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver1}", "Bally", odds1))
                cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver2}", "Bally", odds2))

            # Commit changes
            conn.commit()
            print(f"{len(matchups)} matchups inserted into F1Matchups table")

    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")

    finally:
        # Close database connection
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print('MySQL connection closed')

except Exception as e:
    print(f"Error scraping data: {e}")

finally:
    # Close the WebDriver
    driver.quit()