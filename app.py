import streamlit as st
import requests
import random
import string
import time
from bs4 import BeautifulSoup
import re

# Simulated AI function (mimicking Grok's capabilities)
def ai_generate_answer(field_name, question_text=None):
    """Generate a contextually relevant answer using AI."""
    if question_text:
        question_lower = question_text.lower()
        if "name" in question_lower:
            return random.choice(["Alex", "Jordan", "Taylor", "Sam"])
        elif "email" in question_lower:
            return f"{random.choice(['user', 'test', 'example'])}@gmail.com"
        elif "age" in question_lower:
            return str(random.randint(18, 80))
        elif "address" in question_lower:
            return f"{random.randint(100, 999)} Main St"
        elif "phone" in question_lower:
            return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    # Fallback based on field name if no question text
    if "name" in field_name.lower():
        return random.choice(["Alex", "Jordan", "Taylor", "Sam"])
    elif "email" in field_name.lower():
        return f"{random.choice(['user', 'test', 'example'])}@gmail.com"
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Function to get form fields from Google Form URL
def get_form_fields(form_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(form_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Log HTML for debugging
        st.write("Raw HTML snippet (first 3000 chars):", response.text[:3000])
        
        form_fields = {}
        
        # Find all 'entry.' fields using a broader approach
        entry_pattern = re.compile(r'entry\.\d+')
        all_elements = soup.find_all(True, {'name': entry_pattern})
        
        for field in all_elements:
            field_name = field.get('name')
            if field_name and '_sentinel' not in field_name:
                # Extract question text from nearby elements
                question_text = None
                parent = field.find_parent(['div', 'span', 'label'])
                if parent:
                    text_elem = parent.find(string=True, recursive=True)
                    if text_elem:
                        question_text = text_elem.strip()
                elif field.get('aria-label'):
                    question_text = field.get('aria-label')

                # Determine field type
                if field.name == 'input':
                    input_type = field.get('type', 'text')
                    if input_type in ['text', 'hidden']:
                        form_fields[field_name] = {'type': 'text', 'question': question_text}
                    elif input_type == 'radio':
                        if field_name not in form_fields:
                            options = [radio.get('value') for radio in soup.find_all('input', {'name': field_name, 'type': 'radio'}) if radio.get('value')]
                            if options:
                                form_fields[field_name] = {'type': 'radio', 'options': options, 'question': question_text}
                    elif input_type == 'checkbox':
                        if field_name not in form_fields:
                            options = [checkbox.get('value') for checkbox in soup.find_all('input', {'name': field_name, 'type': 'checkbox'}) if checkbox.get('value')]
                            if options:
                                form_fields[field_name] = {'type': 'checkbox', 'options': options, 'question': question_text}
                elif field.name == 'textarea':
                    form_fields[field_name] = {'type': 'text', 'question': question_text}
                elif field.name == 'select':
                    options = [option.get('value') for option in field.find_all('option') if option.get('value')]
                    if options:
                        form_fields[field_name] = {'type': 'dropdown', 'options': options, 'question': question_text}

        # Include hidden fields
        hidden_inputs = soup.find_all('input', {'type': 'hidden', 'name': entry_pattern})
        for hidden in hidden_inputs:
            field_name = hidden.get('name')
            if field_name and '_sentinel' not in field_name and field_name not in form_fields:
                value = hidden.get('value', '')
                form_fields[field_name] = {'type': 'hidden', 'value': value if value else None, 'question': None}

        if not form_fields:
            st.warning("No fields detected with initial parsing. Attempting broader search...")
            # Fallback: Search HTML string for entry.XXXX patterns
            entry_matches = re.findall(r'entry\.\d+', response.text)
            for field_name in set(entry_matches):
                if '_sentinel' not in field_name and field_name not in form_fields:
                    # Assume text field if no other info
                    form_fields[field_name] = {'type': 'text', 'question': None}

        return form_fields
    except Exception as e:
        st.error(f"Error fetching form fields: {e}")
        return {}

# Function to submit form with random or AI-generated data
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
st.title("Google Form Random Filler with AI")
st.write("Enter a public Google Form URL to fill it with AI-generated or random answers.")

# Input for Google Form URL
form_url = st.text_input("Google Form URL", "https://docs.google.com/forms/d/e/1FAIpQLSfq7LqAucQ1kMnK36uDn1s1MRMvPCwPVTyELCT7TCwOgQ79iw/viewform")

# Toggle for AI-generated answers
use_ai = st.checkbox("Use AI for contextual answers", value=True)

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

            if st.button("Submit Answers"):
                success_count = 0
                for i in range(num_submissions):
                    random_data = {}
                    for field, info in form_fields.items():
                        field_type = info['type']
                        question_text = info.get('question')
                        
                        if field_type == 'text':
                            random_data[field] = ai_generate_answer(field, question_text) if use_ai else generate_random_text()
                        elif field_type in ['radio', 'checkbox', 'dropdown']:
                            options = info['options']
                            random_data[field] = random.choice(options)
                        elif field_type == 'hidden':
                            random_data[field] = info['value'] if info['value'] else generate_random_text()
                    
                    if submit_form(submit_url, random_data):
                        success_count += 1
                    st.write(f"Submission {i+1}/{num_submissions} completed.")
                    time.sleep(1)
                
                st.success(f"Successfully submitted {success_count} out of {num_submissions} forms!")
        else:
            st.warning("Could not detect any form fields. Please check the URL or form structure.")
    else:
        st.error("Please enter a valid Google Form URL (e.g., containing 'forms.gle' or 'docs.google.com/forms').")
