import serial
import time
import struct
import sys

# --- 1. Configuration Parameters ---
# The /dev/serial0 link typically points to the active GPIO UART port on Raspberry Pi.
SERIAL_PORT = '/dev/serial0'  
BAUD_RATE = 9600
DATA_FRAME_LENGTH = 9

# Fixed address bytes according to the datasheet (B1 and B2)
MODULE_ADDR_H = 0x2C
MODULE_ADDR_L = 0xE4

def calculate_checksum(data):
    """
    Calculates the checksum (B9) based on the datasheet:
    Sum of bytes B1 to B8, then take the lower 8 bits (modulo 256).
    'data' should be the full 9-byte raw frame.
    """
    # Check if we have at least B1 to B8 for summation
    if len(data) < 8:
        return -1
        
    # Sum of bytes B1 through B8 (indices 0 through 7)
    total_sum = sum(data[0:8])
    
    # Take the lower 8 bits (equivalent to % 256)
    checksum = total_sum & 0xFF
    return checksum

def parse_sensor_data(raw_data):
    """
    Parses the 9-byte data frame and calculates TVOC, CH2O, and CO2 concentrations.
    """
    # Check if the received data length is correct
    if len(raw_data) != DATA_FRAME_LENGTH:
        print(f"Data length error: Received {len(raw_data)} bytes, expected {DATA_FRAME_LENGTH}.")
        return None

    # 1. Verify Module Address (B1 and B2)
    if raw_data[0] != MODULE_ADDR_H or raw_data[1] != MODULE_ADDR_L:
        print(f"Module address mismatch: Received {hex(raw_data[0])}{hex(raw_data[1])}, expected {hex(MODULE_ADDR_H)}{hex(MODULE_ADDR_L)}")
        return None

    # 2. Verify Checksum (B9)
    received_checksum = raw_data[8]
    calculated_checksum = calculate_checksum(raw_data)
    
    if received_checksum != calculated_checksum:
        print(f"Checksum error: Received {hex(received_checksum)}, Calculated {hex(calculated_checksum)}")
        return None
        
    # Concentration formula (mg/m3) = (High * 256 + Low) * 0.001

    # 3. TVOC Concentration (B3, B4)
    tvoc_raw = (raw_data[2] * 256) + raw_data[3]
    tvoc_concentration = tvoc_raw * 0.001
    
    # 4. CH2O Concentration (B5, B6)
    ch2o_raw = (raw_data[4] * 256) + raw_data[5]
    ch2o_concentration = ch2o_raw * 0.001
    
    # 5. CO2 Concentration (B7, B8)
    co2_raw = (raw_data[6] * 256) + raw_data[7]
    co2_concentration = co2_raw * 0.001

    return {
        "TVOC": tvoc_concentration,
        "CH2O": ch2o_concentration,
        "CO2": co2_concentration,
        "Raw_Frame": bytes(raw_data).hex() # Convert list back to bytes for hex display
    }


def main():
    """
    Main program: Initializes the serial port and loops for reading data.
    """
    ser = None
    try:
        # Initialize serial port connection
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1  # Set read timeout
        )
        print(f"Successfully connected to UART port: {SERIAL_PORT} @ {BAUD_RATE} bps")
        
        # Clear input buffer to avoid reading old data
        ser.flushInput()

        while True:
            # Read a complete data frame (9 bytes)
            # The sensor actively sends data, so we just read.
            raw_data = ser.read(DATA_FRAME_LENGTH)
            
            if raw_data:
                # Convert bytes object to int list for easy processing
                data_list = list(raw_data)
                
                result = parse_sensor_data(data_list)
                
                if result:
                    print("-" * 30)
                    print(f"Frame (Hex): {result['Raw_Frame']}")
                    print(f"TVOC Concentration: {result['TVOC']:.3f} mg/m³")
                    print(f"CH2O Concentration: {result['CH2O']:.3f} mg/m³")
                    print(f"CO2 Concentration: {result['CO2']:.3f} mg/m³")
                
            else:
                # This will print if the 1-second timeout is hit without receiving data
                # If you continuously see this, check wiring or sensor power.
                print("Waiting for data...")

            time.sleep(1) # Wait 1 second before the next read attempt

    except serial.SerialException as e:
        print(f"Fatal Serial Error: {e}")
        print("Please check the port name, baud rate, and user permissions for /dev/serial0.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()