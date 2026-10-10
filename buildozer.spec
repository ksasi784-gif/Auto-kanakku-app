[app]
title = Tamilan Auto Meter
package.name = tamilanautometer
package.domain = org.sasi.meter
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 0.1
icon.filename = icon.png
requirements = python3,kivy,qrcode,pillow,plyer
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
