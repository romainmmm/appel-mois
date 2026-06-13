Set WshShell = CreateObject("WScript.Shell")
WshShell.Run Chr(34) & Replace(WScript.ScriptFullName, "Repartition des menages.vbs", "lancer.bat") & Chr(34), 0, False
