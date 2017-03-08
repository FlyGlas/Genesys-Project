#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob
from PyQt4 import QtGui, QtCore
#import pyqtgraph as pg
#import numpy as np
import serial



########################################################################
# Function to find all available serial ports on the system
# Source: https://github.com/mwaylabs/fruitymesh/blob/master/util/term/startTerms.py
def serialPorts():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
########################################################################
  
    
########################################################################
# Override readline() from pySerial to change eol character
# from \n to \r. With this modifiction not every use of readline() 
# waits for a timeout.
class mySerial(serial.Serial):   
    
    def readline(self):
        eol = b'\r'
        leneol = len(eol)
        line = bytearray()
        while True:
            c = super().read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line)
########################################################################   
    
########################################################################
# Modify QCheckBox and add possibility to disable user modification
class MyQCheckBox(QtGui.QCheckBox):
    
    def __init__(self, *args, **kwargs):
        QtGui.QCheckBox.__init__(self, *args, **kwargs)        
        self.is_modifiable = True
        self.clicked.connect( self.value_change_slot )

    def value_change_slot(self): 
        if self.isChecked():
            self.setChecked(self.is_modifiable)
        else:
            self.setChecked(not self.is_modifiable)            

    def setModifiable(self, flag):
        self.is_modifiable = flag            

    def isModifiable(self):
        return self.is_modifiable   
########################################################################  

########################################################################
# Creat class for data storage        
class DataContainer():
    def __init__(self, _PV=0.0, _PC=0.0, _MV=0.0, _MC=0.0, _POVP=0.0, _PUVL=0.0,
                       _SRCV=False,_SRCC=False, _SRNFLT=True, _SRFLT=False, _SRAST=False, _SRFDE=False, _SRLCL=False,
                       _FRAC=False, _FROTP=False, _FRFOLD=False, _FROVP=False, _FRSO=False, _FROFF=False, _FRENA=False,
                       _OUTPUT=False,
                       _DeviceIDN = "", _DeviceREV = "", _DeviceSN = "", _DeviceDATE = ""):
        self.PV = _PV         #Programmed Voltage
        self.PC = _PC         #Programmed Current
        self.MV = _MV         #Measured Voltage
        self.MC = _MC         #Measured Current
        self.POVP = _POVP     #Programmed Overvoltage Protection
        self.PUVL = _PUVL     #Programmed Untervoltage Protection
        self.SRCV = _SRCV     #Status Register Constant Voltage
        self.SRCC = _SRCC     #Status Register Constant Current
        self.SRNFLT = _SRNFLT #Status Register No Fault
        self.SRFLT = _SRFLT   #Status Register Fault
        self.SRAST = _SRAST   #Status Register Auto Start
        self.SRFDE = _SRFDE   #Status Register Fold Back Enabled
        self.SRLCL = _SRLCL   #Status Register Local Mode Enabled
        self.FRAC = _FRAC     #Fault Register AC Fail
        self.FROTP = _FROTP   #Fault Register Over Temperature
        self.FRFOLD = _FRFOLD #Fault Register Foldback 
        self.FROVP = _FROVP   #Fault Register Overvoltage
        self.FRSO = _FRSO     #Fault Register Shut OFF
        self.FROFF = _FROFF   #Fault Register Output Off
        self.FRENA = _FRENA   #Fault Register Enable
        self.OUTPUT = _OUTPUT #Status Output (True=ON, False=OFF)
        self.DeviceIDN  = _DeviceIDN
        self.DeviceREV   = _DeviceREV
        self.DeviceSN   = _DeviceSN
        self.DeviceDATE = _DeviceDATE
        
    @property
    def MP(self):
        return self.MV * self.MC
        
    @property
    def minPOVP(self):
        value = self.PV/100 * 105
        if value < 5.00:
            return 5.00
        else:
            return round(value, 2)# + 0.05
    @property            
    def maxPUVL(self):
        value = self.PV/100 * 95
        if value > 47.50:
            return 47.50
        else:
            return round(value, 2)# - 0.05
        
    @property
    def minPV(self):
        value = self.PUVL/95 * 100
        if value < 0.00:
            return 0.00
        else:
            return round(value , 2)# + 0.05
    @property            
    def maxPV(self):
        value = self.POVP/105 * 100
        if value > 50.00:
            return 50.00
        else:
            return round(value , 2)# - 0.05
########################################################################
GenData = DataContainer()
########################################################################


########################################################################
class ComSerial:
    def __init__(self):
        super(ComSerial, self).__init__()
        self.ser = mySerial()
        self.ComPort = ""
        self.ComADR = ""
        self.ComSpeed = ""
        self.Connected = False
        
    def SetComPort(self,_ComPort):
        self.ComPort = _ComPort
        
    def SetComAddress(self,_ComADR):
        self.ComADR = _ComADR
        
    def SetComSpeed(self, _ComSpeed):
        self.ComSpeed = _ComSpeed
        
    def IsConnected(self):
        return self.Connected
        
    def ConnectPort(self):
        try:
            self.ser = mySerial(port=self.ComPort,
	            baudrate=self.ComSpeed,
	            timeout=1,
	            parity=serial.PARITY_NONE,
	            stopbits=serial.STOPBITS_ONE,
	            bytesize=serial.EIGHTBITS)
            self.ser.isOpen() # try to open port, if possible print message and proceed with 'while True:'
            self.Connected = True
            print ('Port ' + self.ComPort + ' is opened!')

        except IOError: # if port is already opened, close it and open it again and print message
            self.ser.close()
            self.ser.open()
            self.Connected = True
            print ('Port ' + self.ComPort + ' was already open, was closed and opened again!')    

    def DisconnectPort(self):
        self.ser.close()
        self.Connected = False
        print ('Port ' + self.ComPort + ' is closed!')
    
    def ConnectDevice(self):
        print('Start: Send ADR 0' + str(self.ComADR))
        if self.ser.isOpen():
            self.ser.write(('ADR 0' + str(self.ComADR) +'\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.ConnectDevice()
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False

    def SetOutputON(self):
        print("Start: Send OUT 1")
        if self.ser.isOpen():
            self.ser.write(('OUT 1\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetOutputON()
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False

    def SetOutputOFF(self):
        print("Start: Send OUT 0")
        if self.ser.isOpen():
            self.ser.write(('OUT 0\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetOutputOFF()
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False

    def SetFLDON(self):
        print("Start: Send FLD 1")
        if self.ser.isOpen():
            self.ser.write(('FLD 1\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetOutputON()
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False

    def SetFLDOFF(self):
        print("Start: Send FLD 0")
        if self.ser.isOpen():
            self.ser.write(('FLD 0\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetOutputOFF()
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False
           
    def SetVoltage(self, voltage):
        print("Start: Send PV n")
        if self.ser.isOpen():
            self.ser.write(('PV ' + str(voltage) + '\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetVoltage(voltage)
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False

    def SetCurrent(self, current):
        print("Start: Send PC n")
        if self.ser.isOpen():
            self.ser.write(('PC ' + str(current) + '\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetCurrent(current)
            if test == 'OK\r':
                print('Answer: ' + test)
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False
           
    def SetOVP(self, voltage):
        print("Start: Send OVP n")   
        if self.ser.isOpen():
            self.ser.write(('OVP ' + str(voltage) + '\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetOVP(voltage)
            if test == 'OK\r':
                print('Answer: ' + test)
                self.QueryOVP()
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False
   
    def SetUVL(self, voltage):
        print("Start: Send UVL n")   
        if self.ser.isOpen():
            self.ser.write(('UVL ' + str(voltage) + '\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'OK\r':
            #    self.SetUVL(voltage)
            if test == 'OK\r':
                print('Answer: ' + test)
                self.QueryUVL()
                return True
            else:
                print('Answer: No reaction from Device.')
                return False
        else:
            print('Answer: No connection to Port.')
            return False                   
            
    def QueryOUT(self):
        print("Start: Query OUT?")   
        if self.ser.isOpen():
            self.ser.write(('OUT?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != ('ON\r' or 'OFF\r'):
            #    self.QueryOUT() 
            if test == 'ON\r':
                print('Answer: ' + test)
                GenData.OUTPUT = True
            if test == 'OFF\r':
                print('Answer: ' + test)
                GenData.OUTPUT = False 
        else:
            print('Anser: No connection to Port.')
                
                
    def QueryOVP(self): 
        print("Start: Query OVP?")                      
        if self.ser.isOpen():
            self.ser.write(('OVP?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            print('Answer: ' + test)
            GenData.POVP = float(test)
        else:
            print('Anser: No connection to Port.')
            
    def QueryUVL(self):  
        print("Start: Query UVL?")                     
        if self.ser.isOpen():
            self.ser.write(('UVL?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            print('Answer: ' + test)
            GenData.PUVL = float(test)  
        else:
            print('Anser: No connection to Port.')
            
    def QueryPC(self):    
        print("Start: Query PC?")                   
        if self.ser.isOpen():
            self.ser.write(('PC?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            print('Answer: ' + test)
            GenData.PC = float(test)
        else:
            print('Anser: No connection to Port.')
                    
    def QueryPV(self):   
        print("Start: Query PV?")                    
        if self.ser.isOpen():
            self.ser.write(('PV?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            print('Answer: ' + test)
            GenData.PV = float(test)
        else:
            print('Anser: No connection to Port.')
            
    def QueryFLD(self):  
        print("Start: Query FLD?")                  
        if self.ser.isOpen():
            self.ser.write(('FLD?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            #while test != 'ON\r' or 'ON\r':
            #    self.QueryOUT()
            if test == 'ON\r':
                print('Answer: ' + test)
                GenData.SRFDE = True
            if test == 'OFF\r':
                print('Answer: ' + test)
                GenData.SRFDE = False
        else:
            print('Anser: No connection to Port.')
            
    def QueryDeviceData(self):
        print("Start: Query IDN?, REV?, SN? and DATE?")
        if self.ser.isOpen():
            self.ser.write(('IDN?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")  
            GenData.DeviceIDN = test
            self.ser.write(('REV?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")  
            GenData.DeviceREV = test            
            self.ser.write(('SN?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")  
            GenData.DeviceSN = test
            self.ser.write(('DATE?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")  
            GenData.DeviceDATE = test
        else:
            print('Anser: No connection to Port.')
               
    def QuerySTT(self):
        print("Start: Query STT?")
        if self.ser.isOpen():
            self.ser.write(('STT?\r').encode())
            test=self.ser.readline()
            test=test.decode("utf-8")
            print('Answer: ' + test)
            
            mv_in=test.find('MV(')
            mv_end=test.find('),PV')
            m_voltage=float(test[(mv_in+3):mv_end]) # Measured Voltage

            pv_in=test.find('PV(')
            pv_end=test.find('),MC')
            p_voltage=float(test[(pv_in+3):pv_end]) # Programmed Voltage

            mc_in=test.find('MC(')
            mc_end=test.find('),PC')
            m_current=float(test[(mc_in+3):mc_end]) # Measured Current

            pc_in=test.find('PC(')
            pc_end=test.find('),SR')
            p_current=float(test[(pc_in+3):pc_end]) # Measured Current
            
            sr_in=test.find('SR(')
            sr_end=test.find('),FR')
            status_reg=int(test[(sr_in+3):sr_end],16) # Status Register
            
            fr_in=test.find('FR(')
            fault_reg=int(test[(fr_in+3):(fr_in+5)],16) # Fault Register

            #Messages
            GenData.MV = m_voltage
            GenData.PV = p_voltage
            GenData.MC = m_current
            GenData.PC = p_current
            # Status register
            GenData.SRCV   = bool(status_reg & 0x01)
            GenData.SRCC   = bool(status_reg & 0x02)
            GenData.SRNFLT = bool(status_reg & 0x04)
            GenData.SRFLT  = bool(status_reg & 0x08)
            GenData.SRAST  = bool(status_reg & 0x10)
            GenData.SRFDE  = bool(status_reg & 0x20)
            GenData.SRLCL  = bool(status_reg & 0x80)
            # Fault Register
            GenData.FRAC   = bool(fault_reg & 0x02)
            GenData.FROTP  = bool(fault_reg & 0x04)
            GenData.FRFOLD = bool(fault_reg & 0x08)
            GenData.FROVP  = bool(fault_reg & 0x10)
            GenData.FRSO   = bool(fault_reg & 0x20)
            GenData.FROFF  = bool(fault_reg & 0x40)
            GenData.FRENA  = bool(fault_reg & 0x80)
        else:
            print('Anser: No connection to Port.')
        
    def QuerySetupGUI(self):
        print("Start: Setup GUI data acquisition.")
        self.QuerySTT()
        self.QueryOVP()
        self.QueryUVL()
        self.QueryOUT()
        self.QueryDeviceData()
        print("End: Setup GUI data acquisition.")
        
    def QueryRefreshGUI(self):
        print("Start: Refresh GUI data acquisition.")
        self.QuerySTT()
        self.QueryOUT()
        print("End: Refresh GUI data acquisition.")            
########################################################################


########################################################################
class myMainContent(QtGui.QWidget):
    
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        
        self.initUI()
        self.mySerial = ComSerial()
        
    def initUI(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refreshGUI)
        
        self.ComboBoxPort = QtGui.QComboBox()
        self.ComboBoxPort.setMaximumWidth(240)
        self.RefreshComboBoxPort()
        self.ButtonRefreshPort = QtGui.QPushButton("R")
        self.ButtonRefreshPort.clicked.connect(self.RefreshComboBoxPort)
        self.ButtonRefreshPort.setFixedWidth(50)
        self.ComboBoxAddress = QtGui.QComboBox()
        self.ComboBoxAddress.addItems(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        self.ComboBoxAddress.setCurrentIndex(6)
        self.ComboBoxAddress.setMaximumWidth(60)
        self.ComboBoxSpeed = QtGui.QComboBox()
        self.ComboBoxSpeed.addItems(["1200","2400","4800","9600","19200"])
        self.ComboBoxSpeed.setCurrentIndex(3)
        self.ComboBoxSpeed.setMaximumWidth(90)
        self.ButtonConnect = QtGui.QPushButton("Connect")
        self.ButtonConnect.setCheckable(True)
        self.ButtonConnect.setMaximumWidth(150)
        self.ButtonConnect.clicked.connect(self.onActivatedButtonConnect)  
        self.LabelDeviceIDN = QtGui.QLabel('IDN')        
        self.LabelDeviceREV = QtGui.QLabel('SW')  
        self.LabelDeviceSN = QtGui.QLabel('SN')  
        self.LabelDeviceDATE = QtGui.QLabel('DATE') 
                
        self.LineEditDeviceIDN = QtGui.QLineEdit()
        self.LineEditDeviceIDN.setReadOnly(True)
        self.LineEditDeviceREV = QtGui.QLineEdit()
        self.LineEditDeviceREV.setReadOnly(True)
        self.LineEditDeviceSN = QtGui.QLineEdit()
        self.LineEditDeviceSN.setReadOnly(True)
        self.LineEditDeviceDATE = QtGui.QLineEdit()
        self.LineEditDeviceDATE.setReadOnly(True)
        
        self.LabelFault = QtGui.QLabel('Fault Register')       
        self.CheckBoxACFail = MyQCheckBox("AC Fail")
        self.CheckBoxACFail.setModifiable(False)
        self.CheckBoxOTP = MyQCheckBox("OTP")
        self.CheckBoxOTP.setModifiable(False)
        self.CheckBoxFBD = MyQCheckBox("FBD")
        self.CheckBoxFBD.setModifiable(False)
        self.CheckBoxOVP = MyQCheckBox("OVP")
        self.CheckBoxOVP.setModifiable(False)
        self.CheckBoxOFF = MyQCheckBox("OFF")
        self.CheckBoxOFF.setModifiable(False)
        self.CheckBoxENA = MyQCheckBox("ENA")
        self.CheckBoxENA.setModifiable(False)
        self.CheckBoxSO  = MyQCheckBox("SO")
        self.CheckBoxSO.setModifiable(False)
                
        self.VoltageLCD = QtGui.QLCDNumber()
        self.VoltageLCD.setDigitCount(5)
        self.VoltageLCD.display(" 0.00")
        self.VoltageLCD.setMinimumHeight(50)
        self.VoltageLCD.setMinimumWidth(125)
        self.VoltageLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.VoltageLCD.setFrameStyle(QtGui.QFrame.NoFrame)
        self.LabelVoltageLCD= QtGui.QLabel('Voltage')
        self.SpinBoxSetVoltage = QtGui.QDoubleSpinBox()   
        self.SpinBoxSetVoltage.setMinimum(0.00)
        self.SpinBoxSetVoltage.setMaximum(50.00)
        self.SpinBoxSetVoltage.setSuffix(" V")
        self.SpinBoxSetVoltage.valueChanged.connect(self.onChangedSpinBoxSetVoltage)
        self.ButtonSetVoltage = QtGui.QPushButton("-")
        self.ButtonSetVoltage.setMaximumWidth(70)
        self.ButtonSetVoltage.clicked.connect(self.onActivatedButtonSetVoltage)  
        self.ButtonSetVoltage.setEnabled(False)

        self.CurrentLCD = QtGui.QLCDNumber()
        self.CurrentLCD.setDigitCount(5)
        self.CurrentLCD.display(" 0.00")
        self.CurrentLCD.setMinimumHeight(50) 
        self.CurrentLCD.setMinimumWidth(125)
        self.CurrentLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.CurrentLCD.setFrameStyle(QtGui.QFrame.NoFrame)
        self.LabelCurrentLCD = QtGui.QLabel('Current')
        self.SpinBoxSetCurrent = QtGui.QDoubleSpinBox()  
        self.SpinBoxSetCurrent.setMinimum(0.00)
        self.SpinBoxSetCurrent.setMaximum(30.00)
        self.SpinBoxSetCurrent.setSuffix(" A")
        self.SpinBoxSetCurrent.valueChanged.connect(self.onChangedSpinBoxSetCurrent)
        self.ButtonSetCurrent = QtGui.QPushButton("-")
        self.ButtonSetCurrent.setMaximumWidth(70)
        self.ButtonSetCurrent.clicked.connect(self.onActivatedButtonSetCurrent)  
        self.ButtonSetCurrent.setEnabled(False)
        
        self.PowerLCD = QtGui.QLCDNumber()
        self.PowerLCD.setDigitCount(6)
        self.PowerLCD.display("   0.0")
        self.PowerLCD.setMinimumHeight(50) 
        self.PowerLCD.setMinimumWidth(150)
        self.PowerLCD.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.PowerLCD.setFrameStyle(QtGui.QFrame.NoFrame)    
        self.LabelPowerLCD = QtGui.QLabel('Power')
        self.ButtonSwitchOUT = QtGui.QPushButton("OFF")
        self.ButtonSwitchOUT.setCheckable(True)
        self.ButtonSwitchOUT.clicked.connect(self.onActivatedButtonSwitchOUT)  
   
        self.LabelSetOVP = QtGui.QLabel('OVP')         
        self.SpinBoxSetOVP = QtGui.QDoubleSpinBox()  
        self.SpinBoxSetOVP.setMinimum(5.00)
        self.SpinBoxSetOVP.setMaximum(57.00)
        self.SpinBoxSetOVP.setSuffix(" V")
        self.SpinBoxSetOVP.valueChanged.connect(self.onChangedSpinBoxSetOVP)
        self.ButtonSetOVP = QtGui.QPushButton("-")
        self.ButtonSetOVP.setMinimumWidth(70)
        self.ButtonSetOVP.clicked.connect(self.onActivatedButtonSetOVP)
        self.ButtonSetOVP.setEnabled(False)
        #self.ButtonSetOVP.setMaximumWidth(40)

        self.LabelSetUVL = QtGui.QLabel('UVL')         
        self.SpinBoxSetUVL = QtGui.QDoubleSpinBox()  
        self.SpinBoxSetUVL.setMinimum(0.00)
        self.SpinBoxSetUVL.setMaximum(47.50)
        self.SpinBoxSetUVL.setSuffix(" V")
        self.SpinBoxSetUVL.valueChanged.connect(self.onChangedSpinBoxSetUVL)
        self.ButtonSetUVL = QtGui.QPushButton("-")
        self.ButtonSetUVL.setMinimumWidth(70)
        self.ButtonSetUVL.clicked.connect(self.onActivatedButtonSetUVL)
        self.ButtonSetUVL.setEnabled(False)
        #self.ButtonSetUVL.setMaximumWidth(40)
   
        self.LabelSetFBD = QtGui.QLabel('FBD')         
        self.SpinBoxSetFBD = QtGui.QSpinBox()  
        self.SpinBoxSetFBD.setMinimum(0)
        self.SpinBoxSetFBD.setMaximum(255)
        #self.SpinBoxSetFBD.setSuffix(" s")
        self.SpinBoxSetFBD.valueChanged.connect(self.onChangedSpinBoxSetFBD)
        self.ButtonSetFBD = QtGui.QPushButton("-")
        self.ButtonSetFBD.setMinimumWidth(70)
        self.ButtonSetFBD.setEnabled(False)
        self.ButtonSwitchFBD = QtGui.QPushButton("OFF")
        self.ButtonSwitchFBD.setCheckable(True)
        self.ButtonSwitchFBD.clicked.connect(self.onActivatedButtonSwitchFBD)
        self.ButtonSwitchFBD.setMinimumWidth(70)

        #self.ButtonSwitchFBD.setMaximumWidth(40)    
        
       
        
        self.LabelTitel = QtGui.QLabel('TDK LAMBDA GENESYS')
        font = QtGui.QFont()
        font.setFamily('Arial')
        font.setFixedPitch(True)
        font.setPointSize(15)
        self.LabelTitel.setFont(font)
        #self.LabelTitel.setAlignment(QtCore.Qt.AlignVCenter)
        
        LayoutVoltage = QtGui.QGridLayout()
        #LayoutVoltage.addWidget(self.LabelVoltageLCD,   0, 0)
        LayoutVoltage.addWidget(self.VoltageLCD,        1, 0, 1, 2)
        LayoutVoltage.addWidget(self.SpinBoxSetVoltage, 2, 0)
        LayoutVoltage.addWidget(self.ButtonSetVoltage,  2, 1)
        
        GroupBoxVoltage = QtGui.QGroupBox("Voltage")
        GroupBoxVoltage.setLayout(LayoutVoltage)
        GroupBoxVoltage.setMinimumWidth(220)
        
        LayoutCurrent = QtGui.QGridLayout()
        #LayoutCurrent.addWidget(self.LabelCurrentLCD,   0, 0)
        LayoutCurrent.addWidget(self.CurrentLCD,        1, 0, 1, 2)
        LayoutCurrent.addWidget(self.SpinBoxSetCurrent, 2, 0)
        LayoutCurrent.addWidget(self.ButtonSetCurrent,  2, 1)

        GroupBoxCurrent = QtGui.QGroupBox("Current")
        GroupBoxCurrent.setLayout(LayoutCurrent) 
        GroupBoxCurrent.setMinimumWidth(220)

        LayoutPower = QtGui.QGridLayout()
        #LayoutPower.addWidget(self.LabelPowerLCD,   0, 0)
        LayoutPower.addWidget(self.PowerLCD,        1, 0)
        LayoutPower.addWidget(self.ButtonSwitchOUT, 2, 0)   
        
        GroupBoxPower = QtGui.QGroupBox("Power")
        GroupBoxPower.setLayout(LayoutPower) 
        GroupBoxPower.setMinimumWidth(220)        

        LayoutPort = QtGui.QHBoxLayout()
        LayoutPort.addWidget(self.ComboBoxPort)
        LayoutPort.addWidget(self.ButtonRefreshPort)
        LayoutPort.addWidget(self.ComboBoxSpeed)
        LayoutPort.addWidget(self.ComboBoxAddress)
        LayoutPort.addWidget(self.ButtonConnect)

        GroupBoxPort = QtGui.QGroupBox("Connection")
        GroupBoxPort.setLayout(LayoutPort)
        
        LayoutDevice = QtGui.QGridLayout() 
        LayoutDevice.addWidget(self.LabelDeviceIDN,     0, 0)
        LayoutDevice.addWidget(self.LabelDeviceREV,     1, 0)
        LayoutDevice.addWidget(self.LabelDeviceSN,      2, 0)
        LayoutDevice.addWidget(self.LabelDeviceDATE,    3, 0)
        LayoutDevice.addWidget(self.LineEditDeviceIDN,  0, 1)
        LayoutDevice.addWidget(self.LineEditDeviceREV,  1, 1)
        LayoutDevice.addWidget(self.LineEditDeviceSN,   2, 1)
        LayoutDevice.addWidget(self.LineEditDeviceDATE, 3, 1)

        GroupBoxDevice = QtGui.QGroupBox("Device")
        GroupBoxDevice.setLayout(LayoutDevice)
        
        LayoutFault = QtGui.QGridLayout()
        #LayoutFault.addWidget(self.LabelFault,     0, 0)
        LayoutFault.addWidget(self.CheckBoxACFail, 1, 0)
        LayoutFault.addWidget(self.CheckBoxOTP,    2, 0)
        LayoutFault.addWidget(self.CheckBoxOVP,    3, 0)
        LayoutFault.addWidget(self.CheckBoxFBD,    1, 1)
        LayoutFault.addWidget(self.CheckBoxOFF,    2, 1)
        LayoutFault.addWidget(self.CheckBoxENA,    3, 1)
        LayoutFault.addWidget(self.CheckBoxSO,     4, 1)
        
        GroupBoxFault = QtGui.QGroupBox("Fault")
        GroupBoxFault.setLayout(LayoutFault)
        
        LayoutProtection = QtGui.QGridLayout()
        LayoutProtection.addWidget(self.LabelSetOVP,     0, 1)
        LayoutProtection.addWidget(self.SpinBoxSetOVP,   0, 2)
        LayoutProtection.addWidget(self.ButtonSetOVP,    0, 3)
        LayoutProtection.addWidget(self.LabelSetUVL,     1, 1)
        LayoutProtection.addWidget(self.SpinBoxSetUVL,   1, 2)
        LayoutProtection.addWidget(self.ButtonSetUVL,    1, 3)
        LayoutProtection.addWidget(self.LabelSetFBD,     2, 1)
        LayoutProtection.addWidget(self.SpinBoxSetFBD,   2, 2)
        #LayoutProtection.addWidget(self.ButtonSetFBD,    2, 3)
        LayoutProtection.addWidget(self.ButtonSwitchFBD, 2, 3)    

        GroupBoxProtection = QtGui.QGroupBox("Protection")
        GroupBoxProtection.setLayout(LayoutProtection)
        
        
#        self.plotX  = np.arange(101)
#        self.plotY1 = np.empty(101)
#        self.plotY2 = np.empty(101)
#
#        pg.mkQApp()
#        pg.setConfigOption('background', '#00000000')
#        pg.setConfigOption('foreground', '#000000FF')
#        pg.setConfigOptions(antialias=True)
#        
#        pw = pg.PlotWidget()
#        pw.show()
#        
#        self.p1 = pw.plotItem
#        self.p1.setXRange(0,100)
#        self.p1.setYRange(0,50)
#        #self.p1.setWindowTitle('Current-Voltage')
#        self.p1.setLabel('bottom', 'time', units='s')
#        self.p1.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=1))
#        self.p1.setLabel('left', 'Voltage', units='V', color='#025b94')
#        self.p1.getAxis('left').setPen(pg.mkPen(color='#025b94', width=1))
#        self.curve1 = self.p1.plot(x=[], y=[], pen=pg.mkPen(color='#025b94'))
#        self.p1.showAxis('right')
#        self.p1.setLabel('right', 'Current', units="A", color='#c4380d')
#        self.p1.getAxis('right').setPen(pg.mkPen(color='#c4380d', width=1))
#
#        self.p2 = pg.ViewBox()
#        self.p1.scene().addItem(self.p2)
#        self.p1.getAxis('right').linkToView(self.p2)
#        self.p2.setXLink(self.p1)
#        self.p2.setYRange(0,30)
#
#        self.curve2 = pg.PlotCurveItem(pen=pg.mkPen(color='#c4380d', width=1))
#        self.p2.addItem(self.curve2)
#        
#        self.updateViews()
#        self.p1.getViewBox().sigResized.connect(self.updateViews)
#        
#        
#        LayoutPlot = QtGui.QVBoxLayout()
#        LayoutPlot.addWidget(pw)
#        GroupBoxPlot = QtGui.QGroupBox("Plot")
#        GroupBoxPlot.setLayout(LayoutPlot)        
        
        LayoutMain = QtGui.QGridLayout(self)
        #LayoutMain.setColumnMinimumWidth(1,5)
        #LayoutMain.setColumnMinimumWidth(3,5)
        #LayoutMain.setRowMinimumHeight(3,5)
#        LayoutMain.setRowMinimumHeight(5,250)
        #LayoutMain.setColumnStretch(1,1)
        #LayoutMain.setColumnStretch(0,1)
        
        LayoutMain.addWidget(self.LabelTitel,    0, 0, 1, 3, alignment = QtCore.Qt.AlignCenter)     
        LayoutMain.addWidget(GroupBoxPort,       1, 0, 1, 3)  
        LayoutMain.addWidget(GroupBoxDevice,     2, 0) 
        LayoutMain.addWidget(GroupBoxFault,      2, 1) 
        LayoutMain.addWidget(GroupBoxProtection, 2, 2)
        LayoutMain.addWidget(GroupBoxVoltage,    3, 0)
        LayoutMain.addWidget(GroupBoxPower,      3, 1)
        LayoutMain.addWidget(GroupBoxCurrent,    3, 2)
#        LayoutMain.addWidget(GroupBoxPlot,       4, 0, 1, 3)
                



#    def updateViews(self):
#            self.p2.setGeometry(self.p1.getViewBox().sceneBoundingRect())
#            self.p2.linkedViewChanged(self.p1.getViewBox(), self.p2.XAxis)
#        
#    def updatePlot(self):
#        self.plotY1 = np.roll(self.plotY1, 1)
#        self.plotY1[0] = GenData.MV
#        self.plotY2 = np.roll(self.plotY2, 1)
#        self.plotY2[0] = GenData.MC
#        self.curve1.setData(self.plotX,self.plotY1)
#        self.curve2.setData(self.plotX,self.plotY2)        


    def initalSetupGUI(self):
        self.mySerial.QuerySetupGUI()         
        self.SpinBoxSetOVP.setValue(GenData.POVP)
        self.SpinBoxSetUVL.setValue(GenData.PUVL)
        self.SpinBoxSetVoltage.setValue(GenData.PV)
        self.SpinBoxSetCurrent.setValue(GenData.PC)     
        self.LineEditDeviceIDN.setText(GenData.DeviceIDN)
        self.LineEditDeviceSN.setText(GenData.DeviceSN)
        self.LineEditDeviceREV.setText(GenData.DeviceREV)
        self.LineEditDeviceDATE.setText(GenData.DeviceDATE)
        self.setSwitchFBDstate()
        self.setSwitchOUTstate()

    def refreshGUI(self):
        self.mySerial.QueryRefreshGUI()
        self.VoltageLCD.display('{:5.2f}'.format(GenData.MV))
        self.CurrentLCD.display('{:5.2f}'.format(GenData.MC))
        self.PowerLCD.display('{:6.1f}'.format(GenData.MP))
        self.CheckBoxACFail.setChecked(GenData.FRAC)
        self.CheckBoxOTP.setChecked(GenData.FROTP)
        self.CheckBoxOVP.setChecked(GenData.FROVP)
        self.CheckBoxFBD.setChecked(GenData.FRFOLD)
        self.CheckBoxOFF.setChecked(GenData.FROFF)
        self.CheckBoxENA.setChecked(GenData.FRENA)
        self.CheckBoxSO.setChecked(GenData.FRSO)
        self.setLCDcolor()
        self.setSwitchOUTstate()
        
        self.SpinBoxSetOVP.setMinimum(GenData.minPOVP)
        self.SpinBoxSetUVL.setMaximum(GenData.maxPUVL)
        self.SpinBoxSetVoltage.setMinimum(GenData.minPV)
        self.SpinBoxSetVoltage.setMaximum(GenData.maxPV)    
#        self.updatePlot()             
        
    def setSwitchFBDstate(self):        
        if GenData.SRFDE == True:
            self.ButtonSwitchFBD.setText("ON")
            self.ButtonSwitchFBD.setChecked(True)
        else:
            self.ButtonSwitchFBD.setText("OFF") 
            self.ButtonSwitchFBD.setChecked(False)
 
    def setSwitchOUTstate(self):           
        if GenData.OUTPUT == True:
            self.ButtonSwitchOUT.setText("ON")
            self.ButtonSwitchOUT.setChecked(True)
        else:
            self.ButtonSwitchOUT.setText("OFF") 
            self.ButtonSwitchOUT.setChecked(False)
          
    def setLCDcolor(self):
        if GenData.SRCC == True:
            self.CurrentLCD.setStyleSheet("QWidget {background-color: %s}" % "#00FF00")
        else:
            self.CurrentLCD.setStyleSheet("QWidget {background-color: %s}" % "transparent")
        if GenData.SRCV == True:
            self.VoltageLCD.setStyleSheet("QWidget {background-color: %s}" % "#00FF00")
        else:
            self.VoltageLCD.setStyleSheet("QWidget {background-color: %s}" % "transparent")
   
            
    def onActivatedButtonConnect(self):
        if self.ButtonConnect.isChecked():
            print("Start connection to Port.")
            self.mySerial.SetComPort(self.ComboBoxPort.currentText())
            self.mySerial.SetComSpeed(self.ComboBoxSpeed.currentText())
            self.mySerial.ConnectPort()
            print("Start connection to Device.")
            self.mySerial.SetComAddress(self.ComboBoxAddress.currentText())
            if self.mySerial.ConnectDevice() == True:
                self.ComboBoxPort.setEnabled(False)
                self.ButtonRefreshPort.setEnabled(False)
                self.ComboBoxSpeed.setEnabled(False)
                self.ComboBoxAddress.setEnabled(False)
                self.ButtonConnect.setText("Disconnect")
                self.parent().statusBar().showMessage("Device connected", 2000)
                print("Load configuration data.")
                self.initalSetupGUI()
                print("Start: Refresh timer.")
                self.timer.start(500)
            else:
                self.showdialogErrorConnectionDevice()
                self.ButtonConnect.setChecked(False)
        else:
            print("Close connection to Port.")
            self.mySerial.DisconnectPort()
            self.ComboBoxPort.setEnabled(True)
            self.ButtonRefreshPort.setEnabled(True)
            self.ComboBoxSpeed.setEnabled(True)
            self.ComboBoxAddress.setEnabled(True)
            self.ButtonConnect.setText("Connect") 
            self.parent().statusBar().showMessage("Device disconnected", 2000)
            print("Stop: Refresh timer.")
            self.timer.stop()
                
        
    def onChangedSpinBoxSetOVP(self):
        if self.SpinBoxSetOVP.value() != GenData.POVP:
            self.ButtonSetOVP.setText("SET")
            self.ButtonSetOVP.setEnabled(True)
        else:
            self.ButtonSetOVP.setText("-")
            self.ButtonSetOVP.setEnabled(False)
            
    def onChangedSpinBoxSetUVL(self):
        if self.SpinBoxSetUVL.value() != GenData.PUVL:
            self.ButtonSetUVL.setText("SET")
            self.ButtonSetUVL.setEnabled(True)
        else:
            self.ButtonSetUVL.setText("-")
            self.ButtonSetUVL.setEnabled(False)

    def onChangedSpinBoxSetFBD(self):
        print("FBD Spinbox changed...")
#        if self.SpinBoxSetFBD.value() != GenData.FBDValue:
#            self.ButtonSetFBD.setText("SET")
#            self.ButtonSetFBD.setEnabled(True)
            
    def onChangedSpinBoxSetVoltage(self):
        if self.SpinBoxSetVoltage.value() != GenData.PV:
            self.ButtonSetVoltage.setText("SET")
            self.ButtonSetVoltage.setEnabled(True)
        else:
            self.ButtonSetVoltage.setText("-")
            self.ButtonSetVoltage.setEnabled(False)            
            
    def onChangedSpinBoxSetCurrent(self):
        if self.SpinBoxSetCurrent.value() != GenData.PC:
            self.ButtonSetCurrent.setText("SET")
            self.ButtonSetCurrent.setEnabled(True)
        else:
            self.ButtonSetCurrent.setText("-")
            self.ButtonSetCurrent.setEnabled(False) 
            
    def onActivatedButtonSetOVP(self):
        print("Send new OVP value.")
        if self.mySerial.SetOVP(self.SpinBoxSetOVP.value()) == True:
            self.ButtonSetOVP.setText("-")
            self.ButtonSetOVP.setEnabled(False)
        
    def onActivatedButtonSetUVL(self):
        print("Send new UVL value.")
        if self.mySerial.SetUVL(self.SpinBoxSetUVL.value()) == True:
            self.ButtonSetUVL.setText("-")
            self.ButtonSetUVL.setEnabled(False)    
        
    def onActivatedButtonSetVoltage(self):
        print("Send new voltage value.")
        if self.mySerial.SetVoltage(self.SpinBoxSetVoltage.value()) == True:
            self.ButtonSetVoltage.setText("-")
            self.ButtonSetVoltage.setEnabled(False) 
        
    def onActivatedButtonSetCurrent(self):
        print("Send new current value.")
        if self.mySerial.SetCurrent(self.SpinBoxSetCurrent.value()) == True:
            self.ButtonSetCurrent.setText("-")
            self.ButtonSetCurrent.setEnabled(False) 

    def onActivatedButtonSwitchFBD(self):
        if self.ButtonSwitchFBD.isChecked():
            if self.mySerial.SetFLDON() == True:    
                self.ButtonSwitchFBD.setText("ON")
                self.ButtonSwitchFBD.setChecked(True)
                self.parent().statusBar().showMessage("Foldback ON", 2000)
            else:
                self.ButtonSwitchFBD.setChecked(False)
        else:
            if self.mySerial.SetFLDOFF() == True:
                self.ButtonSwitchFBD.setText("OFF") 
                self.ButtonSwitchFBD.setChecked(False)
                self.parent().statusBar().showMessage("Foldback OFF", 2000)
            else:
                self.ButtonSwitchFBD.setChecked(True)    
                
    def onActivatedButtonSwitchOUT(self):
        if self.ButtonSwitchOUT.isChecked():
            if self.mySerial.SetOutputON() == True:
                self.ButtonSwitchOUT.setText("ON")
                self.ButtonSwitchOUT.setChecked(True)
                self.parent().statusBar().showMessage("Output ON", 2000)
            else:
                self.ButtonSwitchOUT.setChecked(False)
        else:
            if self.mySerial.SetOutputOFF() == True:
                self.ButtonSwitchOUT.setText("OFF") 
                self.ButtonSwitchOUT.setChecked(False)
                self.parent().statusBar().showMessage("Output OFF", 2000)
            else:
                self.ButtonSwitchOUT.setChecked(True)
                
    def RefreshComboBoxPort(self):
        ports = serialPorts()
        self.ComboBoxPort.clear()
        for port in ports:
            self.ComboBoxPort.addItem(port)  
   
    def showdialogErrorConnectionDevice(self):
        #msg = QtGui.QMessageBox()
        #msg.setIcon(QtGui.QMessageBox.Critical)
        #msg.setWindowTitle("Error")
        #msg.setText("No answer form Device.\nCheck connection and address.")
        #msg.setStandardButtons(QtGui.QMessageBox.Ok)
        #retval = msg.exec_()
        QtGui.QMessageBox.critical(self, 'Error',
            "No answer form Device.\nCheck connection and address.", QtGui.QMessageBox.Ok)
########################################################################



########################################################################

class myMainWindow(QtGui.QMainWindow):                                  
    def __init__(self):
        super(myMainWindow, self).__init__()
        self.initUI()

    def initUI(self):               
        #if sys.platform=="darwin":
        #    QtGui.qt_mac_set_native_menubar(False)
            
        exitAction = QtGui.QAction(QtGui.QIcon('pics/exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit/Terminate application')
        exitAction.triggered.connect(self.close)
        
        aboutAction = QtGui.QAction(QtGui.QIcon('pics/about.png'), '&About', self)
        aboutAction.setStatusTip('About application')
        aboutAction.triggered.connect(self.aboutBox)

        self.statusBar()

        menubar = self.menuBar()   
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        
        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(aboutAction)
        

        
        # create the widget here
        content = myMainContent(self)
        self.setCentralWidget(content)

        #self.setGeometry(500, 180, 400, 400)   
        self.move(200, 10)
        self.setWindowTitle('Genesys Project')
        
        
    def aboutBox(self):
        QtGui.QMessageBox.information(self, 'About Genesys Project',
            "Genesys Project by flyglas\nVersion: 0.6b", QtGui.QMessageBox.Ok)
        
    def closeEvent(self, event):
        print("event")
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()         

        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = myMainWindow()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    
    
