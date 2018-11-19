'''
Loop a certain CAN frame

@author Clament John
@data 09th November 2018
'''

import platform
import time
import sys
import ctypes
from ctypes import *
import signal
import threading
import Queue

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

def putCanTx(message, delay, queue_in):
    while True:
        queue_in.put(message)
        time.sleep(delay)

def signal_handler(sig, frame):
    #close the HW before exiting
    libCAN.CloseCANMate(handle)
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

libCAN = cdll.LoadLibrary("libcanmate.so")
libc = CDLL("libc.so.6")
printf = libc.printf

# Define the CAN Message struct
class CANMsg(Structure):
    _pack_ = 1
    _fields_ = [('bExtended', ctypes.c_ubyte),
                ('chTmStmpH', ctypes.c_ubyte),
                ('chTmStmpL', ctypes.c_ubyte),
                ('EArbId1', ctypes.c_ubyte),
                ('EArbId0', ctypes.c_ubyte),
                ('SArbId1', ctypes.c_ubyte),
                ('SArbId0', ctypes.c_ubyte),
                ('DLC', ctypes.c_ubyte),
                ('D0', ctypes.c_ubyte),
                ('D1', ctypes.c_ubyte),
                ('D2', ctypes.c_ubyte),
                ('D3', ctypes.c_ubyte),
                ('D4', ctypes.c_ubyte),
                ('D5', ctypes.c_ubyte),
                ('D6', ctypes.c_ubyte),
                ('D7', ctypes.c_ubyte)]

def from_param(self):
    return ctypes.c_void_p(self.c_ptr)


# Define the CAN Event struct
class CANEvent(Structure):
    _fields_ = [('chErr', ctypes.c_ubyte),
                ('chTxErrCnt', ctypes.c_ubyte),
                ('chRxErrCnt', ctypes.c_ubyte)]

#Datacallback function
def Datacalbk(a, b):
    #print "Received: "
    printf("Recv Value: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X\n",
           a[0].bExtended, a[0].chTmStmpH, a[0].chTmStmpL, a[0].EArbId1, a[0].EArbId0, a[0].SArbId1, a[0].SArbId0,
           a[0].DLC, a[0].D0, a[0].D1, a[0].D2, a[0].D3, a[0].D4, a[0].D5, a[0].D6, a[0].D7)
    return 0

#Eventcallback function
def Eventcalbk(a):
    print "Event Occured\n"
    print a[0].chErr, a[0].chTxErrCnt, a[0].chRxErrCnt
    return 0


def Help():
    print "Possible Option are :"
    print "loop-read, loop-write, loopback, canopen, Ctrl+C\n"



#Variables
ret_check = c_int(0)
handle = c_void_p()
num = c_int(1)

#Index no for Baudrate
"""
 BAUD_RATE33K	1
 BAUD_RATE50K	2
 BAUD_RATE80K	3
 BAUD_RATE83K	4
 BAUD_RATE100K	5
 BAUD_RATE125K	6
 BAUD_RATE200K	7
 BAUD_RATE250K	8
 BAUD_RATE500K	9
 BAUD_RATE625K	10
 BAUD_RATE800K	11
 BAUD_RATE1000K	12
"""
chBaudRate = c_int(8) #BAUD_RATE250K	8

pmsg = CANMsg(0, 0, 0, 0, 0, 0, 8, 8, 9, 10, 12, 99, 51, 34, 73, 45) #  initially memset to {0}
pdo1 = CANMsg(0, 0, 0, 0, 0, 1, 138, 8, 0, 0, 0, 0, 0, 0, 1, 1)
heartBeat = CANMsg(0, 0, 0, 0, 0, 7, 10, 8, 0, 0, 0, 0, 0, 0, 2, 2)
#specify the required arg types
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

