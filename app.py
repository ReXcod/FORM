import streamlit as st
import requests
import random
import string
import time
from bs4 import BeautifulSoup
import re
from openai import OpenAI

# Function to generate random text (fallback)
def generate_random_text(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to generate AI answers using OpenAI
def generate_ai_answer(api_key, field_name, question_text=None):
    """Generate a contextually relevant answer using OpenAI API."""
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"Generate a realistic answer for a form field named '{field_name}'"
        if question_text:
            prompt += f" with the question '{question_text}'"
        prompt += ". Keep it short and appropriate."

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a lightweight model; upgrade to "gpt-4" if desired
            messages=[
                {"role": "system", "content": "You are a helpful assistant generating realistic form answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return generate_random_text()  # Fallback to random text on error

# Function to get form fields from Google Form URL
def get_form_fields(form_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(form_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        st.write("Raw HTML snippet (first 3000 chars):", response.text[:3000])
        
        form_fields = {}
        
        # Initial parsing
        all_elements = soup.find_all(['input', 'textarea', 'select'], {'name': lambda x: x and 'entry.' in x})
        for field in all_elements:
            field_name = field.get('name')
            if field_name and '_sentinel' not in field_name:
                question_text = None
                parent = field.find_parent(['div', 'span', 'label'])
                if parent:
                    text_elem = parent.find(string=True, recursive=True)
                    if text_elem:
                        question_text = text_elem.strip()
                elif field.get('aria-label'):
                    question_text = field.get('aria-label')

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

        # Fallback parsing
        if not form_fields or len(form_fields) < 2:
            st.warning("Initial parsing found insufficient fields. Attempting broader search...")
            entry_matches = set(re.findall(r'entry\.\d+', response.text))
            for field_name in entry_matches:
                if '_sentinel' not in field_name and field_name not in form_fields:
                    field_elem = soup.find('input', {'name': field_name})
                    if field_elem and field_elem.get('type') == 'radio':
                        options = [radio.get('value') for radio in soup.find_all('input', {'name': field_name, 'type': 'radio'}) if radio.get('value')]
                        if options:
                            form_fields[field_name] = {'type': 'radio', 'options': options, 'question': None}
                    elif field_elem and field_elem.get('type') == 'checkbox':
                        options = [checkbox.get('value') for checkbox in soup.find_all('input', {'name': field_name, 'type': 'checkbox'}) if checkbox.get('value')]
                        if options:
                            form_fields[field_name] = {'type': 'checkbox', 'options': options, 'question': None}
                    else:
                        form_fields[field_name] = {'type': 'text', 'question': None}

        return form_fields
    except Exception as e:
        st.error(f"Error fetching form fields: {e}")
        return {}

# Function to submit form
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
st.title("Google Form Filler with OpenAI")
st.write("Enter a public Google Form URL and your OpenAI API key to fill it with AI-generated answers.")

# API Key input
api_key = st.text_input("OpenAI API Key", type="password")
if not api_key:
    st.warning("Please enter your OpenAI API key to use AI-generated answers.")

# Form URL input
form_url = st.text_input("Google Form URL", "https://docs.google.com/forms/d/e/1FAIpQLSfq7LqAucQ1kMnK36uDn1s1MRMvPCwPVTyELCT7TCwOgQ79iw/viewform")

# Toggle for AI
use_ai = st.checkbox("Use OpenAI for answers (requires API key)", value=True, disabled=not api_key)

if form_url and (not use_ai or api_key):
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
                            if use_ai and api_key:
                                random_data[field] = generate_ai_answer(api_key, field, question_text)
                            else:
                                random_data[field] = generate_random_text()
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
