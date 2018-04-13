# The MIT License (MIT)
#
# Copyright (c) 2016 PyBER
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import numpy as np

def getLegend(line):
	line = line.replace("#", "")
	line = line.replace("||", "|")
	line = line.split('|')
	for i in range(len(line)):
		line[i] = line[i].strip()

	return line


def getVal(line):
	line = line.replace("#", "")
	line = line.replace("||", "|")
	line = line.split('|')

	valLine = []
	for i in range(len(line)):
		val = float(0.0)

		try:
			val = float(line[i])

			if "inf" in str(val):
				val = float(0.0)

		except ValueError:
			pass

		valLine.append(val)

	return valLine


def getLegendIdx(legend, colName):
	for i in range(len(legend)):
		if legend[i] == colName:
			return i
	return -1


def dataReader(filename, NoiseType):
	# read all the lines from the current file
	aFile = open(filename, "r")
	lines = []
	for line in aFile:
		lines.append(line)
	aFile.close()

	legend    = []
	data      = []
	dataNoise = []
	dataBER   = []
	dataFER   = []
	dataBEFE  = []
	dataThr   = []
	dataDeta  = []
	dataName  = []

	for line in lines:
		if line.startswith("#"):
			if len(line) > 3 and line[0] == '#' and line[2] == '*':
				entry = line.replace("# * ", "").replace("\n", "").split(" = ")
				if len(entry) == 1:
					entry[0] = entry[0].replace("-", "")
				dataDeta.append(entry)

			elif len(line) > 7 and line[0] == '#' and line[5] == '*' and line[6] == '*':
				entry = line.replace("#    ** ", "").replace("\n", "").split(" = ")
				dataDeta.append(entry)

			elif len(line) > 6 and line[0] == '#' and line[1] == ' ' and line[2] == ' ' and line[3] == ' ' and line[4] == ' ' and line[5] != ' ' and line[5] != '*':
				entry = line.replace("#    ", "*").replace("\n", "").split(" = ")
				if len(entry) == 1:
					entry[0] = entry[0].replace("-", "")
				dataDeta.append(entry)

			elif len(line) > 20 and (line.find("FRA |") != -1 or line.find("BER |") != -1 or line.find("FER |") != -1):
				legend = getLegend(line)

		else:
			if len(legend) != 0:
				d = getVal(line)
				if len(d) == len(legend):
					data.append(d)


	data = np.array(data).transpose()

	dataDeta.append(["Other"])
	dataDeta.append(["File name", os.path.basename(filename)])

	# get the command to to run to reproduce this trace
	if lines and "Run command:" in lines[0]:
		dataDeta.append(["Run command", str(lines[1].strip())])
	else:
		dataDeta.append(["Run command", ""])
	if lines and "Run command:" in lines[2]:
		dataDeta.append(["Run command", str(lines[3].strip())])
	else:
		dataDeta.append(["Run command", ""])

	# get the curve name (if there is one)
	if lines and "Curve name:" in lines[0]:
		dataName = str(lines[1].strip())
	if lines and "Curve name:" in lines[2]:
		dataName = str(lines[3].strip())

	idx = getLegendIdx(legend, NoiseType)

	if len(data) and idx != -1 :
		# set noise range
		idx = getLegendIdx(legend, NoiseType)
		dataNoise = data[idx]

		# set BER
		idx = getLegendIdx(legend, "BER")
		if idx == -1:
			dataBER = [0 for x in range(len(dataNoise))]
		else:
			dataBER = data[idx]

		# set FER
		idx = getLegendIdx(legend, "FER")
		if idx == -1:
			dataFER = [0 for x in range(len(dataNoise))]
		else:
			dataFER = data[idx]

		# set BE/FE
		idx = getLegendIdx(legend, "BE")
		if idx == -1:
			dataBE = [0 for x in range(len(dataNoise))]
		else:
			dataBE = data[idx]

		idx = getLegendIdx(legend, "FE")
		if idx == -1:
			dataFE = [1 for x in range(len(dataNoise))]
		else:
			dataFE = data[idx]

		dataBEFE = [0 for x in range(len(dataNoise))]

		for i in range(len(dataBEFE)):
			try:
				dataBEFE[i] = dataBE[i]/dataFE[i]
			except ZeroDivisionError:
				dataBEFE[i] = float(0)

		# set Througput
		idx = getLegendIdx(legend, "SIM_THR")
		if idx == -1:
			dataThr = [0 for x in range(len(dataNoise))]
		else:
			dataThr = data[idx]

	return dataNoise, dataBER, dataFER, dataBEFE, dataThr, dataDeta, dataName
