import streamlit as st
import requests
import random
import time
from openai import OpenAI
from bs4 import BeautifulSoup

# Function to parse Google Forms fields
def get_form_fields(form_url):
    """Extracts form fields from the given Google Form URL."""
    try:
        response = requests.get(form_url)
        if response.status_code != 200:
            st.error(f"Failed to fetch the form. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        fields = {}

        for field in soup.find_all("div", class_="Qr7Oae"):
            field_name = field.get_text(strip=True)
            if field_name:
                fields[field_name] = ""

        return fields
    except Exception as e:
        st.error(f"Error parsing the Google Form: {e}")
        return []

# Function to generate AI-based answers
def generate_ai_answer(api_key, field_name, question_text=None):
    """Generate a contextually relevant answer using OpenAI API."""
    try:
        client = OpenAI(api_key=api_key)  # Correct API usage
        prompt = f"Generate a realistic answer for a form field named '{field_name}'."
        if question_text:
            prompt += f" The question is: '{question_text}'."
        prompt += " Keep it short and appropriate."

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
        return generate_random_text()  # Fallback if OpenAI fails

# Function to generate random fallback text
def generate_random_text():
    """Generate a random filler text for form fields."""
    responses = [
        "This is my response.",
        "Thank you for the opportunity!",
        "I appreciate the consideration.",
        "Looking forward to participating!",
        "Here is my answer to the question."
    ]
    return random.choice(responses)

# Streamlit UI
st.title("Google Form Auto-Filler")

# Input fields
form_url = st.text_input("Enter Google Form URL:")
api_key = "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"

if st.button("Fetch Form Fields"):
    if not form_url:
        st.error("Please enter a Google Form URL.")
    else:
        fields = get_form_fields(form_url)
        if fields:
            st.success("Form fields extracted successfully!")
            for field in fields.keys():
                st.write(f"- {field}")

if st.button("Generate AI Responses"):
    if not form_url or not api_key:
        st.error("Please enter both the Google Form URL and OpenAI API Key.")
    else:
        fields = get_form_fields(form_url)
        if fields:
            responses = {}
            for field in fields.keys():
                responses[field] = generate_ai_answer(api_key, field)
                time.sleep(1.5)  # Rate limiting to prevent API bans

            st.success("AI-generated responses:")
            for field, response in responses.items():
                st.write(f"**{field}:** {response}")
