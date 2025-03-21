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

        # Look for input fields with 'entry.' IDs (Google Forms convention)
        inputs = soup.find_all('input', {'name': lambda x: x and 'entry.' in x})
        for input_field in inputs:
            field_name = input_field.get('name')
            if field_name:
                form_fields[field_name] = 'text'

        # Find multiple-choice fields (radio buttons)
        mcq_fields = soup.find_all('div', {'role': 'radiogroup'})
        for mcq in mcq_fields:
            field_name = None
            options = []
            for input_field in mcq.find_all('input', {'name': lambda x: x and 'entry.' in x}):
                field_name = input_field.get('name')
                options = [opt.get('value') for opt in mcq.find_all('input', {'type': 'radio'}) if opt.get('value')]
            if field_name and options:
                form_fields[field_name] = options

        # Find checkbox fields
        checkbox_fields = soup.find_all('div', {'role': 'checkbox'})
        for checkbox in checkbox_fields:
            field_name = None
            options = []
            for input_field in checkbox.find_all('input', {'name': lambda x: x and 'entry.' in x}):
                field_name = input_field.get('name')
                options = [opt.get('value') for opt in checkbox.find_all('input', {'type': 'checkbox'}) if opt.get('value')]
            if field_name and options:
                form_fields[field_name] = options

        return form_fields
    except Exception as e:
        st.error(f"Error fetching form fields: {e}")
        return {}

# Function to submit form with random data
def submit_form(form_url, form_data):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        st.write("Submitting payload:", form_data)  # Debug payload
        response = requests.post(form_url, data=form_data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            st.write(f"Submission failed with status code: {response.status_code}")
            st.write(f"Response: {response.text[:500]}")
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
    if "forms.gle" in form_url or "docs.google.com/forms" in form_url:
        if "forms.gle" in form_url:
            response = requests.get(form_url, allow_redirects=True)
            form_url = response.url

        viewform_url = form_url if "viewform" in form_url else form_url.replace("edit", "viewform")
        submit_url = viewform_url.replace("viewform", "formResponse")

        form_fields = get_form_fields(viewform_url)

        if form_fields:
            st.write("Detected Form Fields:")
            st.json(form_fields)

            num_submissions = st.slider("Number of Submissions", 1, 10, 1)

            if st.button("Submit Random Answers"):
                success_count = 0
                for i in range(num_submissions):
                    random_data = {}
                    for field, value in form_fields.items():
                        if isinstance(value, str) and value == 'text':
                            random_data[field] = generate_random_text()
                        elif isinstance(value, list):  # MCQ or checkbox
                            random_data[field] = random.choice(value)
                    
                    if submit_form(submit_url, random_data):
                        success_count += 1
                    st.write(f"Submission {i+1}/{num_submissions} completed.")
                    time.sleep(1)
                
                st.success(f"Successfully submitted {success_count} out of {num_submissions} forms!")
        else:
            st.warning("Could not detect any form fields. Please check the URL.")
    else:
        st.error("Please enter a valid Google Form URL (e.g., containing 'forms.gle' or 'docs.google.com/forms').")
