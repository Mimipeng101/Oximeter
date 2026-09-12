import time
from berry_oximeter import BerryOximeter
from smtplib import SMTP
import os
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["APP_PASSWORD"]

# Initialize both variables
avg_o2_reading = None
avg_pulse = None

# --- SECTION 1: THE SIMPLE QUICK CHECK ---
print("--- Starting Quick Check ---")
with BerryOximeter() as oximeter:
    oximeter.connect()
    oximeter.log_to_console(True)
    time.sleep(10)  # Wait 10 seconds
    print("Quick check done.\n")

    # --- SECTION 2: ACTUAL DATA COLLECTION/THE MATH SUMMARY ---
    print("--- Starting 30-Second Data Collection ---")
    start_time = time.time()

    valid_readings = []
    last_alert_second = -5

    while time.time() - start_time < 30:  # Collect 30 seconds of data into a bucket
        elapsed_time = time.time() - start_time
        elapsed_seconds = int(elapsed_time)

        current_reading = oximeter.get_current_reading()
        if current_reading.is_valid:
            valid_readings.append(current_reading)

            if elapsed_seconds % 5 == 0 and elapsed_seconds != last_alert_second:
                last_alert_second = elapsed_seconds

                # 1. Check for dangerous oxygen levels
                if current_reading.spo2 < 90:
                    print(f"Danger! {current_reading.spo2:.1f}% - Low Blood Oxygen!")

                # 2. Check for dangerous pulse rates (Tachycardia / Bradycardia)
                if current_reading.pulse_rate > 100:
                    print(f"High Heart Rate! {current_reading.pulse_rate:.1f} bpm")
                elif current_reading.pulse_rate < 60:
                    print(f"Low Heart Rate! {current_reading.pulse_rate:.1f} bpm")
        time.sleep(1)

    # Calculate the averages
    if valid_readings:

        with open('health_log.csv', 'w') as file:
            file.write("Oxygen(%),Pulse(bpm)\n")
            for reading in valid_readings:
                file.write(f"{reading.spo2},{reading.pulse_rate}\n")

        avg_o2_reading = sum(r.spo2 for r in valid_readings) / len(valid_readings)
        print(f"Your Average Oxygen: {avg_o2_reading:.1f}%")
        avg_pulse = sum(r.pulse_rate for r in valid_readings) / len(valid_readings)
        print(f"Your Average Pulse: {avg_pulse:.1f} bpm")

    else:
        print("No valid data collected.")

    print("Collection done.")

# --- SECTION 3: SENDING DATA VIA EMAIL --- #
if avg_o2_reading is not None:
    print("--- Sending Email Report ---")

    with open('health_log.csv', 'r') as file:
        file_contents = file.read()

    email_message = (f"Subject: Health Report\n\n"
                     f"Your average blood oxygen reading over 30 seconds was: {avg_o2_reading:.1f}%\n"
                     f"Your average heart/pulse rate reading over 30 seconds was: {avg_pulse:.1f} bpm\n\n"
                     f"ALL COLLECTED DATA:\n"
                     f"{file_contents}")

    try:
        with SMTP("smtp.gmail.com", 587) as connection:  # Fixed host and added standard TLS port
            connection.starttls()
            connection.login(
                user=EMAIL,
                password=PASSWORD,
            )
            connection.sendmail(
                from_addr=EMAIL,
                to_addrs=EMAIL,
                msg=email_message,
            )
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
else:
    print("Skipping email: No valid oximeter data was collected.")