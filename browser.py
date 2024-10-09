import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException  # Import TimeoutException
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
import streamlit as st
from dotenv import load_dotenv
import vars

# Load environment variables from .env file
load_dotenv()

# Initialize Streamlit app
st.title("Browser Automation in English language instructions")

# Initialize the AzureChatOpenAI instance with correct parameters
llm = AzureChatOpenAI(
    openai_api_type=vars.openai_api_type,
    azure_deployment=vars.azure_deployment,
    openai_api_version=vars.openai_api_version,
    azure_endpoint=vars.azure_endpoint,
    openai_api_key=vars.openai_api_key
)

# Generate Selenium code with LLM
def get_selenium_code(command, driver_variable_name='driver'):
    prompt = f'''
    You are an expert Python developer specializing in Selenium automation.
    Generate Python Selenium code to perform the following action on google.com:

    "{command}"

    Instructions:
    - Use robust selectors that are less likely to break if attributes change.
    - Use find_element() instead of the deprecated find_element_by_* methods.
    - Prefer using By.NAME, By.ID, By.XPATH, etc., for locating elements.
    - Implement error handling and fallback options.
    - Use explicit waits to ensure elements are loaded before interaction.
    - Use the variable '{driver_variable_name}' as the Selenium WebDriver instance.
    - Do not include any import statements or explanations.
    - Ensure the code is executable and handles exceptions.
    - Assume the driver has been initialized and navigated to 'https://www.google.com'.
    '''
    try:
        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        st.error(f"Error generating code: {e}")
        return None

# WebDriver initialization (only once)
def init_webdriver():
    if 'driver_initialized' not in st.session_state:
        st.session_state['driver_initialized'] = False
    if 'driver' not in st.session_state or st.session_state['driver'] is None:
        try:
            st.session_state['driver'] = webdriver.Chrome()
            st.session_state['driver'].maximize_window()
            st.session_state['driver_initialized'] = True
            st.session_state['browser_initialized'] = False  # Ensure only one navigation to Google
        except Exception as e:
            st.error(f"Error initializing WebDriver: {e}")
            return None
    return st.session_state['driver']

# Quit browser and clean up WebDriver
def quit_browser():
    if 'driver' in st.session_state and st.session_state['driver'] is not None:
        try:
            st.session_state['driver'].quit()
            st.session_state['driver'] = None
            st.session_state['driver_initialized'] = False
            st.session_state['browser_initialized'] = False
            st.success("Browser quit successfully.")
        except Exception as e:
            st.error(f"Error quitting WebDriver: {e}")

# Ensure WebDriver is initialized only once
if not st.session_state.get('driver_initialized', False):
    driver = init_webdriver()
else:
    driver = st.session_state['driver']

# Main logic
def main():
    # Load Google only once per session
    if driver and not st.session_state.get('browser_initialized', False):
        try:
            driver.get('https://www.google.com')
            st.session_state['browser_initialized'] = True  # Ensure this runs only once
        except Exception as e:
            st.error(f"Error navigating to Google: {e}")

    # Input for user command
    command = st.text_input("Enter your command (e.g., 'Search for Streamlit on Google')")

    # Run button that will both generate and execute Selenium code
    if command and st.button("Run", key="run"):
        selenium_code = get_selenium_code(command)
        if selenium_code:
            st.session_state['selenium_code'] = selenium_code

            # Write the generated code to a Python file
            file_path = "generated_selenium_code.py"
            with open(file_path, "w") as file:
                file.write(selenium_code)

            # Provide download link for the generated code
            with open(file_path, "rb") as file:
                st.download_button(
                    label="Download Generated Code",
                    data=file,
                    file_name="generated_selenium_code.py",
                    mime="application/octet-stream",
                    key="download_button"
                )

            # Execute the generated Selenium code
            try:
                # Define a local scope for exec
                local_scope = {
                    'driver': driver,
                    'By': By,
                    'time': time,
                    'NoSuchElementException': NoSuchElementException,
                    'WebDriverWait': WebDriverWait,
                    'EC': EC,
                    'Keys': Keys,
                    'TimeoutException': TimeoutException  # Include TimeoutException in local scope
                }
                exec(selenium_code, {}, local_scope)
                st.success("Code executed successfully.")
            except TimeoutException:
                st.error("Operation timed out while waiting for elements. Please try again.")
            except Exception as e:
                st.error(f"An error occurred during execution:")
                st.error(traceback.format_exc())

    # Quit browser
    if st.button("Quit Browser", key="quit"):
        quit_browser()

if __name__ == "__main__":
    main()
