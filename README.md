# domoticz-fronius-inverter-plugin
Domoticz Fronius Inverter plugin
--------------------------------

This plugin is running without issues since 2 feb 2018 (Domoticz 3.8799).  
As of june 2020 it is still running on Domoticz beta 12119.  
It's not feature complete yet, but it's working.  
As the original author does not maintain it anymore, i will give it a try.

It creates 3 devices on the Utility page.    
One custom meter showing only the current generated Watts.  
The second is a kWh type meter with the current generated Watts and the yeartotal.  
The third is a kWh type meter with the current generated Watts and the daytotal.  

The Fronius API only returns the generated kWhs as an integer.
To make the graphs more fluent the plugin calculates the fractions by using the current Watts generated,
until the intverter return one kWh more. Then the fraction part is reset and starts calculating again.  
The option to turn this calculation off has been added, but not tested yet.

Comparing the Fronius phone app with this plugin, there is a small difference. Acceptable for now.

- Fronius app - Dommoticz plugin (kWh generated per day)
- 10.4 - 10.692
- 8.62 - 8.431
- 5.72 - 5.859

Installation
------------

In your `domoticz/plugins` directory do  

```bash
git clone https://github.com/robhiddinga/domoticz-fronius-inverter-plugin.git
```
To update in your `domoticz-fronius-inverter-plugin` directory do  
```bash
git pull
```

Restart your Domoticz service with:

```bash
sudo service domoticz.sh restart
```

Now go to **Setup**, **Hardware** in Domoticz. There you add
**Fronius Inverter**.

Fill in the IP address and device ID of your inverter.
The device ID is usually 1.

Choose if you want to use the fraction calculations.
Default Yes. No not supported yet

Currently the plugin only supports Fronius API version V1

Features to add
---------------

- Improved debug options.
- Some things I can't come up with right now, let me know what you want!


This plugin uses an icon by 
<a href="https://www.flaticon.com/authors/vectors-market" title="Vectors Market">
Vectors Market</a> from 
<a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
and is licensed by 
<a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">
CC 3.0 BY</a>
