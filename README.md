**Disclaimer: This file was written with assistance from AI-based software other than CS50's own. (Chat GPT)**

<br/>

# Automated Plant Monitoring and Watering System

### Video demo: https://youtu.be/b4iUzopBMHg

## Description

This project is a comprehensive, automated solution for monitoring and maintaining optimal conditions for plant growth. It integrates various sensors, hardware controls, and a web-based interface to track environmental factors like soil moisture, temperature, humidity, and water tank levels. The system is designed to automate the watering process, ensuring that plants receive the right amount of water based on real-time data.

## Equipment

The equipment used in this project:
- Raspberry Pi 3B+
- 5V submersible water pump
- HC-SR04 Ultrasonic distance sensor
- DHT11 Temperature and relative humidity sensor
- A basic breadboard, dupont jumper wires and LED diodes
- Arduino Uno
- 3.3-5V capacitive soil moisture sensor 
- LEDlife Max-Grow 30W grow light 

<br/>

## plant_monitoring.py

This script is an automated plant monitoring and watering system that integrates various sensors and hardware controls to maintain optimal plant conditions.

External libraries:
- [Adafruit Blinka](https://github.com/adafruit/Adafruit_Blinka)
- [Adafruit CircuitPython DHT](https://github.com/adafruit/Adafruit_CircuitPython_DHT)
- [Adafruit CircuitPython HCSR04](https://github.com/adafruit/Adafruit_CircuitPython_HCSR04)
- [pyfirmata2](https://github.com/berndporr/pyFirmata2)

### Soil Moisture Measurement

As the Raspberry Pi lacks built-in analog-to-digital conversion, an Arduino is acting as an intermediary between the moisture sensor and the Raspberry Pi. It is used to convert the analog signals from the soil moisture sensor into digital data that can be processed by the Raspberry Pi. 

The `take_moisture_sample()` function collects analog readings from the moisture sensor. The readings are averaged, inverted, and normalized to provide a moisture value where a high number indicates high moisture.

### Temperature and Humidity Measurement

 The `take_temperature_and_humidiy_sample()` function reads temperature and humidity data using an Adafruit DHT11 sensor. Multiple readings are taken to ensure accuracy, and errors are handled to avoid interruptions.

### Tank Level Measurement

The `take_tank_level_sample()` function uses an ultrasonic sensor (HC-SR04) to measure the distance to the water surface in the tank, giving an indication of the water level.

### Data Logging

The `take_samples()` function aggregates the moisture, temperature, humidity, and tank level data. It then stores these measurements in a SQLite database, recording the environmental conditions for historical analysis.

### Automated Watering

The `water_plant()` function determines whether the plant requires watering based on the moisture level compared to predefined thresholds stored in the database. If the soil is too dry and the water tank has sufficient water, the script activates a water pump via a GPIO pin on the Raspberry Pi to water the plant. The action is logged in the database for tracking purposes.

### Continuous Operation

The script runs in an infinite loop, executing the `take_samples()` and `water_plant()` functions every 15 minutes. It continuously monitors and maintains plant conditions

Certainly! Below is the markdown to include in your `README.md` for the files `api.py`, `view.html`, and `header.html`, following the structure you've used for `plant_monitoring.py`.

<br/>

## api.py

This file serves as the backend API, enabling the interaction between the plant monitoring data and the web interface. It is built using [FastAPI](https://fastapi.tiangolo.com/) and integrates with the SQLite database to provide real-time data to the front-end.

### External Libraries

- [FastAPI](https://fastapi.tiangolo.com/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [SQLite3](https://docs.python.org/3/library/sqlite3.html)

### Main Features

#### Web Interface Endpoint (`/`)

- **Purpose**: Serves the main dashboard that displays plant monitoring data.
- **Functionality**: Retrieves sensor data from the SQLite database and renders it using the `view.html` template. Also calculates moisture level boundaries and translates tank level measurements into percentages.

#### Header Data Endpoint (`/header`)

- **Purpose**: Provides the latest temperature, humidity, and tank level readings.
- **Functionality**: Fetches the most recent sensor data and updates the dashboard header dynamically using the `header.html` template.

#### Chart Data Endpoint (`/chart-data`)

- **Purpose**: Supplies real-time moisture data for the dashboard's chart.
- **Functionality**: Returns JSON-encoded sensor readings that are used to update the moisture level chart on the front-end.

#### Static Files

- **Purpose**: Serves static assets (CSS, images) required for the front-end.
- **Functionality**: Uses FastAPI’s `StaticFiles` to deliver assets from the `assets` directory.

#### Data Translation

- **Utility**: Includes functions like `translate()` to convert raw sensor data into meaningful values, such as converting ultrasonic sensor measurements into tank water level percentages.

</br>

## view.html

This is the main template for the web-based plant monitoring dashboard. It provides a user-friendly interface to visualize real-time and historical data about the plant's environment.

### External Libraries

- [HTMX](https://htmx.org/)
- [Chart.js](https://www.chartjs.org/)
- [Luxon](https://moment.github.io/luxon/)
- [Simple.css](https://simplecss.org/)

### Main Features

#### Responsive Design

- **Purpose**: Ensures the dashboard is accessible and visually appealing across different devices.
- **Functionality**: Uses Simple.css for a minimalist design and includes media queries for mobile responsiveness.

#### Real-Time Updates

- **Purpose**: Keeps the dashboard data up-to-date without full-page reloads.
- **Functionality**: Utilizes HTMX to automatically refresh the header and chart data at regular intervals.

#### Moisture Level Chart

- **Purpose**: Visualizes moisture data over time to help users track the plant's hydration levels.
- **Functionality**: Implements a time-series line chart using Chart.js and Luxon, which dynamically updates with new data fetched from the `/chart-data` endpoint.

#### Visual Indicators

- **Purpose**: Displays the latest temperature, humidity, and tank level in a user-friendly format.
- **Functionality**: Uses material design icons and CSS animations to highlight key environmental metrics.

</br>

## header.html

This template is a component of the main dashboard, focusing on displaying the latest environmental readings in a concise, visually appealing format.

### Main Features

#### Temperature, Humidity, and Water Level Display

- **Purpose**: Presents real-time data for key environmental factors.
- **Functionality**: Fetches the latest readings from the backend and renders them with appropriate icons and styling.

#### Water Tank Level Animation

- **Purpose**: Visually represents the current water level in the tank.
- **Functionality**: Utilizes CSS animations to adjust the tank level indicator in real-time based on the latest sensor data.

#### Dynamic Updates

- **Purpose**: Ensures the header data stays current without requiring manual page refreshes.
- **Functionality**: Integrated with HTMX to refresh the displayed data every 60 seconds, pulling from the `/header` endpoint.
