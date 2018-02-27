#!/usr/bin/env python

import sys
import struct

def word_align(value, word_size = 4):
	if value % word_size == 0:
		return value
	else:
		return ((value / word_size) + 1) * word_size

class FrameReader:
	default_frame_format = "QHHHH"
	default_frame_size = 16 # bytes

	@staticmethod
	def validframe(header, word_size, big_endian):
		if big_endian:
			time, record_len, text_len, dict_len, flags = struct.unpack(
					">" + FrameReader.default_frame_format, header)
		else:
			time, record_len, text_len, dict_len, flags = struct.unpack(
					"<" + FrameReader.default_frame_format, header)

		if record_len == 0:
			return None

		calc_len = (FrameReader.default_frame_size +
				word_align(text_len + dict_len, word_size))

		if record_len == calc_len:
			return True
		return False

	@staticmethod
	def getframelayout(header):
		if FrameReader.validframe(header, 4, False):
			return (False, 4, "<" + FrameReader.default_frame_format)
		elif FrameReader.validframe(header, 8, False):
			return (False, 8, "<" + FrameReader.default_frame_format)
		elif FrameReader.validframe(header, 4, True):
			return (True, 4, ">" + FrameReader.default_frame_format)
		elif FrameReader.validframe(header, 8, True):
			return (True, 8, ">" + FrameReader.default_frame_format)
		else:
			return None

	@staticmethod
	def load(stream):
		frames = []
		frameformat = None
		while True:
			buffer = stream.read(FrameReader.default_frame_size)
			if len(buffer) == 0:
				# eof
				break
			if len(buffer) != FrameReader.default_frame_size and len(buffer) != 0:
				print("error: corrupt data?")
				break

			if not frameformat:
				frameformat = FrameReader.getframelayout(buffer)
				if not frameformat:
					print("error: cannot figure out message structure layout, corrupt data?")
					break

			time, record_len, text_len, dict_len, flags = struct.unpack(
					frameformat[2], buffer)
			if record_len == 0:
				break # end messages

			expected_len = word_align(record_len - FrameReader.default_frame_size,
					frameformat[1])
			record = stream.read(expected_len)

			text_sect = record[0:text_len]
			dict_sect = record[text_len:(text_len + dict_len)]

			frame = {
				"time" : time,
				"flags" : flags,
				"text" : text_sect,
				"dict" : dict_sect,
				}

			frames.append(frame)
		return frames

def usage():
	print("logbufreader - Interpret binary logbuf dumps")
	print("")
	print("\tlogbufreader.py <binary logbuf>")
	print("")

def main(args):
	if (len(args) != 2):
		usage()
		return -1

	target = args[1]

	frames = None
	with open(target, "rb") as f:
		frames = FrameReader.load(f)

	for i in frames:
		print("[% 16.3f] %s" % (
				(float(i["time"]) / 1000),
				i["text"].replace("\n", "\n" + " " * 19)))
	return 0

sys.exit(main(sys.argv))
