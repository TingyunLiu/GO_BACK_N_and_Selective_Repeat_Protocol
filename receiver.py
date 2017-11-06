from sys import argv # import argv for command line argument
from socket import * # import socket library
from packet import * # import my own packet.py file


#*********************************************************************************************************************
# Usage function to handle command line argument
#*********************************************************************************************************************
def usage():
  	print "Usage: ./receiver <protocal selector> <filename>" # print the usage of the function for receiver
  	print "<protocol selector> 0 for Go-Back-N and 1 for Selective Repeat" # print protocal selector information
  	exit()


#*********************************************************************************************************************
# Function to write hostname and port number into a file for channel to connect
#*********************************************************************************************************************
def write_ip_and_port(infofile):
	recvInfo = open(infofile, 'w') # open recvInfo (recvInfo is for channel to read)
	recvInfo.write(gethostname()) # write hostname
	recvInfo.write(" ") # write space
	recvInfo.write(str(receiver_socket.getsockname()[1])) # write port number
	recvInfo.close() # close the file recvInfo


# check command line argument, protocal must be in [0,1]
if (len(argv) != 3) or (int(argv[1]) != 0 and int(argv[1]) != 1):
	usage()

protocal = int(argv[1]) # extract protocal for later use

receiver_socket = socket(AF_INET, SOCK_DGRAM) # create UDP socket
receiver_socket.bind(("",0)) # bind with a random available port number

write_ip_and_port('recvInfo') # write ip address and port number into recvInfo

outfile = open(argv[2], 'w') # open output file

base = 0 # window base, for selective repeat use only
rcv_buf = [None] * WINDOW_SIZE # a buffer to keep track of packets within window size, for selective repeat use only
expected_seq_num = 0 # expected next sequence number, for GO_BACK_N use only 
ack_pkt = make_a_packet(ACK_PACKET_TYPE, HEADER_SIZE, MAX_SEQ_NUM-1, "") # make first void packet

while True:

	(pkt, channel_address) = receiver_socket.recvfrom(1024) # received a packet
	(pkt_type, length, seq_num, data) = unpack_a_packet(pkt) # unpack the packet
	print "PKT RECV DAT {0} {1}".format(length, seq_num)

	if pkt_type == DATA_PACKET_TYPE: # if packet is a data type packet
		if protocal == GO_BACK_N: # for protocal is GO_BACK_N
			if seq_num == expected_seq_num: # only send new ack packet with new seq_num when seq_num is as expected
				ack_pkt = make_a_packet(ACK_PACKET_TYPE, HEADER_SIZE, expected_seq_num, "") # make a new ack packet
				receiver_socket.sendto(ack_pkt, channel_address) # send ack packet
				print "PKT SEND ACK {0} {1}".format(HEADER_SIZE, seq_num)
				outfile.write(data) # write the data into output file
				expected_seq_num = (expected_seq_num + 1) % MAX_SEQ_NUM # increment expected_seq_num by 1
			else: # not expected packet (out of order packet)
				receiver_socket.sendto(ack_pkt, channel_address) # send previous ack packet
				print "PKT SEND ACK {0} {1}".format(HEADER_SIZE, get_packet_seq_num(ack_pkt))
		else: # protocal is selective repeat
			# Packet with sequence number in [rcv_base, rcv_base+N-1] is correctly received
			if check_seq_in_window(seq_num, base):
				ack_pkt = make_a_packet(ACK_PACKET_TYPE, HEADER_SIZE, seq_num, "") # make new ack packet with seq_num
				receiver_socket.sendto(ack_pkt, channel_address) # send ack packet
				print "PKT SEND ACK {0} {1}".format(HEADER_SIZE, seq_num)

				if rcv_buf[(seq_num - base) % MAX_SEQ_NUM] is None: # if have not received the packet with the seq_num
					rcv_buf[(seq_num - base) % MAX_SEQ_NUM] = data # update received buffer with data
					if seq_num == base: # only shift buffer and write into file when having not received yet
						while rcv_buf[0]: # write until next first un-received seq_num
							outfile.write(rcv_buf[0]) # write next packet of data into file
							rcv_buf = shift_buffer_to_left(rcv_buf) # shift buffer to the left by 1 element
							base = (base + 1) % MAX_SEQ_NUM # increment base by 1

			# Packet with sequence number in [rcv_base-N, rcv_base-1] is correctly received
			# an ACK must be generated, even though this is a packet that the receiver has previously acknowledged
			elif check_seq_in_last_window(seq_num, base):
				ack_pkt = make_a_packet(ACK_PACKET_TYPE, HEADER_SIZE, seq_num, "") # make new ack packet with seq_num
				receiver_socket.sendto(ack_pkt, channel_address) # send ack packet, re-acknowledge
				print "PKT SEND ACK {0} {1}".format(HEADER_SIZE, seq_num)

	elif pkt_type == EOT_PACKET_TYPE: # packet is EOT type packet, which is last packet
		print "PKT RECV EOT {0} {1}".format(length, seq_num)
		eot_pkt = make_a_packet(EOT_PACKET_TYPE, HEADER_SIZE, EOT_SEQ_NUM, "") # make EOT packet
		receiver_socket.sendto(eot_pkt, channel_address) # send EOT packet
		print "PKT SEND EOT {0} {1}".format(HEADER_SIZE, EOT_SEQ_NUM)
		break
	else: # received neither DATA packet nor EOT packet
		print "ERROR: Reveived wrong type of packet, expect DATA or EOT packet" # print error msg
		break

outfile.close() # close the output file
receiver_socket.close() # close the socket

