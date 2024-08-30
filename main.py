import sqlite3
import time

import adafruit_dht
import adafruit_hcsr04
import board
import digitalio
import pyfirmata2

arduino = pyfirmata2.Arduino("/dev/ttyACM0")


def take_moisture_sample():
    moisture_samples = []
    arduino.analog[1].register_callback(lambda x: moisture_samples.append(x))
    arduino.analog[1].enable_reporting()
    time.sleep(10)
    arduino.analog[1].disable_reporting()
    arduino.analog[1].unregiser_callback()

    average_moisture = round(sum(moisture_samples) / len(moisture_samples), 2)
    return average_moisture


def take_temperature_and_humidiy_sample():
    measurementsForWrite = 100
    counter = 0
    tempSum = 0
    humiditySum = 0

    while counter <= measurementsForWrite:
        try:
            # TODO: If one fails and not the other, that's a problem
            # TODO: Shitty results on first reading, "Checksum did not validate returned in error"
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity

            humiditySum += humidity or 0
            tempSum += temperature_c or 0
            counter += 1
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error

    avgTemp = round(tempSum / counter, 2)
    avgHum = round(humiditySum / counter)
    return (avgTemp, avgHum)


def take_tank_level_sample():
    counter = 0
    distance_samples = []
    while counter < 6:
        try:
            distance_samples.append(sonar.distance)
            counter = counter + 1
            time.sleep(2)

        except:
            print("Reading distance failed. Retrying...")

    return round(sum(distance_samples) / 5, 2)


def take_samples():
    print("Taking measurements.")
    moisture = take_moisture_sample()
    temp_and_humidity_results = take_temperature_and_humidiy_sample()
    tank_distance = take_tank_level_sample()

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


def run_pump(time_to_run):
    # TODO Implement pump logic
    print(f"Running pump for {time_to_run} seconds")
    pump.value = True
    time.sleep(time_to_run)
    pump.value = False
    print("Turned off pump.")


def water_plant(results):
    db.execute("SELECT * FROM plant WHERE id = 1;")
    plant = dict(db.fetchone())

    # Low moisture value means wet plant
    if results["moisture"] < plant["min_moisture"]:
        plant["is_drying"] = 1
    # High moisture value means dry plant
    elif results["moisture"] > plant["max_moisture"]:
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
        print("Tank level too low! Not watering!")
        """
        TODO: Maybe light up a LED on the board when this happens
        to physically signal that water needs to be refilled
        """
        return

    try:
        db.execute(
            "INSERT INTO watering_log (moisture, plant_id) VALUES (?, ?);",
            [results["moisture"], plant["id"]],
        )
        #TODO: Figure out if there's a way to reset this if the process dies for whatever reason..
        run_pump(3)
        con.commit()
    except:
        print("Well shit..")
        # TODO: Should probably attempt to disconnect everything gracefully at this point..


def main():
    while True:
        results = take_samples()
        water_plant(results)

        time.sleep(1 * hour)


dhtDevice = adafruit_dht.DHT11(board.D18)

pump = digitalio.DigitalInOut(board.D26)
pump.direction = digitalio.Direction.OUTPUT

sonar = adafruit_hcsr04.HCSR04(board.D5, board.D6)
# Sample every 20th millisecond
arduino.samplingOn(20)

con = sqlite3.connect("plant.db")
con.row_factory = sqlite3.Row
db = con.cursor()

minute = 60
hour = minute * 60

main()
