@echo off
call .venv\Scripts\activate
python simulator\sensor_simulator.py --scenario occupied_fire --readings 80 --interval 1
pause
