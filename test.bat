setlocal EnableDelayedExpansion


for /f %%i in ('cd') do set current=%%i
echo %current%
echo %1
set t=%current%%1
echo %t%
set name=anneal.dat
for /F %%i in ("%name%") do set BASENAME=%%~ni
echo %BASENAME%

set t=
set x=er
if "%t%"=="" echo kk
if %x%==er echo ll 

for %%d in (*.bat) do echo %%d

:: configuration of the first script to obtain the vectors 
set /A DIMENSION=200
set WIN_SIZE=5
set EPOCHS=10
set WORKERS=4
set MODEL_FILE=%1_%DIMENSION%_%WIN_SIZE%_%EPOCHS%_sg.vect
echo %MODEL_FILE%

set LOCAL_BASENAME=kk
FOR %%d IN (*.dat) DO (
	echo %%d
	echo local:!LOCAL_BASENAME!
	for /F %%i in ("%%d") do set LOCAL_BASENAME=%%~ni
	echo !LOCAL_BASENAME!
)  

set cnt=0
for %%A in (*) do set /a cnt+=1
echo File count = %cnt%

SET ACTUAL_NUM_CLUSTER=0
echo Trying
FOR %%e IN (*.dat) DO ( 
	echo flullfy
	echo %%e
	SET /A ACTUAL_NUM_CLUSTER+=1
)
echo !ACTUAL_NUM_CLUSTER!