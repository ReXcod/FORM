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
        
        # Log more HTML to ensure fields are visible
        st.write("Raw HTML snippet (first 3000 chars):", response.text[:3000])
        
        form_fields = {}

        # Find all elements with 'entry.' in the name attribute
        all_inputs = soup.find_all(['input', 'textarea', 'select'], {'name': lambda x: x and 'entry.' in x})
        for field in all_inputs:
            field_name = field.get('name')
            if field_name and '_sentinel' not in field_name:
                # Determine field type
                if field.name == 'input':
                    input_type = field.get('type', 'text')
                    if input_type in ['text', 'hidden']:
                        form_fields[field_name] = 'text'
                    elif input_type == 'radio':
                        if field_name not in form_fields:
                            options = [radio.get('value') for radio in soup.find_all('input', {'name': field_name, 'type': 'radio'}) if radio.get('value')]
                            if options:
                                form_fields[field_name] = options
                    elif input_type == 'checkbox':
                        if field_name not in form_fields:
                            options = [checkbox.get('value') for checkbox in soup.find_all('input', {'name': field_name, 'type': 'checkbox'}) if checkbox.get('value')]
                            if options:
                                form_fields[field_name] = options
                elif field.name == 'textarea':
                    form_fields[field_name] = 'text'
                elif field.name == 'select':
                    options = [option.get('value') for option in field.find_all('option') if option.get('value')]
                    if options:
                        form_fields[field_name] = options

        # Include hidden fields with preset values
        hidden_inputs = soup.find_all('input', {'type': 'hidden', 'name': lambda x: x and 'entry.' in x})
        for hidden in hidden_inputs:
            field_name = hidden.get('name')
            if field_name and '_sentinel' not in field_name and field_name not in form_fields:
                value = hidden.get('value', '')
                form_fields[field_name] = value if value else 'text'

        return form_fields
    except Exception as e:
        st.error(f"Error fetching form fields: {e}")
        return {}

# Function to submit form with random data
def submit_form(form_url, form_data):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        st.write("Submitting payload:", form_data)
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

# Input for Google Form URL with default
form_url = st.text_input("Google Form URL", "https://docs.google.com/forms/d/e/1FAIpQLSfq7LqAucQ1kMnK36uDn1s1MRMvPCwPVTyELCT7TCwOgQ79iw/viewform")

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
                        if value == 'text':
                            random_data[field] = generate_random_text()
                        elif isinstance(value, list):  # MCQ, checkbox, or dropdown
                            random_data[field] = random.choice(value)
                        elif isinstance(value, str):  # Hidden field with preset value
                            random_data[field] = value
                    
                    if submit_form(submit_url, random_data):
                        success_count += 1
                    st.write(f"Submission {i+1}/{num_submissions} completed.")
                    time.sleep(1)
                
                st.success(f"Successfully submitted {success_count} out of {num_submissions} forms!")
        else:
            st.warning("Could not detect any form fields. Please check the URL or form structure.")
    else:
        st.error("Please enter a valid Google Form URL (e.g., containing 'forms.gle' or 'docs.google.com/forms').")
