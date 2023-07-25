
setlocal EnableDelayedExpansion
echo OFF 
FOR %%d IN (%1*.dat) DO ( 
	echo %%d
	echo entropyCalculator.bat %%d %2 %3
	call entropyCalculator.bat %%d %2 %3
)