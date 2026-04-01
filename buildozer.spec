[app]
title = Cane Toad Trap
package.name = canetoadtrap
package.domain = org.canetoad

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0.0

requirements = python3,flet,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1



