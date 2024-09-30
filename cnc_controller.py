import serial
import os
import time
from threading import Event
import math

BAUD_RATE = 115200
SERIAL_PORT = "COM11" #Serial Port
X_LOW_BOUND = 0
X_HIGH_BOUND = 270
Y_LOW_BOUND = 0
Y_HIGH_BOUND = 150
Z_LOW_BOUND = -40 #Not actually sure
Z_HIGH_BOUND = 0

#Home the CNC machine
def home():
    print("Homing")

#Wait for the CNC machine to complete its motion
def wait_for_movement_completion(ser, cleaned_line):
    Event().wait(1)
    if cleaned_line != '$X' or '$$':
        idle_count = 0
        while True:
            ser.reset_input_buffer()
            command = str.encode('?' + '\n')
            ser.write(command)
            grbl_out = ser.readline()
            grbl_response = grbl_out.strip().decode('utf-8')

            if grbl_response != 'ok':
                if grbl_response.find('Idle') > 0:
                    idle_counter += 1
            if idle_count > 0:
                break
    return

#Command the CNC machine to move to a point (x,y,z)
def move_to_point(x,y,z,speed):
    if coordinates_within_bounds(x,y,z):
        gcode =  f"G1 X{x} Y{y} Z{z} F{speed}" + " \n"
        print(f"Moved To (X{x}, Y{y}, Z{z}): ", follow_gcode_path(gcode))
    else:
        print(f"Cannot move to (X{x}, Y{y}, Z{z}), coordinates not within bounds")

#Returns the gcode to move to a point (x,y,z)
#You can create a long gcode list to execute all at once instead of doing it line-by-line
def get_gcode_for_point(x,y,z,speed):
    return f"G1 X{x} Y{y} Z{z} F{speed}" + " \n"

#Check if you are within the stage
def coordinates_within_bounds(x,y,z):
    within_bounds = False
    if X_LOW_BOUND <= x <= X_HIGH_BOUND and Y_LOW_BOUND <= y <= Y_HIGH_BOUND and Z_LOW_BOUND <= z <= Z_HIGH_BOUND:
        within_bounds = True
    return within_bounds

#Wake up the CNC machine
def wake_up(ser):
    ser.write(str.encode("\r\n\r\n"))
    time.sleep(1)  # Wait for cnc to initialize
    ser.flushInput()  # Flush startup text in serial input
    print("CNC awake")

#Follows a gcode path, will execute as many commands at a time as the buffer is set to
#If the buffer is too high, the machine may not complete all the commands
def follow_gcode_path(gcode, buffer=20):
    with serial.Serial(SERIAL_PORT, BAUD_RATE) as ser:
        wake_up(ser)
        out_strings = []
        commands = gcode.split('\n')
        for i in range (0, math.ceil(len(commands)/buffer)):
            try:
                buffered_commands = commands[i*buffer:(i+1)*buffer]
            except:
                buffered_commands = commands[i*buffer:]
            buffered_gcode = ""
            for j in range (0, len(buffered_commands)):
                buffered_gcode += buffered_commands[j] 
                buffered_gcode += "\n"

            command = str.encode(buffered_gcode)
            ser.write(command)
            wait_for_movement_completion(ser, buffered_gcode)
            grbl_out = ser.readline()  # Wait for response
            out_string =grbl_out.strip().decode('utf-8')
            out_strings.append(out_string)
            print("Commands rendered:", len(buffered_commands)+i*buffer)
        return out_strings