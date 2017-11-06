-------------------------
Command Line Instructions
-------------------------
Example: ./sender <protocal>, <timeout>, <output_filename>
	 ./channel <max_delay>, <discard_probability>, <random_seed>, <verbose>
	 ./receiver <protocal>, <input_filename>
	 <protocal selector> 0 for Go-Back-N and 1 for Selective Repeat

Note: Always running the receiver program first, then run the channel program, and last run sender.
	 The receiver program will print its ip address and port number to a file called recvInfo,
	 and channel then can read receiver's ip address and port number from that file.
	 The channel will print its ip address and port number to a file called channelInfo for
	 sender to retrieve.
	 <protocal> for sender and receiver must be equal and be either 0 or 1.
	 <timeout> for sender must be an positive integer.
	 <input_filename> for receiver must be readable.
	 <output_filename> for sender must be writable.

	The program will print in following format:
		PKT {SEND|RECV} {DAT|ACK|EOT} <total length> <sequence number>
	Also, the program will print Timeout: <timeout>ms whenever there is a timeout triggered.

-------------------
Compiler version
-------------------
The program can be compiled by Python 2.7.12


-------------------
Running Environment 
-------------------
The program has been run and tested on student environment @ubuntu1604-006% with linux binary channel.

