Set oShell = CreateObject("Shell.Application")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strPath = Wscript.ScriptFullName
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile)

MsgBox "This will install YAMM url handler and the MO plugin." & vbcrlf & vbcrlf & "Administrator access is required for this, so next screen will ask for that",64,"YAMM install"

oShell.ShellExecute "c:\python27\pythonw.exe", """" & strFolder & "\yammy ui.pyw"" --setup", "", "runas", 1