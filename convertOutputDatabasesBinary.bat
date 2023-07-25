
setlocal EnableDelayedExpansion

FOR %%d IN (output_databases\*.dat) DO ( 
	echo %%d
	CALL binaryConverter.bat %%d
)