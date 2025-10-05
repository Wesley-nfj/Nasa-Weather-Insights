from flask import Flask, render_template, request, redirect, url_for, flash
import requests
from datetime import datetime, timedelta
import os
from statistics import mean
from dotenv import load_dotenv  

load_dotenv()  

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'app secret key')


def get_coordinates(location):
    """
    Turns a location name into latitude and longitude using the Nominatim API.
    Includes some common cities as backup if the API does not respond.
    """
    # Quick fallback for common cities (helps if API is down or slow)
    fallback_cities = {
        'douala': {'lat': 4.0511, 'lon': 9.7679, 'display_name': 'Douala, Cameroon'},
        'yaounde': {'lat': 3.8480, 'lon': 11.5021, 'display_name': 'Yaoundé, Cameroon'},
        'paris': {'lat': 48.8566, 'lon': 2.3522, 'display_name': 'Paris, France'},
        'london': {'lat': 51.5074, 'lon': -0.1278, 'display_name': 'London, UK'},
        'new york': {'lat': 40.7128, 'lon': -74.0060, 'display_name': 'New York, USA'},
        'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'display_name': 'Tokyo, Japan'},
        'lagos': {'lat': 6.5244, 'lon': 3.3792, 'display_name': 'Lagos, Nigeria'},
        'nairobi': {'lat': -1.2864, 'lon': 36.8172, 'display_name': 'Nairobi, Kenya'},
        'cairo': {'lat': 30.0444, 'lon': 31.2357, 'display_name': 'Cairo, Egypt'},
    }

    location_lower = location.lower().strip()
    if location_lower in fallback_cities:
        return fallback_cities[location_lower]

    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': location, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'NASA-Weather-Insights/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()

        if not data:
            # Try a fuzzy match if not found
            for city, coords in fallback_cities.items():
                if city in location_lower or location_lower in city:
                    return coords
            return None

        return {
            'lat': float(data[0]['lat']),
            'lon': float(data[0]['lon']),
            'display_name': data[0]['display_name']
        }
    except requests.exceptions.Timeout:
        for city, coords in fallback_cities.items():
            if city in location_lower or location_lower in city:
                return coords
        return None
    except Exception as e:
        print(f"Geolocation error: {e}")
        return None


