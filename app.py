import streamlit as st
import pandas as pd
import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure Streamlit
st.set_page_config(page_title="Texas HCP Scraper", layout="wide")
st.title("👨‍⚕️ Texas Healthcare Provider Search Automation")

uploaded_file = st.file_uploader("📤 Upload Excel File with FirstName and LastName columns", type=["xlsx"])

if uploaded_file:
    input_df = pd.read_excel(uploaded_file)
    st.write("📄 Preview of Uploaded Data:")
    st.dataframe(input_df)

    if st.button("🚀 Start Scraping"):
        with st.spinner("Scraping in progress... Please wait."):

            # Set up Selenium Chrome Driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            wait = WebDriverWait(driver, 10)
            results = []

            for index, row in input_df.iterrows():
                first_name = row['FirstName']
                last_name = row['LastName']

                try:
                    driver.get("https://profile.tmb.state.tx.us/Search.aspx?3939a0ce-1fde-497b-a10f-dfb6ad30fb80")
                    wait.until(EC.presence_of_element_located((By.ID, "BodyContent_tbLastName"))).clear()
                    driver.find_element(By.ID, "BodyContent_tbLastName").send_keys(last_name)
                    driver.find_element(By.ID, "BodyContent_tbFirstName").clear()
                    driver.find_element(By.ID, "BodyContent_tbFirstName").send_keys(first_name)
                    driver.find_element(By.ID, "BodyContent_btnSearch").click()

                    wait.until(EC.presence_of_element_located((By.ID, "BodyContent_gvSearchResults")))
                    rows = driver.find_elements(By.CSS_SELECTOR, "#BodyContent_gvSearchResults tr")[1:]

                    for r in rows:
                        cols = r.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 6:
                            name_tag = cols[0].find_element(By.TAG_NAME, "a")
                            results.append({
                                "Searched FirstName": first_name,
                                "Searched LastName": last_name,
                                "Name": name_tag.text.strip(),
                                "JS_Link": name_tag.get_attribute("href"),
                                "License": cols[1].text.strip(),
                                "License Type": cols[2].text.strip(),
                                "Address": cols[3].text.strip(),
                                "City": cols[4].text.strip()
                            })
                except Exception as e:
                    st.warning(f"No result for {first_name} {last_name} — {str(e)}")
                    continue

            driver.quit()

            if results:
                df = pd.DataFrame(results)

                # Display in Streamlit
                st.success("✅ Scraping completed successfully!")
                st.dataframe(df)

                # Download Button
                output = BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                st.download_button(
                    label="📥 Download Results as Excel",
                    data=output,
                    file_name="hcp_texas_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ No data was scraped. Please check your inputs.")