#!/usr/bin/python3

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

import PyQt5
import lib.pyqtgraph.pyqtgraph.console
import lib.pyqtgraph.pyqtgraph as pg
from lib.pyqtgraph.pyqtgraph.Qt import QtCore, QtGui
from lib.pyqtgraph.pyqtgraph.dockarea import *
import numpy as np
import fileExplorer

# uncomment those next lines to display the plot in black on white instead of white on black
# pg.setConfigOption('background', 'w')
# pg.setConfigOption('foreground', 'k')

app  = QtGui.QApplication(['PyBER Plotter'])
win  = QtGui.QMainWindow()
area = DockArea()
win.setCentralWidget(area)
win.resize(1280,800)
win.setWindowTitle('PyBER Plotter')
win.setWindowIcon(QtGui.QIcon('img/woody_ico.png'))

# Create docks, place them into the window one at a time.
# Note that size arguments are only a suggestion; docks will still have to
# fill the entire dock area and obey the limits of their internal widgets.
dFile = Dock("File explorer",               size=(275,400))
dDeta = Dock("Details",                     size=(275,400))
dBER  = Dock("Bit Error Rate (BER)",        size=(400,200))
dFER  = Dock("Frame Error Rate (FER)",      size=(400,200))
dBEFE = Dock("BE/FE",                       size=(400,125))
dThr  = Dock("Simulation coded throughput", size=(400,125))

area.addDock(dFile, 'left'         )
area.addDock(dBER,  'right',  dFile)
area.addDock(dFER,  'right',  dBER )
area.addDock(dBEFE, 'bottom', dBER )
area.addDock(dThr,  'bottom', dFER )
area.addDock(dDeta, 'bottom', dFile)

# Add widgets into each dock
pg.setConfigOptions(antialias=True)

wDeta = QtGui.QTabWidget()
dDeta.addWidget(wDeta)

wBER = pg.PlotWidget(labels={'left': "Bit Error Rate", 'bottom': "Eb/N0 (dB)"})
wBER.plot(np.random.random_sample(size=100))
wBER.showGrid(True,  True)
wBER.setLogMode(False, True)
wBER.showLabel('left', True)
wBER.showLabel('bottom', True)
dBER.addWidget(wBER)

wFER = pg.PlotWidget(labels={'left': "Frame Error Rate", 'bottom': "Eb/N0 (dB)"})
wFER.plot(np.random.random_sample(size=100))
wFER.showGrid(True,  True)
wFER.setLogMode(False, True)
wFER.showLabel('left', True)
wFER.showLabel('bottom', True)
dFER.addWidget(wFER)

wBEFE = pg.PlotWidget(labels={'left': "BE/FE", 'bottom': "Eb/N0 (dB)"})
wBEFE.plot(np.random.random_sample(size=100))
wBEFE.showGrid(True,  True)
wBEFE.showLabel('left', True)
wBEFE.showLabel('bottom', True)
dBEFE.addWidget(wBEFE)

wThr = pg.PlotWidget(labels={'left': "Throughput (Mbps)", 'bottom': "Eb/N0 (dB)"})
wThr.plot(np.random.random_sample(size=100))
wThr.showGrid(True,  True)
wThr.showLabel('left', True)
wThr.showLabel('bottom', True)
dThr.addWidget(wThr)

wFile = fileExplorer.generatePannel(wBER, wFER, wBEFE, wThr, wDeta)
dFile.addWidget(wFile)

# -----------------------------------------------------------------------------

exitAction = QtGui.QAction('&Exit', win)
exitAction.setShortcut('Ctrl+Q')
exitAction.setStatusTip('Exit application')
exitAction.triggered.connect(lambda: sys.exit(0))

selectFolderAction = QtGui.QAction('&Open Folder', win)
selectFolderAction.setShortcut('Ctrl+O')
selectFolderAction.setStatusTip('Open a folder to browse')
selectFolderAction.triggered.connect(lambda: wFile.selectFolder())

autoSelectNoiseAction = QtGui.QAction('&Auto select noise', win)
autoSelectNoiseAction.setShortcut('Ctrl+A')
autoSelectNoiseAction.setStatusTip('Automatically select a noise type with the selected files')
autoSelectNoiseAction.triggered.connect(lambda: wFile.autoSelectNoise())

switchNoiseTypeAction = QtGui.QAction('&Switch Noise Type', win)
switchNoiseTypeAction.setShortcut('Ctrl+E')
switchNoiseTypeAction.setStatusTip('Switch abscissa between Eb/N0, Es/N0, MI, ROP, EP...')
switchNoiseTypeAction.triggered.connect(lambda: wFile.switchNoiseType())

switchNoiseTypeRevertAction = QtGui.QAction('&Switch Noise Type (revert order)', win)
switchNoiseTypeRevertAction.setShortcut('Ctrl+Shift+E')
switchNoiseTypeRevertAction.setStatusTip('Switch abscissa between EP, ROP, MI, Es/N0, Eb/N0...')
switchNoiseTypeRevertAction.triggered.connect(lambda: wFile.switchNoiseTypeRevert())

switchFileFilterAction = QtGui.QAction('&Enable/Disable File Filter', win)
switchFileFilterAction.setShortcut('Ctrl+F')
switchFileFilterAction.setStatusTip('Enable or disable the file filter (*.perf, *.dat, *.txt, *.data)')
switchFileFilterAction.triggered.connect(lambda: wFile.switchFileFilter())

refreshAction = QtGui.QAction('&Refresh', win)
refreshAction.setShortcut('F5')
refreshAction.setStatusTip('Refresh the displayed curves')
refreshAction.triggered.connect(lambda: wFile.refresh())

win.statusBar()

menubar = win.menuBar()
fileMenu = menubar.addMenu('&File')
fileMenu.addAction(selectFolderAction)
fileMenu.addAction(exitAction)
optionMenu = menubar.addMenu('&Display')
optionMenu.addAction(refreshAction)
optionMenu.addAction(autoSelectNoiseAction)
optionMenu.addAction(switchNoiseTypeAction)
optionMenu.addAction(switchNoiseTypeRevertAction)
optionMenu.addAction(switchFileFilterAction)

# -----------------------------------------------------------------------------

win.show()

# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
	import sys
	if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
		QtGui.QApplication.instance().exec_()