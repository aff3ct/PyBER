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
import sys
import reader
import subprocess
import time
import lib.pyqtgraph.pyqtgraph as pg
from lib.pyqtgraph.pyqtgraph.Qt import QtCore, QtGui
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

	dataNoise  = []
	dataBER    = []
	dataFER    = []
	dataBEFE   = []
	dataThr    = []
	dataDeta   = []
	dataName   = []

	#                     1  2  3  4  5  6  7  8  9  10  11  12  13  14  15, 16
	colors             = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17]
	lastSNR            = []
	paths              = []
	styles             = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine, QtCore.Qt.DotLine, QtCore.Qt.DashDotLine, QtCore.Qt.DashDotDotLine]
	dashPatterns       = [[1, 3, 4, 3], [2, 3, 4, 3], [1, 3, 1, 3], [4, 3, 4, 3], [3, 3, 2, 3], [4, 3, 1, 3]]

	NoiseType          = ["Eb/N0",       "Es/N0",       "MI",          "ROP",                         "EP"                 ]
	NoiseTypeLabel     = ["Eb/N0 (dB)",  "Es/N0 (dB)",  "Mutual Info", "Received Optical Power (dB)", "Erasure Probability"]
	BERLegendPosition  = ["BottomLeft",  "BottomLeft",  "BottomLeft",  "BottomLeft",                  "BottomRight"        ]
	FERLegendPosition  = ["BottomLeft",  "BottomLeft",  "BottomLeft",  "BottomLeft",                  "BottomRight"        ]
	BEFELegendPosition = ["TopRight",    "TopRight",    "TopRight",    "TopRight",                    "BottomRight"        ]
	ThrLegendPosition  = ["BottomRight", "BottomRight", "BottomRight", "BottomRight",                 "BottomRight"        ]

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

	def switchNoiseTypeRevert(self):
		if self.NoiseTypeIdx == 0:
			self.NoiseTypeIdx = len(self.NoiseType) -1
		else:
			self.NoiseTypeIdx -= 1

		self.refresh()
		self.setLabel()

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

		self.dataName  = [[] for x in range(len(self.paths))]
		self.dataNoise = [[] for x in range(len(self.paths))]
		self.dataBER   = [[] for x in range(len(self.paths))]
		self.dataFER   = [[] for x in range(len(self.paths))]
		self.dataBEFE  = [[] for x in range(len(self.paths))]
		self.dataThr   = [[] for x in range(len(self.paths))]
		self.dataDeta  = [[] for x in range(len(self.paths))]
		self.lastSNR   = [[] for x in range(len(self.paths))]

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

		self.dataName[pathId] = []
		dataName = []
		self.dataNoise[pathId], self.dataBER[pathId], self.dataFER[pathId], self.dataBEFE[pathId], self.dataThr[pathId], self.dataDeta[pathId], dataName = reader.dataReader(path, self.NoiseType[self.NoiseTypeIdx])

		if not dataName:
			self.dataName[pathId] = "Curve " + str(pathId)
		elif dataName in self.dataName:
			self.dataName[pathId] = dataName + "_" + str(pathId)
		else:
			self.dataName[pathId] = dataName

		if len(self.dataNoise[pathId]) == 0:
			self.dataName[pathId] = "**" + self.dataName[pathId] + "**"
			self.lastSNR[pathId] = -999.0
		else:
			self.lastSNR[pathId] = self.dataNoise[pathId][len(self.dataNoise[pathId]) -1]

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

			self.wBER. plot(x=self.dataNoise[pathId], y=self.dataBER [pathId], pen=pen, symbol='x', name=self.dataName[pathId])
			self.wFER. plot(x=self.dataNoise[pathId], y=self.dataFER [pathId], pen=pen, symbol='x', name=self.dataName[pathId])
			self.wBEFE.plot(x=self.dataNoise[pathId], y=self.dataBEFE[pathId], pen=pen, symbol='x', name=self.dataName[pathId])
			self.wThr. plot(x=self.dataNoise[pathId], y=self.dataThr [pathId], pen=pen, symbol='x', name=self.dataName[pathId])

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
			for entry in self.dataDeta[pathId]:
				if len(entry) == 2 and entry[1]:
					if entry[0] == "Run command":
						runCmd = QtGui.QLineEdit(str(entry[1]))
						runCmd.setReadOnly(True)
						layoutLegend.addRow("<b>" + entry[0] + "</b>: ", runCmd)
					else:
						layoutLegend.addRow("<b>" + entry[0] + "</b>: ", QtGui.QLabel(entry[1]))
				elif len(entry) == 1:
					if len(entry[0]) >= 1 and entry[0][0] == '*':
						e = entry[0].replace("*", "")
						layoutLegend.addRow("<b><u>" + e + ":<u></b>", QtGui.QLabel(""))
					else:
						if not firstTitle:
							line = QtGui.QFrame()
							line.setFrameShape(QtGui.QFrame.HLine)
							line.setFrameShadow(QtGui.QFrame.Sunken)
							layoutLegend.addRow(line)
						firstTitle = False
						layoutLegend.addRow("<h3><u>" + entry[0] + "<u></h3>", QtGui.QLabel(""))

			wCur = QtGui.QWidget();
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

def generatePannel(wBER, wFER, wBEFE, wThr, wDeta):
	if len(sys.argv) >= 2:
		os.chdir(sys.argv[1])
	else:
		os.chdir("./data/")

	model = QtGui.QFileSystemModel()
	model.setReadOnly(True)
	model.setRootPath(QtCore.QDir.currentPath())
	model.setNameFilters(['*.perf', '*.dat', '*.txt', '*.data'])
	model.setNameFilterDisables(False)

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

	return view
