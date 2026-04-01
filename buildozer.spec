[app]
title = Cane Toad Trap
package.name = canetoadtrap
package.domain = org.canetoad
source.dir = .
version = 1.0.0
requirements = python3,requests
permissions = INTERNET

[app:android]
orientation = portrait
fullscreen = 0
android.api = 30
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1






