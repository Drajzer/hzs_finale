from flask import Flask,render_template, Response,request, redirect, url_for,session
import json
import os 
import requests 
from openai import OpenAI
from flask_cors import CORS
import mariadb
import bcrypt
import jwt
import datetime
import re

app = Flask(__name__, template_folder='templates',static_folder='static')
CORS(app)  # Enable CORS for all routes

client = OpenAI(
        api_key="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"
    )


@app.route('/')
def index():
    return render_template('index.html')

def sortCategories(categories):

    return "ok"
def parse_categories(message_str):
    # Extract content from the message
    content_match = re.search(r"content='(.*?)'", message_str, re.DOTALL)
    if content_match:
        content = content_match.group(1)
        # Extract categories from the content
        categories = re.findall(r'([a-zA-Z]+):', content)
        return categories
    else:
        return None


def handleAI(interests, location):
    # Set your OpenAI API key
    prompt = f'''
    You are a touristic guide. You need to suggest a variety of activities 9 activites or 9 locations that align with the person's preferences. 
    Give me categories which I can search on Google places. Activites are: {', '.join(interests)}.
    Let's assume a persona who prefers Adventure, Nature, and Group activities. 
    Here's how the prioritization might look (expressed as percentages, where a higher percentage indicates a higher priority for this persona). 
    Locations should exist in {location[0]}, {location[1]}. Also, add 2 relaxed activities.
    Your response should be in format one activity per row without aditional text.
    '''
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": prompt}
    ]
    )

    result = parse_categories(str(completion.choices[0].message))
    print(result)

    return "ok"

@app.route('/api/interests', methods=['POST'])
def handleInterests():
    data = request.json
    interests = data['interests']  
    loc = data['location']

    location = [loc['country'], loc['city']]

    print(interests)
    print(location)
    handleAI(interests,location)

    return 'OK'


@app.route('/location', methods=['GET'])
def location():
    return render_template('location.html')



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)