def get_historical_weather_nasa(lat, lon, target_date, years=5):
    """
    Pulls weather data for the same calendar day across past years from NASA POWER.
    """
    try:
        current_year = datetime.now().year
        start_year = current_year - years
        end_year = current_year - 1
        month = target_date.month
        day = target_date.day

        start_date = f"{start_year}{month:02d}{day:02d}"
        end_date = f"{end_year}{month:02d}{day:02d}"

        print(f"Fetching NASA data from {start_date} to {end_date}")

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            'parameters': 'T2M,T2M_MAX,T2M_MIN,WS10M,WS10M_MAX,PRECTOTCORR',
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }

        response = requests.get(url, params=params, timeout=30)
        print(f"NASA API status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text[:300]}")
            return []

        data = response.json()
        if 'properties' not in data or 'parameter' not in data['properties']:
            print("Bad response format from NASA")
            return []

        params_data = data['properties']['parameter']
        all_data = []

        for year in range(start_year, end_year + 1):
            date_str = f"{year}{month:02d}{day:02d}"
            temp_data = params_data.get('T2M', {})
            if date_str in temp_data:
                all_data.append({
                    'year': year,
                    'date': date_str,
                    'temp_avg': params_data.get('T2M', {}).get(date_str),
                    'temp_max': params_data.get('T2M_MAX', {}).get(date_str),
                    'temp_min': params_data.get('T2M_MIN', {}).get(date_str),
                    'wind_avg': params_data.get('WS10M', {}).get(date_str),
                    'wind_max': params_data.get('WS10M_MAX', {}).get(date_str),
                    'precip': params_data.get('PRECTOTCORR', {}).get(date_str)
                })

        print(f"✓ Got data for {len(all_data)} years")
        return all_data

    except Exception as e:
        print(f"NASA API error: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_weather_data(historical_data):
    """Looks through the historical data and figures out trends and conditions."""
    if not historical_data:
        return None

    valid_temps_avg = [d['temp_avg'] for d in historical_data if d.get('temp_avg') is not None]
    valid_temps_max = [d['temp_max'] for d in historical_data if d.get('temp_max') is not None]
    valid_temps_min = [d['temp_min'] for d in historical_data if d.get('temp_min') is not None]
    valid_winds_avg = [d['wind_avg'] for d in historical_data if d.get('wind_avg') is not None]
    valid_winds_max = [d['wind_max'] for d in historical_data if d.get('wind_max') is not None]
    valid_precip = [d['precip'] for d in historical_data if d.get('precip') is not None]

    if not valid_temps_avg:
        return None

    avg_temp = round(mean(valid_temps_avg), 1)
    min_temp = round(min(valid_temps_min), 1) if valid_temps_min else avg_temp
    max_temp = round(max(valid_temps_max), 1) if valid_temps_max else avg_temp
    avg_wind = round(mean(valid_winds_avg), 1) if valid_winds_avg else 0
    max_wind = round(max(valid_winds_max), 1) if valid_winds_max else 0
    avg_rain = round(mean(valid_precip), 1) if valid_precip else 0
    max_rain = round(max(valid_precip), 1) if valid_precip else 0

    main_prediction = determine_main_condition(avg_temp, max_temp, avg_rain, max_wind)

    total_days = len(historical_data)
    probs = {
        'very_hot': round((sum(1 for t in valid_temps_max if t > 30) / total_days) * 100) if total_days > 0 else 0,
        'very_cold': round((sum(1 for t in valid_temps_min if t < 10) / total_days) * 100) if total_days > 0 else 0,
        'very_windy': round((sum(1 for w in valid_winds_max if w > 10) / total_days) * 100) if total_days > 0 else 0,
        'very_wet': round((sum(1 for r in valid_precip if r > 10) / total_days) * 100) if total_days > 0 else 0,
    }

    results = {
        'main_prediction': main_prediction,
        'temp_range': f"{min_temp}°C - {max_temp}°C",
        'avg_temp': avg_temp,
        'wind_info': f"{avg_wind} m/s (max: {max_wind} m/s)",
        'rain_info': f"{avg_rain} mm (max: {max_rain} mm)",
        'probabilities': probs,
        'confidence': f"{total_days} years of NASA data"
    }

    return results


def determine_main_condition(avg_temp, max_temp, avg_rain, max_wind):
    """Figures out the main weather type based on temperature, wind, and rain."""
    if avg_rain > 10:
        return "Rainy"
    elif max_temp > 32:
        return "Hot"
    elif avg_temp < 10:
        return "Cold"
    elif max_wind > 12:
        return "Windy"
    elif 18 <= avg_temp <= 25:
        return "Pleasant"
    elif avg_temp > 25:
        return "Warm"
    else:
        return "Cool"


def generate_tip(main_prediction, temp_range, rain_info):
    """Gives a short tip based on the prediction."""
    tips = {
        'Hot': f"Hot day ahead ({temp_range}). Drink water often, wear light clothes, and avoid too much sun.",
        'Warm': f"Warm and comfy ({temp_range}). Great for outdoor stuff, just stay hydrated.",
        'Pleasant': f"Perfect day ({temp_range}). Ideal for outdoor plans!",
        'Cool': f"Cool temperatures ({temp_range}). A light jacket should be fine.",
        'Cold': f"Cold weather ({temp_range}). Bundle up properly.",
        'Rainy': f"Expect rain ({rain_info}). Carry an umbrella or raincoat.",
        'Windy': f"Strong winds expected. Be careful with outdoor setups or travel."
    }
    return tips.get(main_prediction, "Check the weather before heading out.")


@app.route('/')
def home():
    """Main page with the form."""
    return render_template('index.html')


@app.route('/results', methods=['POST'])
def results():
    """Handles the form submission and shows prediction results."""
    try:
        location = request.form.get('location', '').strip()
        datetime_str = request.form.get('datetime', '').strip()

        if not location or not datetime_str:
            flash('Please enter both location and date/time.', 'error')
            return redirect(url_for('home'))

        target_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        coords = get_coordinates(location)
        if not coords:
            flash('Could not find that location. Try again.', 'error')
            return redirect(url_for('home'))

        historical_data = get_historical_weather_nasa(coords['lat'], coords['lon'], target_datetime, years=10)
        if not historical_data:
            flash('Could not get NASA weather data. Try again.', 'error')
            return redirect(url_for('home'))

        analysis = analyze_weather_data(historical_data)
        if not analysis:
            flash('Error analyzing the data.', 'error')
            return redirect(url_for('home'))

        tip = generate_tip(
            analysis['main_prediction'],
            analysis['temp_range'],
            analysis['rain_info']
        )

        return render_template(
            'results.html',
            city=location,
            datetime=target_datetime.strftime('%B %d, %Y at %I:%M %p'),
            main_prediction=analysis['main_prediction'],
            temp_range=analysis['temp_range'],
            avg_temp=analysis['avg_temp'],
            wind_info=analysis['wind_info'],
            rain_info=analysis['rain_info'],
            probs=analysis['probabilities'],
            confidence=analysis['confidence'],
            tip=tip
        )

    except ValueError:
        flash('Invalid date/time format.', 'error')
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error in results route: {e}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
