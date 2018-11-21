'''
Send CANFrames (PDOs and heartbeat in accordance with CANOpen) over
the CANMate CAN emulator.

@author Clament John
@data 19th November 2018

Python 2.7
'''

import platform
import time
import sys
import ctypes
from ctypes import *
import signal
import threading
import Queue

'''Keyboard interrupt
'''
def signal_handler(sig, frame):
    pdo1_thrd.do_run = False
    pdo2_thrd.do_run = False
    pdo3_thrd.do_run = False
    heart_thrd.do_run = False
    #close the HW before exiting
    libCAN.CloseCANMate(handle)
    print('You pressed Ctrl+C!')
    sys.exit(0)

#Datacallback function
def Datacalbk(a, b):
    #print "Received: "
    if a[0].D7 == 0:
        printf("Heart: %02X%02X [%02X] %02X %02X %02X %02X %02X %02X %02X %02X\n", a[0].SArbId1, a[0].SArbId0, a[0].DLC, 
        a[0].D0, a[0].D1, a[0].D2, a[0].D3, a[0].D4, a[0].D5, a[0].D6, a[0].D7)
    if a[0].D7 in (1,2,3):
        printf("PDO  : %02X%02X [%02X] %02X %02X %02X %02X %02X %02X %02X %02X\n", a[0].SArbId1, a[0].SArbId0, a[0].DLC, 
        a[0].D0, a[0].D1, a[0].D2, a[0].D3, a[0].D4, a[0].D5, a[0].D6, a[0].D7)
    return 0

#Eventcallback function
def Eventcalbk(a):
    printf("Event: %02X %02X %02X\n", a[0].chErr, a[0].chTxErrCnt, a[0].chRxErrCnt)
    return 0


def Help():
    print "Possible Option are :"
    print "loop-read, loop-write, loopback, Ctrl+C\n"



# Define the CAN Message struct
class CANMsg(Structure):
    _pack_ = 1
    _fields_ = [('bExtended', ctypes.c_ubyte),
                ('chTmStmpH', ctypes.c_ubyte),#Upper byte of time stamp field
                ('chTmStmpL', ctypes.c_ubyte),#Lower byte of time stamp field
                #time stamp is ignored for Tx messages
                ('EArbId1', ctypes.c_ubyte),#bits 25-29 if its an extended message
                ('EArbId0', ctypes.c_ubyte),#3rd byte in case of exteneded message
                ('SArbId1', ctypes.c_ubyte),#2nd byte incase of extended and MSB contains bits 9-11 for standard message
                ('SArbId0', ctypes.c_ubyte),#first byte for both extended & standard
                ('DLC', ctypes.c_ubyte),#message length
                ('D0', ctypes.c_ubyte),
                ('D1', ctypes.c_ubyte),
                ('D2', ctypes.c_ubyte),
                ('D3', ctypes.c_ubyte),
                ('D4', ctypes.c_ubyte),
                ('D5', ctypes.c_ubyte),
                ('D6', ctypes.c_ubyte),
                ('D7', ctypes.c_ubyte)]
                
# Define the CAN Event struct
class CANEvent(Structure):
    _fields_ = [('chErr', ctypes.c_ubyte),
                ('chTxErrCnt', ctypes.c_ubyte),
                ('chRxErrCnt', ctypes.c_ubyte)]

def toCanTx(message, delay, queue_in):
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        if message.D7 == 0:
            printf("Heart: %02X%02X [%02X] %02X %02X %02X %02X %02X %02X %02X %02X\n", message.SArbId1, message.SArbId0, message.DLC, 
            message.D0, message.D1, message.D2, message.D3, message.D4, message.D5, message.D6, message.D7)
        if message.D7 in (1,2,3):
            printf("PDO  : %02X%02X [%02X] %02X %02X %02X %02X %02X %02X %02X %02X\n", message.SArbId1, message.SArbId0, message.DLC, 
            message.D0, message.D1, message.D2, message.D3, message.D4, message.D5, message.D6, message.D7)
        queue_in.put(message)
        time.sleep(delay)
    print("stopping {} thread".format(t.name))

