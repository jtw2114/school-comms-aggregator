Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\jerem\school-comms-aggregator"
WshShell.Environment("Process")("PYTHONPATH") = "C:\Users\jerem\school-comms-aggregator"
WshShell.Run """C:\Users\jerem\school-comms-aggregator\.venv\Scripts\pythonw.exe"" -m src.main", 0, False
