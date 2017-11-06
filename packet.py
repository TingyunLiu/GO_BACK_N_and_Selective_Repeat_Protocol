from struct import pack, unpack # import pack, unpack for packet


# constants for protocal selector
GO_BACK_N = 0
SELECTIVE_REPEAT = 1

# some useful constants for sender and receiver to use
HEADER_SIZE = 12
WINDOW_SIZE = 10
DATA_MAX_SIZE = 500
MAX_SEQ_NUM = 256
EOT_SEQ_NUM = 1

# constants indicating different pkt type
DATA_PACKET_TYPE = 0
ACK_PACKET_TYPE = 1
EOT_PACKET_TYPE = 2


#*********************************************************************************************************************
# Function to make a packet with the 4 fields of info as input, it returns a packet
#*********************************************************************************************************************
def make_a_packet(pkt_type, length, seq_num, data):
	packet_format = "> I I I {0}s".format(len(data)) # specify a format for the packet
	pkt = pack(packet_format, pkt_type, length, seq_num, data) # pack it
	return pkt


#*********************************************************************************************************************
# Function to unpacket a packet with specified format, it returns a tuple of size 4
#*********************************************************************************************************************
def unpack_a_packet(pkt):
	unpacket_format = "> I I I {0}s".format(len(pkt) - HEADER_SIZE) # specify a format for the packet
	(pkt_type, length, seq_num, data) = unpack(unpacket_format, pkt) # unpack it
	return (pkt_type, length, seq_num, data)


#*********************************************************************************************************************
# Function to return a packet's length
#*********************************************************************************************************************
def get_packet_length(pkt):
	(pkt_type, length, seq_num, data) = unpack_a_packet(pkt) # unpack it
	return length


#*********************************************************************************************************************
# Function to return a packet's sequence number
#*********************************************************************************************************************
def get_packet_seq_num(pkt):
	(pkt_type, length, seq_num, data) = unpack_a_packet(pkt) # unpack it
	return seq_num


#*********************************************************************************************************************
# Function to make all packets from an input file with maximum 500 bytes per packet, it returns an array of packets
#	with sequence number [0, 255], size, and data correctly embeded, the type is data for all packet
#*********************************************************************************************************************
def make_packets(file):
	infile = open(file, 'rb') # open the file
	all_pkts = [] # store the return array
	index = 0 # keep track of where we are when packing the byte from the file
	while True:
		next_data = infile.read(DATA_MAX_SIZE) # read 500 bytes each time
		if not next_data: # if read failed, end of file
			break
		# make a packet with type = DATA, length = length of data + header size (i.e., 12), seq_num = index % 256
		new_pkt = make_a_packet(DATA_PACKET_TYPE, len(next_data) + HEADER_SIZE, index % MAX_SEQ_NUM, next_data)
		all_pkts.append(new_pkt) # append to the packet array
		index += 1 # increment the index
	return all_pkts # return the packet array


#*********************************************************************************************************************
# Function to check if the seqnum in the window that starts from base.
#	It returns true if seqnum in [base, base+N-1], where N is the window size
#	Note: the seqnum and base are accumulated in a way: 0,1,...,254,255,0,1,...
#*********************************************************************************************************************
def check_seq_in_window(seqnum, base):
	return (((seqnum - base) % MAX_SEQ_NUM) < WINDOW_SIZE) and (((seqnum - base) % MAX_SEQ_NUM) >= 0)


#*********************************************************************************************************************
# Function to check if the seqnum in the previous window that starts from base-N, where N is the window size
#	It returns true if seqnum in [base-N, base-1], where N is the window size
#	Note: the seqnum and base are accumulated in a way: 0,1,...,254,255,0,1,...
#*********************************************************************************************************************
def check_seq_in_last_window(seqnum, base):
	return (((base - seqnum) % MAX_SEQ_NUM) <= WINDOW_SIZE) and (((base - seqnum) % MAX_SEQ_NUM) > 0)


#*********************************************************************************************************************
# Function to shift a buffer to the left by 1 index, it returns the new shifted buffer
#*********************************************************************************************************************
def shift_buffer_to_left(old_buf):
	shifted_buf = [None] * WINDOW_SIZE # initialize a new buffer with all entries None
	for i in range(WINDOW_SIZE-1):
		shifted_buf[i] = old_buf[i+1] # copy each shifted element from old buffer to new buffer
	return shifted_buf # return the new shifted buffer

