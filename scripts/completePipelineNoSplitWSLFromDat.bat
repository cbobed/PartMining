::===============================================================
:: File: completePipelineNoSplitWSL.bat
:: Author: Carlos Bobed
:: Date: Jul 2021
:: Comments: script for Windows command line to launch the 
:: 		whole pipeline to calculate the codetable and the compression 
:: 		from a single databse. It requires WSL and the scripts prepared for 
::  	Maillot et al. 2018, and Bobed et al. 2020 to obtain the codetables 
:: 		This script must be launched within a conda environment 
:: 		with the proper packages installed. 
:: 		It is easily adaptable to bash (the ones launched via 
:: 		WSL already are bash scripts)
:: 	Usage: configure the execution variables,and the following 
::		parameters are accepted: 
:: 			%1 the filename of the dataset
::===============================================================

setlocal EnableDelayedExpansion

for /f %%i in ('cd') do set CURRENT_PATH=%%i

set PYTHON_PROJECT_PATH=c:\Users\cbobed\workingDir\git\PartMining
set SLIM_PROJECT_PATH=C:\Users\cbobed\workingDir\software\slim
set DATASETS_PATH=c:\Users\cbobed\workingDir\git\PartMining
set OUTPUT_SPLITTED_PATH=%PYTHON_PROJECT_PATH%\output_databases

for /F %%i in ("%1") do set DB_BASENAME=%%~ni

copy %1 %SLIM_PROJECT_PATH%
cd %SLIM_PROJECT_PATH%

wsl ./obtainCT-SLIM2012.sh !DB_BASENAME!
:: now, in LOCAL_BASENAME-output we have the codetable and the analysis file
copy !DB_BASENAME!-output\ct-latest.ct !OUTPUT_SPLITTED_PATH!\!DB_BASENAME!.ct
copy !DB_BASENAME!-output\!DB_BASENAME!.db.analysis.txt !OUTPUT_SPLITTED_PATH!\

cd %PYTHON_PROJECT_PATH% 

CALL calculateRatio.bat %1 !OUTPUT_SPLITTED_PATH!\!DB_BASENAME!.db.analysis.txt !OUTPUT_SPLITTED_PATH!\!DB_BASENAME!.ct

cd %CURRENT_PATH%