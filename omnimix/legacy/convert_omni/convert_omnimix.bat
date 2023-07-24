@echo off

pushd
cd /d %~dp0

omnimix_data_install\\python\\python.exe convert_omnimix.py

popd

pause