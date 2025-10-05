# NASA Weather Insights - Backend Setup

## Overview
This Flask backend provides probability-based weather predictions using historical data from **NASA POWER API** and geolocation from OpenStreetMap Nominatim.

## Features
- ✅ Geolocation conversion (text → coordinates)
- ✅ Historical weather data retrieval (10 years from NASA)
- ✅ Probability calculations for extreme conditions
- ✅ Smart predictions with helpful tips
- ✅ Error handling and user feedback
- ✅ **100% NASA Data - No API keys needed!**

## Project Structure
```
nasa-weather-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html         # Base template with navbar/footer
│   ├── index.html        # Home page with form
│   └── results.html      # Results display page
└── static/
    ├── css/
    │   └── style.css     # Custom styles
    └── images/
        └── nasa-logo1.jpg
```

## Setup Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. No API Credentials Needed!
**NASA POWER API is completely free and open** - no signup required!

### 3. Run the Application
```bash
python app.py
```

The app will be available at: `http://localhost:5000`

## API Endpoints

### `GET /`
- Renders the home page with location and date/time input form

### `POST /results`
- Processes form submission
- Retrieves historical weather data from NASA
- Calculates probabilities
- Displays prediction results

## How It Works

### 1. **Geolocation Processing**
```python
location = "Douala, Cameroon"
coords = get_coordinates(location)
# Returns: {'lat': 4.0511, 'lon': 9.7679, 'display_name': '...'}
```

### 2. **Historical Data Retrieval (NASA POWER API)**
- Fetches weather data for the same calendar day over the past **10 years**
- Parameters: temperature (°C), wind speed (m/s), precipitation (mm)
- Data from **1981 to present** available
- **Single API call** for all years (fast performance)

### 3. **Probability Calculation**
Thresholds:
- **Very Hot**: Temperature > 30°C
- **Very Cold**: Temperature < 10°C
- **Very Windy**: Wind speed > 10 m/s
- **Very Wet**: Precipitation > 10 mm/day

Formula:
```
Probability = (Days meeting condition / Total days) × 100
```

### 4. **Main Prediction**
The condition with the highest probability becomes the main prediction:
- If all probabilities are 0, prediction is "comfortable"
- Otherwise, the max probability determines the prediction

### 5. **Tips Generation**
Based on the main prediction, the app provides actionable advice:
- Very Hot → Stay hydrated, use sunscreen
- Very Cold → Dress warmly, watch for ice
- Very Windy → Secure objects, careful outdoors
- Very Wet → Bring umbrella, check flood warnings

## Error Handling

The backend handles:
- ❌ Invalid locations (Nominatim returns no results)
- ❌ Missing form data
- ❌ API failures (NASA timeout/errors)
- ❌ Invalid date formats
- ❌ Network issues

All errors display user-friendly messages via Flask flash messages.

## Production Deployment

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Customization

### Adjust Weather Thresholds
Edit in `calculate_probabilities()`:
```python
HOT_THRESHOLD = 30  # Change to 35 for hotter climates
COLD_THRESHOLD = 10  # Change to 0 for colder regions
WIND_THRESHOLD = 10  # Adjust based on location
RAIN_THRESHOLD = 10  # Adjust based on rainfall patterns
```

### Change Historical Years Range
Edit in `/results` route (line 176):
```python
historical_data = get_historical_weather_nasa(..., years=10)  
# Change to years=20 for 20 years, years=5 for 5 years
```

### Add More Weather Parameters
NASA POWER supports many parameters. Modify the request:
```python
parameters = 'T2M,T2M_MAX,T2M_MIN,WS10M,WS10M_MAX,PRECTOTCORR,RH2M'
# RH2M = Relative Humidity at 2 Meters
```

## Troubleshooting

### "Could not retrieve NASA weather data"
- Check your internet connectivity
- NASA POWER API might be temporarily down
- Try reducing years (from 10 to 5)

### "Could not find the specified location"
- Try more specific location names: "Douala, Littoral, Cameroon"
- Use city names instead of addresses
- Check spelling
- **Built-in fallbacks** for: Douala, Yaoundé, Paris, London, New York, Tokyo, Lagos, Nairobi, Cairo

### Slow Loading
- Reduce years in the API call (10 years → 5 years)
- Check internet speed
- NASA API responds in 5-15 seconds for 10 years

## NASA Data Source

**NASA POWER (Prediction Of Worldwide Energy Resources)**
- URL: https://power.larc.nasa.gov/
- Data: Global meteorological and solar datasets
- Coverage: 1981 to near real-time
- Resolution: Daily values
- **Completely Free and Open Access**

## License
Built for NASA Space Apps Challenge 2025 - Douala

## Support
For issues or questions about:
- NASA POWER API: https://power.larc.nasa.gov/docs/
- OpenStreetMap Nominatim: https://nominatim.org/