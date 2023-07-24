# Original: https://github.com/iidx/bms2bmson-python

#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import re
import sys
import json
import operator
import traceback

__author__ = "xert*"
__version__ = "0.3"
__bmsonversion__ = "1.0.0"

class bms2bmson:
	@staticmethod
	def ToBaseX(str, shift):
		a = str[0]
		b = str[1]
		c = 0

		c += a - ord('A') + 10 if (a >= ord('A') and a <= ord('Z')) else a - ord('0')
		c *= shift
		c += b - ord('A') + 10 if (b >= ord('A') and b <= ord('Z')) else b - ord('0')

		return c

	@staticmethod
	def LoadBMS(bmsfile):
		bmsfilename = bmsfile
		ext_formats = [".bms", ".bme", ".bml", ".pms"]
		ext = os.path.splitext(os.path.basename(bmsfile))[1]

		for ptr, format in enumerate(ext_formats):
			if ext == format:
				with open(bmsfile, "rb") as bmsdata:
					return bmsdata.read()
		return None

	def ExportToJson(self):
		bmson = {}

		bmson["version"] 	 = __bmsonversion__
		bmson["info"] 		 = self.BMSInfo
		bmson["lines"] 		 = self.lines
		bmson["bpm_events"]  = self.bpmnotes
		bmson["stop_events"] = self.stopnotes
		bmson["sound_channels"] = []

		cnotes = {}
		wavslen = len(self.wavHeader)
		for i in range(wavslen):
			cnotes[self.wavHeader[i]["ID"]] = []

		for wn in self.notes:

			if wn["id"] not in cnotes:
				continue
			n = {}
			n["c"] = wn["channel"] > 30

			if wn["channel"] is 1:
				n["x"] = 0
			else:
				n["x"] = (wn["channel"]-10) % 30

			n["y"] = wn["locate"]
			n["l"] = wn["length"]

			cnotes[wn["id"]].append(n)

		for i in range(wavslen):

			tempdict = {}
			tempdict["name"] = self.wavHeader[i]["name"]
			tempdict["notes"] = cnotes[self.wavHeader[i]["ID"]]
			bmson["sound_channels"].append(tempdict)

		bga = {}
		bga["bga_header"] = self.bgaHeader
		bga["bga_events"] = self.bbnotes
		bga["layer_events"] = self.blnotes
		bga["poor_events"] = self.bpnotes

		bmson["bga"] = bga

		self.bmson = bmson

	def GetMetadata(self, bmsdata):

		self.BMSInfo = { "title" 			: None,
						 "subtitle" 		: None,
					     "artist" 			: None,
					     "subartists" 		: None,
					     "genre" 			: None,
					     "mode_hint" 		: "beat-7k",
					     "chart_name" 		: None,
					     "level" 			: 0,
					     "init_bpm" 		: 0.0,
					     "total" 			: 100.0,
					     "back_image" 		: None,
					     "eyecatch_image"	: None,
					     "banner_image" 	: None,
					     "preview_music" 	: None,
					     "resolution" 		: 240 }

		self.wavHeader = []
		self.bgaHeader = []
		self.stopnum = {}
		self.bpmnum = {}

		tags = [ "ARTIST", "GENRE", "TITLE", "BPM", "TOTAL", "PLAYLEVEL" ]
		extags = [ "WAV", "BMP", "BPM", "STOP" ]

		for tag in tags:

			value = re.search(b"#" + str.encode(tag) + b"\s(.+)\r", bmsdata)

			if value is None:
				continue

			value = value.group(1)

			if tag is "PLAYLEVEL" and value is not None:
				self.BMSInfo["level"] = int(value)

			elif tag is "BPM" and value is not None:
				self.BMSInfo["init_bpm"] = float(value)

			elif tag is "TOTAL" and value is not None:
				self.BMSInfo["total"] = float(value)

			elif (tag is "TITLE") or (tag is "GENRE") or (tag is "ARTIST"):
				print(tag, value)
				self.BMSInfo[tag.lower()] = str(value, 'shift-jis')

			else:
				pass

		for tag in extags:

			value = re.findall(b"#" + str.encode(tag) + b"([0-9A-Z]{2})\s(.+)\r", bmsdata)

			if value is not None:

				for v, parameter in value:

					if tag is "WAV":
						self.wavHeader.append({ "ID" : self.ToBaseX(v, 36), "name" : str(parameter, 'shift-jis') })

					elif tag is "BMP":
						self.bgaHeader.append({ "ID" : self.ToBaseX(v, 36), "name" : str(parameter, 'shift-jis') })

					elif tag is "BPM":
						self.bpmnum[self.ToBaseX(v, 36)] = float(parameter)

					elif tag is "STOP":
						self.stopnum[self.ToBaseX(v, 36)] = int(parameter)

		return self.BMSInfo

	def ReadBMSLines(self, bmsdata):

		self.lineh	= { i : 960 for i in range(1000) }
		self.isln 	= { i : False for i in range(4096) }
		self.lines = []
		self.NotePre = []
		self.linemax = 0
		GlobalCounter = 0

		bmslines = re.findall(b"#([0-9]{3})([0-9]{2}):(.+)\r", bmsdata)

		for measure, channel, parameter in bmslines:
			ch = int(channel)
			ms = int(measure)

			if ch >= 10 and ch < 70:
				c = ch % 10
				m = ch / 10

				if c == 6:   c = 8
				elif c == 7: c = 9
				elif c == 8: c = 6
				elif c == 9: c = 7
				ch = m * 10 + c

			if ch == 2:
				self.lineh[ms] = int(960 * float(parameter))

			else:
				paramlen = len(parameter) // 2
				for j in range(paramlen):
					paramsub = parameter[j*2:j*2+2]
					nn = self.ToBaseX(paramsub, 16) if ch == 3 else self.ToBaseX(paramsub, 36)

					if nn is not 0:
						self.linemax = max([self.linemax, ms + 1])
						self.NotePre.append({"x" : ch, "y" : 0, "n" : nn, "ms" : ms, "mm" : paramlen, "mc" : j})

		y = 0
		for i in range(self.linemax + 1):
			self.lines.append({"y" : y})
			y += self.lineh[i]

		for i in range(len(self.NotePre)):
			ms = self.NotePre[i]["ms"]
			seq_y = (self.lines[ms+1]["y"] - self.lines[ms]["y"]) * self.NotePre[i]["mc"] / self.NotePre[i]["mm"]
			self.NotePre[i]["y"] = self.lines[ms]["y"] + seq_y

		self.NotePre = sorted(self.NotePre, key=lambda k: k['y'])

		for i in range(len(self.NotePre)):
			"""
			Longnote Processor

			"""
			ch = self.NotePre[i]['x']

			if (ch > 10 and ch < 50) and self.isln[self.NotePre[i]['n']]:
				pln = i
				while pln - 1 >= 0:
					pln = pln - 1
					ch2 = self.NotePre[pln]['x']
					if ch == ch2:
						self.NotePre.append({ "x" : self.NotePre[pln]['x'],
											  "y" : self.NotePre[pln]['y'],
											  "n" : self.NotePre[pln]['n'],
											  "ms" : 0,
											  "mm" : 0,
											  "mc" : 0 })
						break

			if (ch > 50 and ch < 70):
				pln = i
				while pln + 1 < len(self.NotePre):
					pln = pln + 1
					ch2 = self.NotePre[pln]['x']
					if ch == ch2:
						self.NotePre[i]['length'] = self.NotePre[pln]['y']
						self.NotePre[i]['x'] -= 40
						self.NotePre[pln]['x'] = 0
						break

		TempNotePre = [r for r in self.NotePre if r['x'] != 0]
		self.NotePre = sorted(TempNotePre, key=lambda k: k['y'])

		self.SetNotes()

	def SetNotes(self):

		self.notes = []
		self.bbnotes = []
		self.blnotes = []
		self.bpnotes = []
		self.bpmnotes = []
		self.stopnotes = []

		for i, np in enumerate(self.NotePre):
			if np['x'] in [4, 6, 7]:

				bn = { 'y'  : np['y'],
					   'id' : np['n'] }

				if np['x'] == 4:
					self.bbnotes.append(bn)

				elif np['x'] == 6:
					self.bpnotes.append(bn)

				elif np['x'] == 7:
					self.blnotes.append(bn)

			if (np['x'] == 1) or ((np['x'] / 10 >= 1) and (np['x'] / 10 <= 4)):

				n = { "channel" : np['x'],
					  "id"		: np['n'],
					  "locate"	: np['y'],
					  "length"	: np.get('length', 0) }

				self.notes.append(n)

			else:
				en = { "y" : np['y'] }
				if np['x'] == 3:
					en['v'] = float(np['n'])
					self.bpmnotes.append(en)

				elif np['x'] == 8:
					en['v'] = self.bpmnum[np['n']]
					self.bpmnotes.append(en)

				elif np['x'] == 9:
					en['v'] = self.stopnum[np['n']]
					self.stopnotes.append(en)

	def Convert(self, file):
		bmsdata = self.LoadBMS(file)

		self.GetMetadata(bmsdata)
		self.ReadBMSLines(bmsdata)

		self.ExportToJson()
