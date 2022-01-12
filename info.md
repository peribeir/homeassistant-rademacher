![logo](https://github.com/peribeir/homeassistant-rademacher/raw/master/img/logo.png)
A Home Assistant custom Integration for local handling of Devices connected to Rademacher bridge.

Works exclusively when devices are connected through HomePilot or Start2Smart Bridge.

### ***\*New\** Covers, Switches and Sensors now supported.**

**See full device list support at the end.**

# Installation
Copy the `rademacher` folder into yout Home Assistant's `custom_components` folder.
This should be located under the `/config` folder.

If you haven't done it already, you should create the `custom_components` folder on your `/config`.

# Usage

First of all, you should add the devices in you Home Pilot Application, or in the Bridge's Interface. The integration works by fetching the list that is registered in the Hub. 

## 1. Automatic Discovery

When Home Assistant Core is running on the same sub-network as the Hub,
if auto-discovery works, you'll see a notification on HA GUI stating it found new devices.

Just click "Check it Out" and you'll be presented with the Integrations page where you should see the new Rademacher Bridge entry.

Click "Configure". If you have set a password for the Hub, enter it and press "Submit", or just "Submit" if you have no password.

You should now be presented with Device/Entities detected, you should select the HA Area where you want to add them.

## 2. Using Config Flow

If Hub has not been auto-discovered, or you just deleted the integration and want to add again:

Start by going to Configuration > Integrations, then press the "Add Integration" button.

Then, search for Rademacher and select it.

In the Dialog that appears, insert the HostName/IP Address of the Rademacher Bridge. Ex: `bridge.local` or `192.168.1.60`

Press "Submit".

You should now be presented with Device/Entities detected, you should select the HA Area where you want to add them.

# Supported Devices

The integration should work with the following devices (tested devices are marked with in **bold** )

## Covers
- **DuoFern tubular motor actuator (DN:35000662)**
  - Tested on 9471 DuoFern Blinds Actuator
- DuoFern tubular motor control B50/B55 (DN:31500162)
- RolloTron Comfort DuoFern (DN:16234511_A)
- RolloTron radio beltwinder 60 kg (DN:14236011)
- **RolloTron radio beltwinder (DN:14234511)**
  - Tested on RolloTron Basis DuoFern 1200-UW Beltwinder
- **DuoFern tubular motor actuator environmental sensor (DN:32000064_A)**
  - Tested on DuoFern Environmental Sensor Weather Station 9475
- DuoFern tubular motor actuator (DN:35140662)
- RolloTube S-line DuoFern (DN:23602075)
- RolloTube S-line Zip DuoFern (DN:25782075)

## Sensors
- Sun sensor Troll Comfort DuoFern (DN:36500572_S)
- Temperature sensor DuoFern Radiator Actuator (DN:35003064_S)
- Temperature sensor DuoFern Room thermostat (DN:32501812_S)
- Sun sensor RolloTron Comfort DuoFern (DN:16234511_S)
- **Sensor DuoFern Environmental sensor (DN:32000064_S)**
  - Tested on DuoFern Environmental Sensor Weather Station 9475

## Switches
- DuoFern Switch actuator (DN:35001164)
- **DuoFern Universal actuator 2-channel (DN:35000262)**
  - Tested on 9470 Universal Actuator