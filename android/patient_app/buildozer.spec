[app]
title = CHRONO-PCOS Patient V8.3+
package.name = chronopcospatient
package.domain = org.chronopcos.patient
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
version = 8.3
requirements = python3,kivy,sqlite3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
p4a.branch = master
[buildozer]
log_level = 2
warn_on_root = 1
