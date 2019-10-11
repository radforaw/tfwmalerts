This software is designed to analyse data from a range of Birmingham City Council Traffic monitoring systems and to produce 'alerts' when certain thesholds (e.g. congestion) are met.


The software consists of three python tools:-

* threshold_generator.py
  * For certain sensors, analysis is required of historic data in order to determine threshold levels, prior to running the main software. Ideally this file is run once a month or so, to keep thresholds up to date

* incident_manager.py
  * This program queries all sensors in real time, creating and deleting events in the database

* api.py
  * This software provides api functionality to the database, so that users can query current and historic data via an http request

Futher details are available within each of these tools.

There might be a script that you can run eventually that makes sure these run in the right order.