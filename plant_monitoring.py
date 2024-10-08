import sqlite3
import time

import adafruit_dht
import adafruit_hcsr04
import board
import digitalio
import pyfirmata2

translate = lambda a, b, c, d, e: round((a - b) * (e - d) / (c - b) + d, 2)


def take_moisture_sample():
    moisture_samples = []
    arduino.analog[1].register_callback(lambda x: moisture_samples.append(x))
    arduino.analog[1].enable_reporting()
    time.sleep(10)
    arduino.analog[1].disable_reporting()
    arduino.analog[1].unregiser_callback()

    # Invert the result to make it easier to resonate about min and max moisture
    average_moisture = round(1 - sum(moisture_samples) / len(moisture_samples), 2)
    return average_moisture


def take_temperature_and_humidiy_sample():
    measurementsForWrite = 100
    counter = 0
    tempSum = 0
    humiditySum = 0

    while counter <= measurementsForWrite:
        try:
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity

            humiditySum += humidity or 0
            tempSum += temperature_c or 0
            counter += 1
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print("RuntimeError")
            print(error.args[0])
            continue
        except Exception as error:
            print("Fatal error. Exiting DHT device")
            dhtDevice.exit()
            raise error

    avgTemp = round(tempSum / counter, 2)
    avgHum = round(humiditySum / counter)
    return (avgTemp, avgHum)


def take_tank_level_sample():
    counter = 0
    distance_samples = []
    attempts = 0
    while counter < 300:
        try:
            distance_samples.append(sonar.distance)
            counter = counter + 1
            time.sleep(0.1)

        except:
            print("Reading distance failed. Retrying...")

        finally:
            attempts += 1

        if attempts > 350:
            raise Exception("Too many retries. Exiting loop.")

    return round(sum(distance_samples) / len(distance_samples), 2)


def take_samples():
    print("Taking measurements.")
    try:
        moisture = take_moisture_sample()
        tank_distance = take_tank_level_sample()
        temp_and_humidity_results = take_temperature_and_humidiy_sample()
    except Exception as error:
        print("Reading measurements failed. Exiting.")
        raise error

    print(
        "Soil moisture:",
        moisture,
        "Temperature:",
        temp_and_humidity_results[0],
        "Humidity:",
        temp_and_humidity_results[1],
        "Distance",
        tank_distance,
    )

    print("Committing to DB")
    db.execute(
        "INSERT INTO measurements (temperature, humidity, moisture, tank_level) VALUES (?, ?, ?, ?)",
        [
            temp_and_humidity_results[0],
            temp_and_humidity_results[1],
            moisture,
            tank_distance,
        ],
    )
    con.commit()
    return {
        "moisture": moisture,
        "temperature": temp_and_humidity_results[0],
        "humidity": temp_and_humidity_results[1],
        "tank_distance": tank_distance,
    }


def run_pump(time_to_run: int):
    print(f"Running pump for {time_to_run} seconds")
    pump.value = True
    time.sleep(time_to_run)
    pump.value = False
    print("Turned off pump.")


def water_plant(results: dict[str, float]):
    db.execute("SELECT * FROM plant WHERE id = 1;")
    plant = dict(db.fetchone())

    # High moisture value means wet plant
    if results["moisture"] > plant["max_moisture"]:
        plant["is_drying"] = 1
    # Low moisture value means wet plant
    elif results["moisture"] < plant["min_moisture"]:
        plant["is_drying"] = 0

    db.execute(
        "UPDATE plant SET is_drying = ? WHERE ID = 1;",
        [plant["is_drying"]],
    )
    con.commit()

    if plant["is_drying"]:
        print("Plant is drying. Not watering")
        return

    if results["tank_distance"] > plant["tank_max_distance"]:
        print("Reservoir water level too low! Not watering!")
        return

    try:
        db.execute(
            "INSERT INTO watering_log (moisture, plant_id) VALUES (?, ?);",
            [results["moisture"], plant["id"]],
        )
        run_pump(3)
    except Exception as pump_error:
        pump.value = False
        print(
            "Exception was thrown while running the pump.",
            pump_error.args[0],
        )
        raise pump_error

    con.commit()


arduino = pyfirmata2.Arduino("/dev/ttyACM0")
arduino.samplingOn(20)

dhtDevice = adafruit_dht.DHT11(board.D18)

sonar = adafruit_hcsr04.HCSR04(board.D5, board.D6)

pump = digitalio.DigitalInOut(board.D26)
pump.direction = digitalio.Direction.OUTPUT

con = sqlite3.connect("plant.db")
con.row_factory = sqlite3.Row
db = con.cursor()

minute = 60
hour = minute * 60
sequence_sleep_time = 60 * minute

while True:
    results = take_samples()
    water_plant(results)
    time.sleep(sequence_sleep_time)
