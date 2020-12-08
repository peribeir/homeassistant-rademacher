![logo](https://github.com/peribeir/homeassistant-rademacher/raw/master/img/logo.png)
A Home Assistant custom Integration for local handling of Devices connected to Rademacher bridge.

Currently only covers are supported.

Tested on Rademacher Rollotron 1200 Shutters with the Rademacher Start2Smart Bridge (although it should also work with HomePilot).

# Installation
Copy the `rademacher` folder into yout Home Assistant's `custom_components` folder.
This should be located under the `/config` folder.

If you haven't done it already, you should create the `custom_components` folder on your `/config`.

# Usage

First of all, you should add the devices in you Home Pilot Application, or in the Bridge's Interface. The integration works by fetching the list that is registered in the Bridge. 

## 1. Using Config Flow

Start by going to Configuration > Integrations, then press the "Add Integration" button.

Then, search for Rademacher and select it.

In the Dialog that appears, insert the HostName/IP Address of the Rademacher Bridge. Ex: `bridge.local` or `192.168.1.60`

Press "Submit".

You should now be presented with Device/Entities detected, you should select the HA Area where you want to add them.