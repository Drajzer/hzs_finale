from flask import Flask,render_template, Response,request, redirect, url_for,session,send_from_directory
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
import ast
from geopy.geocoders import Nominatim

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes
current_directory = os.path.dirname(os.path.abspath(__file__))

# Set the template folder to the current directory
app.template_folder = current_directory
client = OpenAI(
        api_key=""
    )




@app.route('/')
def index():
    return render_template('index.html', first = "", second = "", third = "", fourth = "", fifth = "", sixth = "", seventh = "", eight = "", ninth = "")

@app.route('/relaxed')
def relaxed():
    return render_template('relaxed.html')

@app.route('/adventure')
def adventure():
    return render_template('adventure.html')

@app.route('/final', methods=['POST'])
def process_html_elements():
    data = request.json

    elements = data['elements']

    return render_template('final.html', code=elements[0])


def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="Firefox 89")
    location = geolocator.geocode(city_name)
    
    if location:
        latitude = location.latitude
        longitude = location.longitude
        return latitude, longitude
    else:
        return None


def parse_string(input_string):
    # Split the string at the colon
    split_string = input_string.split(":")

    # If there is something after the colon
    if len(split_string) > 1:
        # Return everything after the colon
        return split_string[1].strip()

    # If there is no colon in the string
    return None

def parseContent(chat_message):
    try:
        match = re.search(r"content='(.*?)'", chat_message)
        if match:
            content = match.group(1)
            
            activities_list = [activity.strip() for activity in content.split(',')]
            
            return activities_list
        else:
            return []
    except Exception as e:
        return []


def get_closest_place(api_key, current_location, interest, radius=5000, types='establishment'):
    params = {
        'key': api_key,
        'location': current_location,
        'radius': radius,
        'types': types,
        'keyword': interest
    }

    response = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params=params)
    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        closest_place = min(data['results'], key=lambda x: x.get('distance', float('inf')))
        return closest_place
    else:
        return None


def handleAI(interests, location):
    prompt = f'''
    You are a touristic guide. You need to suggest a variety of activities 9 activites or 9 locations that align with the person's preferences. 
    Give me categories which I can search on Google places. Activites are: {', '.join(interests)}.
    Locations should exist in {location}. Also, add 2 relaxed activities.
    Only give activites not exact places. Answers should be in format activity then comma then activity then comma etc.
    Give exact answers, no more than 9. Answers should be one word per activity.
    Names of categories on serbian latinica.
    Do not include food or drinks.
    '''
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": prompt}
    ]
    )

    result = parseContent(str(completion.choices[0].message))
    

    return result

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(current_directory, 'static'), filename)

def exactMatch(jsonList):
    matches =[
            (["Relaxed", "Nature", "Group"], ['park', 'zoo', 'aquarium', 'campground', 'museum', 'restaurant', 'cafe', 'art_gallery', 'botanical_garden', 'picnic_area', 'tourist_attraction']), 
            (["Relaxed", "Urban", "Group"], ['museum', 'art_gallery', 'shopping_mall', 'movie_theater', 'restaurant', 'cafe', 'city_hall', 'library', 'park', 'tourist_attraction', 'tourist_attraction']),
            (['Relaxed', 'Nature', 'Solo'], ['park', 'botanical_garden', 'zoo', 'aquarium', 'museum', 'art_gallery', 'cafe', 'nature_reserve', 'hiking_trail', 'scenic_lookout', 'tourist_attraction']),
            (['Active', 'Nature', 'Group'], ['park', 'hiking_trail', 'amusement_park', 'zoo', 'campground', 'beach', 'gym', 'bicycle_store', 'sports_complex', 'stadium', 'tourist_attraction']),
            (['Active', 'Urban', 'Group'], ['gym', 'stadium', 'amusement_park', 'bowling_alley', 'shopping_mall', 'movie_theater', 'night_club', 'sports_bar', 'park', 'escape_room', 'tourist_attraction']),
            (['Active', 'Nature', 'Solo'], ['park', 'hiking_trail', 'gym', 'botanical_garden', 'zoo', 'bicycle_store', 'nature_reserve', 'campground', 'rock_climbing', 'beach', 'tourist_attraction']),
            (['Active', 'Urban', 'Solo'], ['gym', 'stadium', 'park', 'art_gallery', 'library', 'shopping_mall', 'cafe', 'museum', 'movie_theater', 'skate_park', 'tourist_attraction'])]


    for currentMatch in matches:
        if jsonList == currentMatch[0]:
            return currentMatch[1]
    
    # if func returns empty list you should send error to user
    return []


@app.route('/api/interests', methods=['POST'])
def handleInterests():
    data = request.json
    interests = exactMatch(data['interests'])
    if interests == []:
      return json.dumps({'error': 'No match found'})

    loc = data['location']

    location = loc['query']


    current_location = get_coordinates(location)
    langitude = current_location[0]
    longitude = current_location[1]
    coorinates = f"{langitude},{longitude}"
    lista=[]
    gapikey= ""
    for interest in interests:
        closest_place = get_closest_place(gapikey, coorinates, interest)
        if closest_place:
            lista.append(closest_place["name"])
    return json.dumps({'list':lista})


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)