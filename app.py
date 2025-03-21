import streamlit as st
import requests
import random
import string
import time
from bs4 import BeautifulSoup

# Function to generate random text
def generate_random_text(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to get form fields from Google Form URL
def get_form_fields(form_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(form_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        form_fields = {}
        
        # Find all input fields
        inputs = soup.find_all('input')
        for input_field in inputs:
            if input_field.get('name'):
                field_name = input_field.get('name')
                field_type = input_field.get('type', 'text')
                form_fields[field_name] = field_type
                
        # Find all multiple choice fields (radio/checkboxes)
        mcq_fields = soup.find_all('div', {'role': 'radiogroup'}) + soup.find_all('div', {'role': 'checkbox'})
        for mcq in mcq_fields:
            options = [opt.get('data-answer-value') for opt in mcq.find_all('div') if opt.get('data-answer-value')]
            if options:
                form_fields[mcq.get('data-params', '').split('[')[0]] = options
                
        return form_fields
    except Exception as e:
        st.error(f"Error fetching form fields: {e}")
        return {}

# Function to submit form with random data
def submit_form(form_url, form_data):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.post(form_url, data=form_data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            st.write(f"Submission failed with status code: {response.status_code}")
            st.write(f"Response: {response.text[:500]}")  # Show first 500 chars for debugging
            return False
    except Exception as e:
        st.error(f"Error submitting form: {e}")
        return False

# Streamlit UI
st.title("Google Form Random Filler")
st.write("Enter a public Google Form URL to automatically fill it with random answers.")

# Input for Google Form URL
form_url = st.text_input("Google Form URL", "")

if form_url:
    # Check if the URL is a valid Google Form URL
    if "forms.gle" in form_url or "docs.google.com/forms" in form_url:
        # Convert short URL to full URL if needed
        if "forms.gle" in form_url:
            response = requests.get(form_url, allow_redirects=True)
            form_url = response.url

        # Get the form's submission URL
        viewform_url = form_url if "viewform" in form_url else form_url.replace("edit", "viewform")
        submit_url = viewform_url.replace("viewform", "formResponse")

        # Fetch form fields
        form_fields = get_form_fields(viewform_url)

        if form_fields:
            st.write("Detected Form Fields:")
            st.json(form_fields)

            # Number of submissions
            num_submissions = st.slider("Number of Submissions", 1, 10, 1)

            if st.button("Submit Random Answers"):
                success_count = 0
                for i in range(num_submissions):
                    random_data = {}
                    for field, value in form_fields.items():
                        if isinstance(value, str):  # Text field
                            random_data[field] = generate_random_text()
                        elif isinstance(value, list):  # MCQ field
                            random_data[field] = random.choice(value)
                    
                    # Submit the form
                    if submit_form(submit_url, random_data):
                        success_count += 1
                    st.write(f"Submission {i+1}/{num_submissions} completed.")
                    time.sleep(1)  # 1-second delay to avoid rate-limiting
                
                st.success(f"Successfully submitted {success_count} out of {num_submissions} forms!")
        else:
            st.warning("Could not detect any form fields. Please check the URL.")
    else:
        st.error("Please enter a valid Google Form URL (e.g., containing 'forms.gle' or 'docs.google.com/forms').")

# Instructions for deployment
st.markdown("""
### How to Deploy:
1. Save this code in a file named `app.py`.
2. Create a `requirements.txt` file with:
