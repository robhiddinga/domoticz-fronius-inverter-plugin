#           Fronius Inverter Plugin
#
#           Author:     RobH 2020. Based on ADJ 2018 version
#
"""
<plugin key="froniusInverter" name="Fronius Inverter" author="RobH" version="0.1.0" wikilink="https://github.com/robhiddinga/domoticz-fronius-inverter-plugin.git" externallink="http://www.fronius.com">
    <params>
        <param field="Mode1" label="IP Address" required="true" width="200px" />
        <param field="Mode2" label="Device ID" required="true" value="1" width="100px" />
        <param field="Mode5" label="Fraction" width="100px">
            <options>
                <option label="True"  value="Yes" default="true" />
                <option label="False" value="No"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True"    value="Debug"/>
                <option label="False"   value="Normal" default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import sys
import json
import datetime
import urllib.request
import urllib.error

class BasePlugin:
    inverterWorking     = True
    intervalCounter     = None
    heartbeat           = 30
    todayWh             = 0
    totalWh             = 0
    currentWatts        = 0
    previousTotalWh     = 0
    previousTodayWh     = 0
    previousCurrentWatt = 0
    whFraction          = 0
    calcTotalWh         = 0
    calcTodayWh         = 0

    def onStart(self):
        if Parameters["Mode6"] != "Normal":
            Domoticz.Debugging(1)

        if (len(Devices) == 0):
            Domoticz.Device(Name="Current power",  Unit=1, TypeName="Custom", Options = { "Custom" : "1;Watt"}, Used=1).Create()
            Domoticz.Device(Name="Total power",    Unit=2, TypeName="kWh", Used=1).Create()
            Domoticz.Device(Name="Today power",    Unit=3, TypeName="kWh", Used=1).Create()

            logDebugMessage("Devices created.")

        Domoticz.Heartbeat(self.heartbeat)
        self.intervalCounter = 0

        if ('FroniusInverter' not in Images): Domoticz.Image('Fronius Inverter Icons.zip').Create()
        if ('FroniusInverterOff' not in Images): Domoticz.Image('Fronius Inverter Off Icons.zip').Create()

        Devices[1].Update(0, sValue=str(Devices[1].sValue), Image=Images["FroniusInverter"].ID)
        Devices[2].Update(0, sValue=str(Devices[2].sValue), Image=Images["FroniusInverter"].ID)
        Devices[3].Update(0, sValue=str(Devices[3].sValue), Image=Images["FroniusInverter"].ID)
        return True


    def onHeartbeat(self):

        if self.intervalCounter == 1:

            ipAddress      = Parameters["Mode1"]
            deviceId       = Parameters["Mode2"]
            DataCollection = "CommonInverterData"
            jsonObject = self.getInverterRealtimeData( ipAddress, deviceId, DataCollection)
            logDebugMessage(str(jsonObject))
            status = self.isInverterActive(jsonObject)
            logDebugMessage("Status = " + str(status))

            self.getCommonInverterData(status, jsonObject)

            if (status != "Off"):

                if (Parameters["Mode5"] == "Yes"):
                  self.doFractionCalculations()

                self.updateDeviceCurrent()
                self.updateDeviceDayMeter()
                self.updateDeviceYearMeter()

                if (self.inverterWorking == False):
                    self.inverterWorking = True

            else:
                self.logErrorCode(jsonObject)

                if (self.inverterWorking == True):
                    self.inverterWorking = False
                    self.updateDeviceOff()


            self.intervalCounter = 0

        else:
            self.intervalCounter = 1
            logDebugMessage("Do nothing: " + str(self.intervalCounter))


        return True


    def getInverterRealtimeData(self, ipAddress, deviceId, DataCollection):

        protocol = "http"
        port     = "80"
        url = protocol + "://" + ipAddress + ":" + port + "/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceID=" + deviceId + "&DataCollection=" + DataCollection
        logDebugMessage('Retrieve solar data from ' + url)

        try:
            req = urllib.request.Request(url)
            jsonData = urllib.request.urlopen(req).read()
            jsonObject = json.loads(jsonData.decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logDebugMessage("Error: " + str(e) + " URL: " + url)
            return

        logDebugMessage("JSON: " + str(jsonData))

        return jsonObject

    def isInverterActive (self, jsonObject):

        # Check whether inverter is online and producing

        logDebugMessage("JSON " + str(jsonObject))
        if str(jsonObject) == "None":
            logDebugMessage("No data from inverter")
            return "Off"
        else:
            logDebugMessage("Data from inverter ")
            s = str(jsonObject)
            if s.find('PAC') > 0:
              logDebugMessage("Data from inverter " + s)
              return "Active"
            else:
              logDebugMessage("Inverter no production, but active")
              return "Online"

    def getCommonInverterData(self, status, jsonObject):

        if (status != "Off"):
           # Get the header data  when active or online
           self.todayWh = jsonObject["Body"]["Data"]["DAY_ENERGY"]["Value"]
           self.totalWh = jsonObject["Body"]["Data"]["TOTAL_ENERGY"]["Value"]

        if (status == "Active"):
           # Get the production data
           self.currentWatts = jsonObject["Body"]["Data"]["PAC"]["Value"]
        else:
           self.currentWatts = 0

        if (status == "Off"):
           # Use saved header data
           self.todayWh = self.previousTodayWh
           self.totalWh = self.previousTotalWh

    def doFractionCalculations(self):

        #today
        if (self.previousTodayWh < self.todayWh):
            logDebugMessage("New today recieved: prev:" + str(self.previousTodayWh) + " - new:" + str(self.todayWh) + " - last fraction: " + str(self.whFraction))
            self.whFraction = 0
            self.previousTodayWh = self.todayWh

        else:

            averageWatts =  (self.previousCurrentWatt + self.currentWatts) / 2
            self.whFraction = self.whFraction + int(round(averageWatts / 60))
            logDebugMessage("Fraction calculated: " + str(self.currentWatts) + " - " + str(self.whFraction))

        self.calcTodayWh = self.todayWh + self.whFraction
        logDebugMessage("Today calculated: " + str(self.calcTodayWh))

        #year
        if (self.previousTotalWh < self.totalWh):
            logDebugMessage("New total recieved: prev:" + str(self.previousTotalWh) + " - new:" + str(self.totalWh) + " - last fraction: " + str(self.whFraction))
            self.whFraction = 0
            self.previousTotalWh = self.totalWh

        else:

            averageWatts =  (self.previousCurrentWatt + self.currentWatts) / 2
            self.whFraction = self.whFraction + int(round(averageWatts / 60))
            logDebugMessage("Fraction calculated: " + str(self.currentWatts) + " - " + str(self.whFraction))

        self.calcTotalWh = self.totalWh + self.whFraction
        logDebugMessage("Total calculated: " + str(self.calcTotalWh))

        return

    def logErrorCode(self, jsonObject):

        if str(jsonObject) == "None":
           code = 0
           reason = " Inverter is offline"

        else:

         code   = jsonObject["Head"]["Status"]["Code"]
         reason = jsonObject["Head"]["Status"]["Reason"]
         if (code == 0):
            reason = 'Inverter is active, but no production'

        if (code != 12):
            logErrorMessage("Code: " + str(code) + ", reason: " + reason)

        return


    def updateDeviceCurrent(self):
        # Device 1 - current today

        self.previousCurrentWatt = self.currentWatts
        logDebugMessage("Current Watts " + str(self.currentWatts))
        try:
         Devices[1].Update(self.currentWatts, str(self.currentWatts), Images["FroniusInverter"].ID)
        except KeyError as e:
         cause = e.args[0]
         logErrorMessage("Cause " + str(cause))

        return

    def updateDeviceDayMeter(self):
        # Device 3 - current today - total today

        self.previousTodayWh = self.todayWh

        try:
         Devices[3].Update(0, str(self.currentWatts) + ";" + str(self.calcTodayWh))
        except KeyError as e:
         cause = e.args[0]
         logErrorMessage("Cause " + str(cause))

        return

    def updateDeviceYearMeter(self):
        # Device 2 - total today - total year

        self.previousTotalWh = self.totalWh

        try:
         Devices[2].Update(0, str(self.todayWh) + ";" + str(self.calcTotalWh))
        except KeyError as e:
         cause = e.args[0]
         logErrorMessage("Cause " + str(cause))
         
        return


    def updateDeviceOff(self):

        Devices[1].Update(0, "0", Images["FroniusInverterOff"].ID)

        if Parameters["Mode5"] == "Yes":
         self.calcTodayWh = self.previousTodayWh + self.whFraction
         self.calcTotalWh = self.previousTotalWh + self.whFraction
        else:
         self.calcTodayWh = self.previousTodayWh
         self.calcTotalWh = self.previousTotalWh

        if  calcTotalWh > 0:
         Devices[2].Update(0, "0;" + str(calcTotalWh))

        if  calcTodayWh > 0:
         Devices[3].Update(0, "0;" + str(calcTodayWh))

    def onStop(self):
        logDebugMessage("onStop called")
        return True

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def logDebugMessage(message):
    if (Parameters["Mode6"] == "Debug"):
        now = datetime.datetime.now()
        f = open(Parameters["HomeFolder"] + "fronius-inverter-plugin.log", "a")
        f.write("DEBUG - " + now.isoformat() + " - " + message + "\r\n")
        f.close()
    Domoticz.Debug(message)

def logErrorMessage(message):
    if (Parameters["Mode6"] == "Debug"):
        now = datetime.datetime.now()
        f = open(Parameters["HomeFolder"] + "fronius-inverter-plugin.log", "a")
        f.write("ERROR - " + now.isoformat() + " - " + message + "\r\n")
        f.close()
    Domoticz.Error(message)
