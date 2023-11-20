[![release](https://img.shields.io/github/v/release/peribeir/homeassistant-rademacher)](https://github.com/peribeir/homeassistant-rademacher/releases/latest)
[![downloads](https://img.shields.io/github/downloads/peribeir/homeassistant-rademacher/total)](https://github.com/peribeir/homeassistant-rademacher/releases/latest)
[![issues](https://img.shields.io/github/issues/peribeir/homeassistant-rademacher)](https://github.com/peribeir/homeassistant-rademacher/issues)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

![logo](https://github.com/peribeir/homeassistant-rademacher/raw/master/img/logo.png)
A Home Assistant custom Integration for local handling of Devices connected to Rademacher bridge.

# Hardware Support (now with BETA support for HP Gateway Premium)

Works exclusively when devices are connected through HomePilot or Start2Smart Bridge.

**Bridges/Gateways from Rademacher are fully supported.**

***Version 2.x added BETA support for the new Homepilot Gateway Premium. Needs further testing.***

***HP Gateway Premium with local password protection not supported yet.***

### **Supports Covers, Switches, Sensors, Dimmers and Thermostats.**

*See full device list support at the end.*

# Installation

## 1. Using HACS (now on default repositories)

> HACS is a community store for integrations, Frontend extensions, etc. It makes installation and maintenance of this component much easier. You can find instructions on how to install HACS [here](https://hacs.xyz/).

Navigate to HACS in you Home Assistants Interface.

Click "Explore & Download Repositories"

Search for "Rademacher Homepilot Bridge"

Click "Download this Repository with HACS".

Select the version you wish do download and finally click "Download".

Restart Home Assistant.

## 2. Manually

Copy the `rademacher` folder into yout Home Assistant's `custom_components` folder.
This should be located under the `/config` folder.

If you haven't done it already, you should create the `custom_components` folder on your `/config`.

Restart Home Assistant.

# Usage

First of all, you should add the devices in you Home Pilot Application, or in the Bridge's Interface. The integration works by fetching the list that is registered in the Hub. 

## 1. Automatic Discovery

When Home Assistant Core is running on the same sub-network as the Hub,
if auto-discovery works, you'll see a notification on HA GUI stating it found new devices.

Just click "Check it Out" and you'll be presented with the Integrations page where you should see the new Rademacher Bridge entry.

Click "Configure". If you have set a password for the Hub, enter it and press "Submit".

On the next dialog, Choose any device that you may want to exclude from managing in HA. If you want to manage all, just press "Submit".

You should now be presented with Device/Entities detected, you should select the HA Area where you want to add them.

## 2. Using Config Flow

If Hub has not been auto-discovered, or you just deleted the integration and want to add again:

Start by going to Configuration > Integrations, then press the "Add Integration" button.

Then, search for Rademacher and select it.

In the Dialog that appears, insert the HostName/IP Address of the Rademacher Bridge. Ex: `bridge.local` or `192.168.1.60`

Press "Submit".

If you have configured a password for the hub, you'll be asked for it. Just insert it and press "Submit".

On the next dialog, Choose any device that you may want to exclude from managing in HA. If you want to manage all, just press "Submit".

You should now be presented with Device/Entities detected, you should select the HA Area where you want to add them.

# Direct and Indirect Contributors

<!-- readme: contributors,thmnxo4,MrWeidenMr,fritte87 -start -->
<table>
<tr>
    <td align="center">
        <a href="https://github.com/peribeir">
            <img src="https://avatars.githubusercontent.com/u/7266291?v=4" width="100;" alt="peribeir"/>
            <br />
            <sub><b>Pedro Ribeiro</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/michelde">
            <img src="https://avatars.githubusercontent.com/u/10096708?v=4" width="100;" alt="michelde"/>
            <br />
            <sub><b>Michel Munzert</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/duhow">
            <img src="https://avatars.githubusercontent.com/u/1145001?v=4" width="100;" alt="duhow"/>
            <br />
            <sub><b>David Girón</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/misa1515">
            <img src="https://avatars.githubusercontent.com/u/61636045?v=4" width="100;" alt="misa1515"/>
            <br />
            <sub><b>Misa1515</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/der-berni">
            <img src="https://avatars.githubusercontent.com/u/5528912?v=4" width="100;" alt="mrweidenmr"/>
            <br />
            <sub><b>der-berni</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/thmnxo4">
            <img src="https://avatars.githubusercontent.com/u/76701693?v=4" width="100;" alt="thmnxo4"/>
            <br />
            <sub><b>Thmnxo4</b></sub>
        </a>
    </td>
  </tr>
  <tr>
    <td align="center">
        <a href="https://github.com/mrweidenmr">
            <img src="https://avatars.githubusercontent.com/u/99197872?v=4" width="100;" alt="mrweidenmr"/>
            <br />
            <sub><b>Mrweidenmr</b></sub>
        </a>
    </td></tr>
</table>
<!-- readme: contributors,thmnxo4,MrWeidenMr -end -->

# Supported Devices

The integration should work with the following devices (tested devices are marked in **bold** )

## Covers
- **DuoFern tubular motor actuator (DN:35000662)**
  - Tested on 9471 DuoFern Blinds Actuator
- DuoFern tubular motor control B50/B55 (DN:31500162)
- RolloTron Comfort DuoFern (DN:16234511_A)
- RolloTron radio beltwinder 60 kg (DN:14236011)
- **RolloTron radio beltwinder (DN:14234511)**
  - Tested on RolloTron Basis DuoFern 1200-UW Beltwinder
- **RolloTron radio swivel beltwindew (DN: 14233011)**
  - Tested on RolloTron swivel winder Standard DuoFern 2510-UW
- **DuoFern tubular motor actuator environmental sensor (DN:32000064_A)**
  - Tested on DuoFern Environmental Sensor Weather Station 9475
- DuoFern tubular motor actuator (DN:35140662)
- RolloTube S-line DuoFern (DN:23602075)
- RolloTube S-line Zip DuoFern (DN:25782075)

## Garage Covers
- RolloPort SX5 DuoFern garage door operator (DN:45059071)

## Sensors
- Sun sensor Troll Comfort DuoFern (DN:36500572_S)
- Temperature sensor DuoFern Radiator Actuator (DN:35003064_S)
- Temperature sensor DuoFern Room thermostat (DN:32501812_S)
- Sun sensor RolloTron Comfort DuoFern (DN:16234511_S)
- **Sensor DuoFern Environmental sensor (DN:32000064_S)**
  - Tested on DuoFern Environmental Sensor Weather Station 9475
- Z-Wave window/door contact (DN: 32002119)
- DuoFern Window/Door Contact (DN: 32003164)
- **DuoFern Room Thermostat (DN:32501812_S)**
  - Tested on DuoFern 9485 wireless radiator thermostat
- **DuoFern Smoke Alarm Device (DN: 32001664)**
  - Tested on DuoFern 9481 Wireless Smoke detector
- **DuoFern Sun/Wind Sensor (DN:32004464)**
  - Tested on DuoFern sun/wind sensor 9499

## Switches
- DuoFern Switch actuator (DN:35001164)
- **DuoFern Universal actuator 2-channel (DN:35000262)**
  - Tested on 9470 Universal Actuator

## Dimmers
- DuoFern Universal dimmer (DN:35140462)
- DuoFern Universal dimming actuator(DN:35000462)

## Thermostat
- **DuoFern Room Thermostat (DN:32501812_A)**
  - Tested on DuoFern 9485 wireless radiator thermostat

## Wall Controllers (new)
  - **DuoFern Multiple Wall Controller BAT (DN:32501974)**
    - Tested on DuoFern multiple wall switch BAT 9494-1
  - DuoFern Wall Controller 1 channel (DN:32501973)
