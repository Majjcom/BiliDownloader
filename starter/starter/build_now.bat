@echo off

call "D:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"

@echo Start Build...

devenv %cd%\starter.sln /Rebuild "Release|x86"

@echo Build finish...

PAUSE