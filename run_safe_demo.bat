@echo off
call .venv\Scripts\activate
python simulator\sensor_simulator.py --scenario safe --readings 80 --interval 1
pause