Help()
while True:
    input = raw_input("Enter the command : ")
    if input == "loop-read":
        handle = libCAN.OpenCANMate(_data_fn, _event_fn)
        #print handle
        if (handle > 0):
            print "Open Sucess"
        else:
            print "Error Opening"
        
        #set the baud rate
        ret_check = libCAN.SetCANBaudRate(handle, chBaudRate)
        if (ret_check == 0):
            print "CAN Baudrate of 500K Configured"
        else:
            print "CAN Baudrate Config failed"

        #set to receive
        ret_check = libCAN.StartReception(handle)
        if (ret_check == 0):
            print "Reception Started"
        else:
            print "Reception failed"
    if input == "loop-write":
        handle = libCAN.OpenCANMate(_data_fn, _event_fn)
        #print handle
        if (handle > 0):
            print "Open Sucess"
        else:
            print "Error Opening"
        
        #set the baud rate
        ret_check = libCAN.SetCANBaudRate(handle, chBaudRate)
        if (ret_check == 0):
            print "CAN Baudrate of 250K Configured"
        else:
            print "CAN Baudrate Config failed"

        #write in a loop
        while True:
            printf("Send Value: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X\n",
                pmsg.bExtended, pmsg.chTmStmpH, pmsg.chTmStmpL, pmsg.EArbId1, pmsg.EArbId0, pmsg.SArbId1, pmsg.SArbId0,
                pmsg.DLC, pmsg.D0, pmsg.D1, pmsg.D2, pmsg.D3, pmsg.D4, pmsg.D5, pmsg.D6, pmsg.D7)
            ret_check = libCAN.WriteCANMessage(handle, byref(pmsg))
            time.sleep(0.5)
            if ret_check == -1:
                break
    if input == "loopback":
        handle = libCAN.OpenCANMate(_data_fn, _event_fn)
        #print handle
        if (handle > 0):
            print "Open Sucess"
        else:
            print "Error Opening"
            break
        
        #set the baud rate
        ret_check = libCAN.SetCANBaudRate(handle, chBaudRate)
        if (ret_check == 0):
            print "CAN Baudrate of 500K Configured"
        else:
            print "CAN Baudrate Config failed"
            break

        #set reception
        ret_check = libCAN.StartReception(handle)
        if ret_check == 0:
            print("reception started\n")
        else:
            print("reception failed\n")
            break

        #enable loopback
        ret_check = libCAN.SetLoopbackMode(handle)
        if ret_check == 0:
            print "Loop Back Mode Configured"
        else:
            print "Loop Back Mode failed"
            break

        #write in a loop
        while True:
            printf("Send Value: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X\n",
                pmsg.bExtended, pmsg.chTmStmpH, pmsg.chTmStmpL, pmsg.EArbId1, pmsg.EArbId0, pmsg.SArbId1, pmsg.SArbId0,
                pmsg.DLC, pmsg.D0, pmsg.D1, pmsg.D2, pmsg.D3, pmsg.D4, pmsg.D5, pmsg.D6, pmsg.D7)
            ret_check = libCAN.WriteCANMessage(handle, byref(pmsg))
            time.sleep(0.5)
            if ret_check == -1:
                break
    if input == "canopen":
        handle = libCAN.OpenCANMate(_data_fn, _event_fn)
        #print handle
        if (handle > 0):
            print "Open Sucess"
        else:
            print "Error Opening"
            break
        
        #set the baud rate
        ret_check = libCAN.SetCANBaudRate(handle, chBaudRate)
        if (ret_check == 0):
            print "CAN Baudrate of 500K Configured"
        else:
            print "CAN Baudrate Config failed"
            break

        #set reception
        ret_check = libCAN.StartReception(handle)
        if ret_check == 0:
            print("reception started\n")
        else:
            print("reception failed\n")
            break

        #enable loopback
        ret_check = libCAN.SetLoopbackMode(handle)
        if ret_check == 0:
            print "Loop Back Mode Configured"
        else:
            print "Loop Back Mode failed"
            break

        #write in a loop
        print("Threaded runs")

        g_in_queue = Queue.Queue()
        t = ProcessThread(g_in_queue)
        t.setDaemon(True)
        t.start()
        threading.Thread(target=putCanTx, args=(pmsg, 10, g_in_queue)).start()
        threading.Thread(target=putCanTx, args=(pdo1, 1, g_in_queue)).start()
        threading.Thread(target=putCanTx, args=(heartBeat, 0.1, g_in_queue)).start()