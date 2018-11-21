These are a few python scripts to help us emulate CAN packets over the [CANMate](http://www.dthoughts.com/products/canmate.html) hardware. The emulator is provided by [Deep Thought](http://www.dthoughts.com/index.html) and they have also provided a `.ddl/.so` file to be used to get an API access into the emulator.

Files:
* **canOpen_emulator.py**:
	This file will send CANFrames using the emulator. The frames will be the ones specified in Putzmeister cement pump document. 
* **loopback.py**:
	This is just to demonstrate the working. It will send the CAN frames + loop them back to be recevied by the emulator itself. To be used for understanding and testing.
* **loop_user.py**s:
	This will send, receive and loopback. Can be configured by the user

## Future Plans

Maybe make this work as an actual [CANOpen](https://www.can-cia.org/canopen/) emulator for CANMate.