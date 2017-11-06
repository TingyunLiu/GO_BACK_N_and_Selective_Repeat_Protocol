from sys import argv # import argv for command line argument
from socket import * # import socket library
from packet import * # import my own packet.py file
import select, os # import select for select polling, os for check is file readable


#*********************************************************************************************************************
# Usage function to handle command line argument
#*********************************************************************************************************************
def usage():
  	print "Usage: ./sender <protocal selector> <timeout> <filename>" # print the usage of the function for sender
  	print "<protocol selector> 0 for Go-Back-N and 1 for Selective Repeat" # print protocal selector information
  	exit()


# check command line argument
# protocal must be in [0,1], timeout must be integer, input file must be readable
if (len(argv) != 4) or (int(argv[1]) != 0 and int(argv[1]) != 1) or \
   (not argv[2].isdigit()) or (not os.access(argv[3], os.R_OK)):
	usage()

protocal = int(argv[1]) # extract protocal for later use
Timeout = float(argv[2]) / 1000 # extract timeout

if not os.access('channelInfo', os.R_OK): # check if 'channelInfo' is readable
	print "Cannot read IP address and port number from channelInfo" # cannot read, print error msg
	exit()
channelInfo = open('channelInfo', 'rb') # open the channelInfo
ip_address, port_num = channelInfo.readline().split(" ") # read IP address and port number from channelInfo
channel_address = (ip_address, int(port_num)) # make a tuple which contains IP address and port number

sndpkts = make_packets(argv[3]) # make all packets from file to send later on
num_of_pkts = len(sndpkts) # calculate the total number of packets need to send
is_ack = [False] * num_of_pkts # keep track of which packet has been acked, initially, set all pkts unacknowledged

sender_socket = socket(AF_INET, SOCK_DGRAM) # create a UDP socket
sender_socket.bind(("",0)) # bind with a random available port number

# Note: to keep base, seq_num, nextseqnum in the range of [0, 255], take a module of 256 when everytime updating them
base = 0 # base of the window
nextseqnum = 0 # next sequence number for the purpost of keep sending limit and acknowledgement tracking
num_of_sent = 0 # keep track of number of packets have sent

while True:
	if (num_of_sent == num_of_pkts) and (base == nextseqnum): # break only when all pkts have been sent AND acked
		break
	# send a packet when it's in the window range, and still have more pkts to send	
	if check_seq_in_window(nextseqnum, base) and (num_of_sent < num_of_pkts):
		sender_socket.sendto(sndpkts[num_of_sent], channel_address) # send next packet to channel
		print "PKT SEND DAT {0} {1}".format(get_packet_length(sndpkts[num_of_sent]), num_of_sent % MAX_SEQ_NUM)
		num_of_sent += 1 # increment the number of packet sent so far
		nextseqnum = (nextseqnum + 1) % MAX_SEQ_NUM # increment the next sequence number
	else:
		wait = select.select([sender_socket], [], [], Timeout) # either wait until an ack or timeout
		if wait[0]: # received an ack
			rcvpkt = sender_socket.recv(1024) # get the ack packet sent from receiver
			(pkt_type, length, seq_num, data) = unpack_a_packet(rcvpkt) # unpack the ack packet
			print "PKT RECV ACK {0} {1}".format(length, seq_num)

			if protocal == GO_BACK_N: # if the protocal is GO_BACK_N
				base = (seq_num + 1) % MAX_SEQ_NUM # simply update the base with sequence number + 1
			else: # protocal is selective repeat
				if (seq_num == base): # sequence number equal to base, base can be moved forward
					is_ack[num_of_sent - (nextseqnum - base) % MAX_SEQ_NUM] = True # set ack array for base
					most_recent_base = base # keep a most recent base for loop condition

					# window base is moved forward to the unacknowledged packet with the smallest seq number
					for i in range(num_of_sent - ((nextseqnum - most_recent_base) % MAX_SEQ_NUM), num_of_sent):
						if is_ack[i]: # next pkt has been acked
							base = (base + 1) % MAX_SEQ_NUM # increment base by 1
						else:
							break # increment base until next unacked
				elif check_seq_in_window(seq_num, base): # if sequence number is within the window
					is_ack[num_of_sent - (nextseqnum - seq_num) % MAX_SEQ_NUM] = True # set seq_num ack to be true

		else: # timeout
			print "Timeout: {0}ms".format(Timeout*1000)
			for i in range(num_of_sent - ((nextseqnum - base) % MAX_SEQ_NUM), num_of_sent): # all pkts in the window

				if protocal == GO_BACK_N: # protocal is GO_BACK_N
					sender_socket.sendto(sndpkts[i], channel_address) # send all pkts in current window
					print "PKT SEND DAT {0} {1}".format(get_packet_length(sndpkts[i]), i % MAX_SEQ_NUM)
				else: # protocal is selective repeat
					if is_ack[i] == False: # if has not been acked
						sender_socket.sendto(sndpkts[i], channel_address) # only send unacked pkts in current window
						print "PKT SEND DAT {0} {1}".format(get_packet_length(sndpkts[i]), i % MAX_SEQ_NUM)

# send last packet, which is end of transfer type of packet
eof_snd_pkt = make_a_packet(EOT_PACKET_TYPE, HEADER_SIZE, EOT_SEQ_NUM, "")
sender_socket.sendto(eof_snd_pkt, channel_address) # send to channel
print "PKT SEND EOT {0} {1}".format(HEADER_SIZE, EOT_SEQ_NUM)

while True: # waiting for until an end of transfer packet confirmation from receiver
	eot_rcv_pkt = sender_socket.recv(1024) # receive a packet
	(pkt_type, length, seq_num, data) = unpack_a_packet(eot_rcv_pkt) # unpack
	if pkt_type == EOT_PACKET_TYPE: # break when it's a EOT packet
		print "PKT RECV EOT {0} {1}".format(length, seq_num)
		break

sender_socket.close() # close the sender socket

