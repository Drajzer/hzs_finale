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
client = OpenAI(
    api_key="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"
    
)

app = Flask(__name__, template_folder='templates',static_folder='static')
CORS(app)  # Enable CORS for all routes
exp = 30*60

host = "127.0.0.1"
port = 3306
app.config['SECRET_KEY'] = "panklav"
exptime = 30*60  
conn = mariadb.connect(
    user="ekr",
    password="025864",
    host=host,
    port=port,
    database="hzs"
)

curr = conn.cursor()

def auth(token, userId,user):
    try:
        payload = jwt.decode(token, key=app.config['SECRET_KEY'],algorithms=['HS256'])
    except jwt.ExpiredSignatureError as expiredError:
        return False
    except:
        return False
    if payload['email'] == user and payload['id'] == userId:
        print(user,"is authenticated, token is valid",userId)
        return True
    
    return False


def checkHash(password: str, passwordHash: str) -> bool:
  passwordBytes = password.encode("utf-8")
  result = bcrypt.checkpw(passwordBytes, passwordHash.encode("utf-8"))
  
  return result


@app.route('/')
def index():
    return render_template('index.html')

def sortCategories(categories):

    return "ok"

def handleAI(interests, location):
    prompt = f"The user is in {location[0]}, {location[1]} and is interested in {', '.join(interests)}."
    print(prompt)

    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      prompt=prompt,
      temperature=0.9,
      max_tokens=150,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6,
      stop=["\n", " Human:", " AI:"]
    )

    return json.dumps({'generated_text': completion.choices[0].text.strip()})


@app.route('/api/interests', methods=['POST'])
def handleInterests():
    data = request.json
    interests = data['interests']  
    loc = data['location']

    location = [loc['country'], loc['city']]
    if session:
        if session['jwt'] is not None:
            x = session['jwt']
            y = jwt.decode(x,app.secret_key,algorithms=['HS256'])
            print(y)
            if auth(x,y['id'],y['email']):
                print("User is authenticated")
                curr.execute("UPDATE users SET categories = ? WHERE id = ?", (json.dumps(interests), y['id']))
                conn.commit()
                print("Interests saved")


    print(interests)
    print(location)
    #handleAI(interests,location)




    return 'OK'




@app.route('/location', methods=['GET'])
def location():
    return render_template('location.html')


@app.route('/register',methods=['POST','GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    email = request.form['username']
    password = request.form['password']
    passwordHash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    curr.execute("INSERT INTO users (email,password) VALUES (?,?)",(email,passwordHash))
    conn.commit()
    session['jwt'] = jwt.encode({'email':email,'id':curr.lastrowid,'exp':datetime.datetime.utcnow() + datetime.timedelta(seconds=exp)},app.secret_key,algorithm='HS256')
    print(session['jwt'])
    return redirect(url_for('index'))

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form['username']
    password = request.form['password']
    print(email,password)
    sql = "SELECT password FROM users WHERE email=?"
    curr.execute(sql,[email])
    if curr.rowcount == 0:
        return render_template('login.html',message="User not found or password is incorrect")
    user = curr.fetchone()[0]
    if user is None:
        return render_template('login.html',message="User not found or password is incorrect")
    if checkHash(password,user):
        print("User found")
        session['jwt'] = jwt.encode({'email':email,'id':user[0],'exp':datetime.datetime.utcnow() + datetime.timedelta(seconds=exp)},app.secret_key,algorithm='HS256')
        return render_template('index.html',message="Login successful")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('jwt',None)
    return render_template('index.html')


@app.route('/dashboard', methods=['GET'])
def handleDashboard():
    if 'jwt' in session:
        token = session['jwt']
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        if auth(token, decoded_token['id'], decoded_token['email']):
            curr.execute("SELECT categories FROM users WHERE id = ?", (decoded_token['id'],))
            categories = curr.fetchone()
            if categories is not None:
                return json.dumps(categories)
    return 'Unauthorized', 401

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)