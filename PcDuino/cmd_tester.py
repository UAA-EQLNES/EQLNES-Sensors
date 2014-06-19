#! /usr/bin/env python
import argparse
from gpio import enableUart
from serial import Serial
from sim900 import Sim900
from time import sleep

def main():
    parser = argparse.ArgumentParser(description='Run Sim900 AT Command Tester.')
    parser.add_argument('-p', '--port', help='Serial port', default='/dev/ttyS1')
    parser.add_argument('-b', '--baudrate', type=int, help='Baudrate of Sim900 GSM shield', default=115200)
    args = parser.parse_args()
    
    port = args.port
    baudrate = args.baudrate

    # Need to initalize gpio0 and gpio1 to UART mode if pcDuino.
    # If not pcDuino, just ignore the error.
    try:
        enableUart()
    except:
        pass

    sim900 = Sim900(Serial(port, baudrate, timeout = 10), delay=0.3)

    # For non-pcDuino devices, there looks to be a delay before commands
    # are sent and read correctly. Waiting two seconds seems to work.
    print "Initializing serial connection..."
    sleep(2)

    print ""
    print "Sim900 AT Command Tester"
    print "------------------------"
    print ""
    print "Type 'exit' to end the program."
    print ""

    while True:
        cmd = raw_input("Enter AT command: ")

        if cmd == 'exit':
            break
        
        sim900.send_cmd(cmd)
        print sim900.read_all()


if __name__ == '__main__':
    main()
