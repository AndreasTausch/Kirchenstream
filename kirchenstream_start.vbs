Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\kirchenstream && python main.py", 0, False