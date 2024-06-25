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
url = "https://sportsbook.draftkings.com/leagues/motorsports/formula-1?category=driver-props"
driver.get(url)

# Wait until the content is loaded
wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sportsbook-offer-category-card')))

# Once the content is loaded, get the page source and parse with BeautifulSoup
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# Find the content block with the matchups
content_blocks = soup.find_all('div', class_='sportsbook-offer-category-card')

# List to hold the extracted data
matchups = []

# Iterate over each content block
for content_block in content_blocks:
    # Find all rows within the content block
    rows = content_block.find_all('div', class_='sportsbook-event-accordion__wrapper expanded')

    # Extract data from each row
    for row in rows:
        driver_names = row.find_all('span', class_='sportsbook-outcome-cell__label')
        driver_odds = row.find_all('span', class_='sportsbook-odds american default-color')

        if len(driver_names) == 2 and len(driver_odds) == 2:
            driver1 = driver_names[0].text.replace("[Race]", "").strip()
            driver2 = driver_names[1].text.replace("[Race]", "").strip()
            odds1 = float(driver_odds[0].text.strip())  # Convert odds to float
            odds2 = float(driver_odds[1].text.strip())  # Convert odds to float

            if (driver2 < driver1):
                temp = driver1
                tempOdds = odds1
                driver1 = driver2
                odds1 = odds2
                driver2 = temp
                odds2 = tempOdds

            matchup = {
                'driver1': driver1,
                'odds1': odds1,
                'driver2': driver2,
                'odds2': odds2
            }
            matchups.append(matchup)

# Close the WebDriver
driver.quit()

# Connect to MySQL database
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='username',
        password='password',
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
            cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver1}", "DraftKings", odds1))
            cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver2}", "DraftKings", odds2))

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