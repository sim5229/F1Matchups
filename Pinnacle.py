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
url = "https://www.pinnacle.com/en/formula-1/austrian-grand-prix-sprint/matchups/#period:0"
driver.get(url)

# Wait until the contentBlock square is loaded
wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
content_block = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'contentBlock.square')))

# Once the content block is loaded, get the page source and parse with BeautifulSoup
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# Find the content block with the matchups
content_block = soup.find('div', class_='contentBlock square')

# Find all rows within the content block
rows = content_block.find_all('div', class_='style_row__yBzX8 style_row__12oAB')

# List to hold the extracted data
matchups = []

# Extract data from each row
for row in rows:
    participants = row.find_all('span', class_='ellipsis event-row-participant style_participant__2BBhy')
    buttons = row.find_all('button', class_='market-btn style_button__G9pbN style_pill__2U30o style_vertical__2J4sL')

    if len(participants) == 2 and len(buttons) == 2:
        driver1 = participants[0].text.strip()
        driver2 = participants[1].text.strip()
        odds1 = buttons[0].find('span').text.strip()
        odds2 = buttons[1].find('span').text.strip()

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
            cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver1}", "Pinnacle", odds1))
            cursor.execute(insert_query, (f"{driver1} vs {driver2}", f"{driver2}", "Pinnacle", odds2))

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