class ProcessThread(threading.Thread):
    def __init__(self, in_q):
        threading.Thread.__init__(self)
        self.in_queue = in_q

    def run(self):
        while True:
            msg = self.in_queue.get()
            result = self.process(msg)
            if result == -1:
                libCAN.CloseCANMate(handle)
                print('Tx failed')
                sys.exit(0)

    def process(self, msg):
        ret_check = libCAN.WriteCANMessage(handle, byref(msg))
        return ret_check

if __name__ == "__main__":
    #stop all process if a signal interrupt is called
    signal.signal(signal.SIGINT, signal_handler)

    #include the API for the CAN Emulator by DeepThought
    libCAN = cdll.LoadLibrary("libcanmate.so")
    libc = CDLL("libc.so.6")
    printf = libc.printf

    #Variables
    ret_check = c_int(0)
    handle = c_void_p()
    num = c_int(1)

    #Index no for Baudrate
    chBaudRate = c_int(8) #BAUD_RATE250K	8

    pmsg = CANMsg(0, 0, 0, 0, 0, 0, 8, 8, 9, 10, 12, 99, 51, 34, 73, 45) #  initially memset to {0}
    pdo1 = CANMsg(0, 0, 0, 0, 0, 1, 138, 8, 0, 0, 0, 0, 0, 0, 0, 1)
    pdo2 = CANMsg(0, 0, 0, 0, 0, 2, 138, 8, 0, 0, 0, 0, 0, 0, 0, 2)
    pdo3 = CANMsg(0, 0, 0, 0, 0, 3, 138, 8, 0, 0, 0, 0, 0, 0, 0, 3)
    heartBeat = CANMsg(0, 0, 0, 0, 0, 7, 10, 8, 0, 0, 0, 0, 0, 0, 0, 0)

    atcra = CANMsg(0, 0, 0, 0, 0, 7, 233, 8, 0, 0, 0, 0, 0, 0, 0, 3)
    libCAN.WriteCANMessage.argtypes = [handle, POINTER(CANMsg)]

    #Datacallback and Eventcallback function declaration
    DataCB = CFUNCTYPE(c_int, POINTER(CANMsg), POINTER(c_int))
    EventCB = CFUNCTYPE(c_int, POINTER(CANEvent))
    _data_fn = DataCB(Datacalbk)
    _event_fn = EventCB(Eventcalbk)

    libCAN.OpenCANMate.argtypes = [DataCB, EventCB]

    #GetBaudRate function declaration
    GetBRate = libCAN.GetCurrentBaudRate
    GetBRate.restype = c_int
    GetBRate.argtypes = [handle, POINTER(c_int)]
    Data = c_int()

    #GetFirmware Version
    GetVer = libCAN.GetFirmwareVersion
    GetVer.restype = c_int
    GetVer.argtypes = [handle, POINTER(c_int)]
    Ver = c_int()

    ### start process ###
    
    #open the device
    handle = libCAN.OpenCANMate(_data_fn, _event_fn)
    if handle <= 0:
        print "Failed to open"
        exit(-1)
    #set the baudrate
    ret_check = libCAN.SetCANBaudRate(handle, chBaudRate)
    #set to start reception
    ret_check = libCAN.StartReception(handle)

    writequeue = Queue.Queue()
    
    t = ProcessThread(writequeue)
    t.setDaemon(True)
    t.start()
    #start a thread and send data every one second
    pdo1_thrd = threading.Thread(name="pdo1", target=toCanTx, args=(pdo1, 1, writequeue))
    pdo2_thrd = threading.Thread(name="pdo2", target=toCanTx, args=(pdo2, 1, writequeue))
    pdo3_thrd = threading.Thread(name="pdo3", target=toCanTx, args=(pdo3, 1, writequeue))
    heart_thrd = threading.Thread(name="heartbeat", target=toCanTx, args=(heartBeat, 0.5, writequeue))

    pdo1_thrd.setDaemon = True
    pdo2_thrd.setDaemon = True
    pdo3_thrd.setDaemon = True
    heart_thrd.setDaemon = True

    pdo1_thrd.start()
    pdo2_thrd.start()
    pdo3_thrd.start()
    heart_thrd.start()

    while True:
        time.sleep(1)
