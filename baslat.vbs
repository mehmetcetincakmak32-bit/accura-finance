Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
basePath = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & basePath & "\baslat.bat" & Chr(34), 0, False
