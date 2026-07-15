# SC Device Hub
This repository contains the source code for the `sc_device_hub` package.

The app is a small FastAPI dashboard for monitoring reachability and toggling Tuya outlets.

It is intended for personal or local-network use and does not include production authentication or any other extra security by default. If you expose the app beyond a trusted LAN, add authentication, TLS, and restrict access to the API endpoints.

## Environment Variables
The following environment variables can be set to configure already included automations:

| Variable | Purpose | Example |
|---|---|---|
| `TUYA_ACCESS_ID` | Tuya IoT Platform Access ID | `1234567890abcdef` |
| `TUYA_ACCESS_KEY` | Tuya IoT Platform Access Key | `abcdef1234567890abcdef1234567890` |
| `HOST` | Host address used by the development server | `0.0.0.0` |
| `PORT` | Port used by the development server | `8000` |

## Installation
To install the package, run:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Running
To run the application, execute:
```bash
PYTHONPATH=src python -m sc_device_hub.main
```


Then open the dashboard at:
```text
http://127.0.0.1:8000
```

The API is available under the versioned prefix:
```text
/api/v1/devices
/api/v1/devices/{device_id}/ping
```

If you want to change the bind address or port, set `HOST` and `PORT` before starting the app.