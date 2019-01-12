# The MIT License (MIT)
#
# Copyright (c) 2018 PyBER
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

import sys
import os
from data.refs.readers.aff3ct_trace_reader import aff3ctTraceReader
import subprocess
import time
import lib.pyqtgraph.pyqtgraph as pg
from lib.pyqtgraph.pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from lib.pyqtgraph.pyqtgraph.dockarea import *
import numpy as np

class AdvTreeView(QtGui.QTreeView):
	wBER      = []
	wFER      = []
	wBEFE     = []
	wThr      = []
	wDeta     = []
	fsWatcher = []

	lBER  = []
	lFER  = []
	lBEFE = []
	lThr  = []

	NoiseTypeIdx = []

	Curves   = []
	dataBEFE = []
	dataName = []

	#                     1  2  3  4  5  6  7  8  9  10  11  12  13  14  15, 16
	colors             = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17]
	lastNoise          = []
	paths              = []
	styles             = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine, QtCore.Qt.DotLine, QtCore.Qt.DashDotLine, QtCore.Qt.DashDotDotLine]
	dashPatterns       = [[1, 3, 4, 3], [2, 3, 4, 3], [1, 3, 1, 3], [4, 3, 4, 3], [3, 3, 2, 3], [4, 3, 1, 3]]

	NoiseType          = ["ebn0",        "esn0",        "mi",          "rop",                         "ep"               ]
	NoiseTypeLabel     = ["Eb/N0 (dB)",  "Es/N0 (dB)",  "Mutual Info", "Received Optical Power (dB)", "Event Probability"]
	BERLegendPosition  = ["BottomLeft",  "BottomLeft",  "BottomLeft",  "BottomLeft",                  "BottomRight"      ]
	FERLegendPosition  = ["BottomLeft",  "BottomLeft",  "BottomLeft",  "BottomLeft",                  "BottomRight"      ]
	BEFELegendPosition = ["TopRight",    "TopRight",    "TopRight",    "TopRight",                    "BottomRight"      ]
	ThrLegendPosition  = ["BottomRight", "BottomRight", "BottomRight", "BottomRight",                 "BottomRight"      ]

	def __init__(self, wBER, wFER, wBEFE, wThr, wDeta):
		super().__init__()

		self.wBER  = wBER
		self.wFER  = wFER
		self.wBEFE = wBEFE
		self.wThr  = wThr
		self.wDeta = wDeta

		# create a legend on the plots
		self.lBER  = self.wBER .addLegend()
		self.lFER  = self.wFER .addLegend()
		self.lBEFE = self.wBEFE.addLegend()
		self.lThr  = self.wThr .addLegend()

		self.NoiseTypeIdx = 0
		self.NoiseSelectedByUser = False
		self.refreshing_time = time.time()

		self.hideLegend()

		self.doubleClicked.connect(self.openFileOrDir)
		self.fsWatcher = QtCore.QFileSystemWatcher()
		self.fsWatcher.fileChanged.connect(self.updateDataAndCurve)

	def switchNoiseType(self):
		self.NoiseTypeIdx += 1

		if self.NoiseTypeIdx == len(self.NoiseType):
			self.NoiseTypeIdx = 0

		self.refresh()
		self.setLabel()
		self.NoiseSelectedByUser = True

	def switchNoiseTypeRevert(self):
		if self.NoiseTypeIdx == 0:
			self.NoiseTypeIdx = len(self.NoiseType) -1
		else:
			self.NoiseTypeIdx -= 1

		self.refresh()
		self.setLabel()
		self.NoiseSelectedByUser = True

	def setLabel(self):
		newLabel = self.NoiseTypeLabel[self.NoiseTypeIdx]
		self.wBER .setLabel('bottom', newLabel)
		self.wFER .setLabel('bottom', newLabel)
		self.wBEFE.setLabel('bottom', newLabel)
		self.wThr .setLabel('bottom', newLabel)

		if len(self.paths):
			self.showLegend()
		else:
			self.hideLegend()

	def refresh(self):
		for name in self.dataName:
			self.removeLegendItem(name)

		self.Curves   = [[] for x in range(len(self.paths))]
		self.dataBEFE = [[] for x in range(len(self.paths))]
		self.dataName = [[] for x in range(len(self.paths))]

		for path in self.paths:
			self.updateData(path)

		self.updateCurves ()
		self.updateDetails()

	def switchFileFilter(self):
		self.model().setNameFilterDisables(not self.model().nameFilterDisables())

	def openFileOrDir(self, *args):
		paths = [ self.model().filePath(index) for index in args ]
		if len(paths):
			if sys.platform == "linux" or sys.platform == "linux2":
				subprocess.call(["xdg-open", paths[0]])
			elif sys.platform == "darwin":
				subprocess.call(["open", paths[0]])
			else:
				os.startfile(paths[0])

	def hideLegend(self):
		# hide the legend
		if self.lBER:  self.lBER  = self.setLegendPosition(self.lBER,  "Hide")
		if self.lFER:  self.lFER  = self.setLegendPosition(self.lFER,  "Hide")
		if self.lBEFE: self.lBEFE = self.setLegendPosition(self.lBEFE, "Hide")
		if self.lThr:  self.lThr  = self.setLegendPosition(self.lThr,  "Hide")

	def setLegendPosition(self, legend, pos):
		if pos == "BottomLeft":
			legend.anchor(itemPos=(0,1), parentPos=(0,1), offset=( 10,-10))
		elif pos == "BottomRight":
			legend.anchor(itemPos=(1,1), parentPos=(1,1), offset=(-10,-10))
		elif pos == "TopRight":
			legend.anchor(itemPos=(1,0), parentPos=(1,0), offset=(-10, 10))
		elif pos == "TopLeft":
			legend.anchor(itemPos=(0,0), parentPos=(0,0), offset=( 10, 10))
		elif pos == "Hide":
			legend.anchor(itemPos=(1,0), parentPos=(1,0), offset=(100, 100))

		return legend

	def showLegend(self):
		# display the legend
		if self.lBER:  self.lBER  = self.setLegendPosition(self.lBER,  self.BERLegendPosition [self.NoiseTypeIdx])
		if self.lFER:  self.lFER  = self.setLegendPosition(self.lFER,  self.FERLegendPosition [self.NoiseTypeIdx])
		if self.lBEFE: self.lBEFE = self.setLegendPosition(self.lBEFE, self.BEFELegendPosition[self.NoiseTypeIdx])
		if self.lThr:  self.lThr  = self.setLegendPosition(self.lThr,  self.ThrLegendPosition [self.NoiseTypeIdx])

	def removeLegendItem(self, name):
		if self.lBER:  self.lBER .removeItem(name)
		if self.lFER:  self.lFER .removeItem(name)
		if self.lBEFE: self.lBEFE.removeItem(name)
		if self.lThr:  self.lThr .removeItem(name)

	def getPathId(self, path):
		if path in self.paths:
			curId = 0
			for p in self.paths:
				if p == path:
					return curId
				else:
					curId = curId +1
			return -1
		else:
			return -1

	def updateData(self, path):
		pathId = self.getPathId(path)
		if pathId == -1:
			return

		self.Curves  [pathId] = aff3ctTraceReader(path)
		self.dataBEFE[pathId] = [b/f for b,f in zip(self.Curves[pathId].getTrace("n_be"), self.Curves[pathId].getTrace("n_fe"))]

		dataName = self.Curves[pathId].getMetadata("title")

		if not dataName:
			self.dataName[pathId] = "Curve " + str(pathId)
		elif dataName in self.dataName:
			self.dataName[pathId] = dataName + "_" + str(pathId)
		else:
			self.dataName[pathId] = dataName

		if not self.Curves[pathId].legendKeyAvailable(self.NoiseType[self.NoiseTypeIdx]):
			self.dataName[pathId] = "**" + self.dataName[pathId] + "**"

	def updateCurves(self):
		self.wBER .clearPlots()
		self.wFER .clearPlots()
		self.wBEFE.clearPlots()
		self.wThr .clearPlots()

		# plot the curves
		for pathId in range(len(self.paths)):
			icolor = self.colors[pathId % len(self.colors)]
			pen = pg.mkPen(color=(icolor,8), width=2, style=QtCore.Qt.CustomDashLine)
			pen.setDashPattern(self.dashPatterns[pathId % len(self.dashPatterns)])


			self.removeLegendItem(self.dataName[pathId])

			noiseKey = self.NoiseType[self.NoiseTypeIdx]

			if self.Curves[pathId].legendKeyAvailable(noiseKey):
				self.wBER. plot(x=self.Curves[pathId].getTrace(noiseKey), y=self.Curves[pathId].getTrace("be_rate"), pen=pen, symbol='x', name=self.dataName[pathId])
				self.wFER. plot(x=self.Curves[pathId].getTrace(noiseKey), y=self.Curves[pathId].getTrace("fe_rate"), pen=pen, symbol='x', name=self.dataName[pathId])
				self.wBEFE.plot(x=self.Curves[pathId].getTrace(noiseKey), y=self.dataBEFE[pathId], pen=pen, symbol='x', name=self.dataName[pathId])
				self.wThr. plot(x=self.Curves[pathId].getTrace(noiseKey), y=self.Curves[pathId].getTrace("sim_thr"), pen=pen, symbol='x', name=self.dataName[pathId])
			else:
				self.wBER. plot(x=[], y=[], pen=pen, symbol='x', name=self.dataName[pathId])
				self.wFER. plot(x=[], y=[], pen=pen, symbol='x', name=self.dataName[pathId])
				self.wBEFE.plot(x=[], y=[], pen=pen, symbol='x', name=self.dataName[pathId])
				self.wThr. plot(x=[], y=[], pen=pen, symbol='x', name=self.dataName[pathId])

	def updateDataAndCurve(self, path):
		if (self.refreshing_time + 0.1) < time.time(): # timer to not freeze because of several refreshes asked at the same time
			self.refresh()
			self.refreshing_time = time.time()

	def updateDetails(self):
		self.wDeta.clear()

		for pathId in range(len(self.paths)):
			icolor = self.colors[pathId % len(self.colors)]
			path   = self.paths[pathId]

			# for filename in self.paths:
			pen = pg.mkPen(color=(icolor,8), width=2, style=QtCore.Qt.CustomDashLine)
			pen.setDashPattern(self.dashPatterns[pathId % len(self.dashPatterns)])

			legendArea = DockArea()
			dInfo      = Dock("", size=(250,900))

			legendArea.addDock(dInfo, 'bottom')

			firstTitle   = True;
			layoutLegend = QtGui.QFormLayout()
			for entry in self.Curves[pathId].SimuHeader:
				if len(entry) == 3 and entry[1]:
					if entry[2] == 1:
						if not firstTitle:
							line = QtGui.QFrame()
							line.setFrameShape(QtGui.QFrame.HLine)
							line.setFrameShadow(QtGui.QFrame.Sunken)
							layoutLegend.addRow(line)
						firstTitle = False
						layoutLegend.addRow("<h3><u>" + entry[0] + "<u></h3>", QtGui.QLabel(""))

					elif entry[2] == 2:
						layoutLegend.addRow("<b><u>" + entry[0] + ":<u></b>", QtGui.QLabel(""))

					elif entry[2] == 3:
						layoutLegend.addRow("<b>" + entry[0] + "</b>: ", QtGui.QLabel(entry[1]))


			# Add an horizontal line to seperate
			line = QtGui.QFrame()
			line.setFrameShape(QtGui.QFrame.HLine)
			line.setFrameShadow(QtGui.QFrame.Plain)
			layoutLegend.addRow(line)
			layoutLegend.addRow("<h3><u>Metadata<u></h3>", QtGui.QLabel(""))

			for entry in self.Curves[pathId].Metadata:
				if entry == "doi":
					url = QtGui.QLineEdit("https://doi.org/" + self.Curves[pathId].Metadata[entry])
					url.setReadOnly(True)
					layoutLegend.addRow("<b>" + entry + "</b>: ", url)
				# if entry == "url":
				# 	url = QtGui.QLabel(str(self.Curves[pathId].Metadata[entry]))
				# 	url.setOpenExternalLinks(True)
				# 	url.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
				# 	layoutLegend.addRow("<b>" + entry + "</b>: ", url)
				# elif entry == "filename":
				# 	url = QtGui.QLabel(str(self.Curves[pathId].Metadata[entry]))
				# 	url.setOpenInternalLinks(True)
				# 	url.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
				# 	layoutLegend.addRow("<b>" + entry + "</b>: ", url)
				else:
					lineEdit = QtGui.QLineEdit(self.Curves[pathId].Metadata[entry])
					lineEdit.setReadOnly(True)
					layoutLegend.addRow("<b>" + entry + "</b>: ", lineEdit)

			wCur = QtGui.QWidget()
			wCur.setLayout(layoutLegend)

			sCur = QtGui.QScrollArea()
			sCur.setWidget(wCur)
			sCur.setWidgetResizable(True)
			dInfo.addWidget(sCur)

			self.wDeta.addTab(legendArea, self.dataName[pathId])

	def selectionChanged(self, selected, deselected):
		super().selectionChanged(selected, deselected)
		newPaths = [ self.model().filePath(index) for index in self.selectedIndexes()
		                if not self.model().isDir(index)] # TODO: remove this restriction

		pathsToRemove = []
		for p in self.paths:
			if p not in newPaths:
				pathsToRemove.append(p)

		for p in pathsToRemove:
			pId = self.getPathId(p)
			self.paths.pop(pId)

		pathsToAdd = []
		for p in newPaths:
			if p not in self.paths:
				pathsToAdd.append(p)
		for p in pathsToAdd:
			self.paths.append(p)

		if len(pathsToRemove) > 0:
			self.fsWatcher.removePaths(pathsToRemove)
		if len(pathsToAdd) > 0:
			self.fsWatcher.addPaths(pathsToAdd)

		self.refresh ()
		self.setLabel()

		if not self.NoiseSelectedByUser:
			self.autoSelectNoise()

	def autoSelectNoise(self):
		save = self.NoiseTypeIdx

		found = False

		for i in range(len(self.NoiseType)):
			self.NoiseTypeIdx = i
			self.refresh()

			noiseKey = self.NoiseType[self.NoiseTypeIdx]

			for t in self.Curves:
				if t.legendKeyAvailable(noiseKey):
					found = True
					break;

			if found:
				self.setLabel()
				break;

		if not found:
			self.NoiseTypeIdx = save
			self.refresh ()
			self.setLabel()

		self.NoiseSelectedByUser = False

	def selectFolder(self):
		options = QtWidgets.QFileDialog.Options()
		# options |= QtWidgets.QFileDialog.DontUseNativeDialog
		# options |= QtGui.QFileDialog.ShowDirsOnly
		dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Open a folder", "", options=options)
		if dirPath:
			oldModel = self.model()
			model = createFileSystemModel(dirPath)
			self.setModel(model)
			self.setRootIndex(model.index(dirPath, 0))
			del oldModel

def createFileSystemModel(dirPath):
	model = QtGui.QFileSystemModel()
	model.setReadOnly(True)
	model.setRootPath(dirPath)
	model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs | QtCore.QDir.AllEntries | QtCore.QDir.Files)
	model.setNameFilters(['*.perf', '*.dat', '*.txt', '*.data'])
	model.setNameFilterDisables(False)

	return model

def generatePannel(wBER, wFER, wBEFE, wThr, wDeta):
	if len(sys.argv) >= 2:
		os.chdir(sys.argv[1])
	else:
		os.chdir("./data/")

	model = createFileSystemModel(QtCore.QDir.currentPath())

	view = AdvTreeView(wBER, wFER, wBEFE, wThr, wDeta)
	view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
	view.setModel(model)
	view.hideColumn(1);
	view.hideColumn(2);
	view.hideColumn(3);
	view.setColumnWidth(30, 1)
	view.setRootIndex(model.index(QtCore.QDir.currentPath(), 0))
	view.setAnimated(True)
	view.setIconSize(QtCore.QSize(24,24))
	view.setExpandsOnDoubleClick(False);

	return view
