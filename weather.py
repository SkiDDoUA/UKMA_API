import datetime as dt
import json
import requests
from flask import Flask, jsonify, request

API_TOKEN = "123"
WEATHER_API_KEY = ""

app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

def get_clothing_recommendation(temp_c, condition):
    recommendations = []
    
    if temp_c < 5:
        recommendations.append("a warm coat")
        recommendations.append("hat, scarf, and gloves")
    elif temp_c < 15:
        recommendations.append("a light jacket")
    else:
        recommendations.append("a t-shirt")
    
    if "rain" in condition.lower():
        recommendations.append("an umbrella")
    if "snow" in condition.lower():
        recommendations.append("waterproof boots")

    return recommendations

def fahrenheit_to_celsius(temp_f):
    return (temp_f - 32) * 5.0/9.0

def get_weather(location, date):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}"
    params = {'key': WEATHER_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = json.loads(response.text)
        main_weather = data['days'][0]
        temp_f = main_weather['temp']
        temp_c = fahrenheit_to_celsius(temp_f)
        condition = main_weather['conditions']
        recommendations = get_clothing_recommendation(temp_c, condition)
        return {
            "temp_c": temp_c,
            "condition": condition,
            "recommendations": recommendations
        }
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/")
def home_page():
    return "<p><h2>Weather SaaS Home.</h2></p>"

@app.route("/api/weather", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    
    token = json_data.get("token")
    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)
    
    location = json_data.get("location")
    date = json_data.get("date")

    weather_data = get_weather(location, date)
    
    result = {
        "requester_name": json_data.get("requester_name"),
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "location": location,
        "date": date,
        "weather": weather_data,
        "advice": f"Based on the weather, consider wearing {', '.join(weather_data['recommendations'])}."
    }

    return jsonify(result)
