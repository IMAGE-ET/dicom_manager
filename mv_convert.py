import os
import sys
from struct import *
from dataset.dataset import DicomDataset

"""
MedVision file structure is as follows:
	-MedVision study header (24 bytes)
		-Consists of mv_head_1 + number of slices (2 bytes) + mv_head_2
	-Slice header (10 Bytes)
		-Consists of #Rows(2 bytes) + #Columns(2 bytes) + sl_head_part 8 or
		 16 bits depending on data (2 bytes) + two_zeros (2 bytes) + slice 
		 number (2 bytes)
	-Pixel data (2 bytes per pixel if 16bit, 1byte if 8bit)
	-Slice header
	-Pixel data
	-etc.	
"""

mv_head_1 = 'MVSTUDY \x00\x00\x00x\x00\x00\x00\x18\'
mv_head_2 = '\x00\n\x00\x00\x00\x00'
sl_head_part_8bit = ' \x01'
sl_head_part_16bit = '\x10\x02'
two_zeros = '\x00\x00'

data = DicomDataset()
data.get_seq_list()



