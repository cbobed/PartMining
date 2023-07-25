::===============================================================
:: File: completePipelineWSLFromDat.bat
:: Author: Carlos Bobed
:: Date: Jul 2021
:: Comments: script for Windows command line to launch the 
:: 		whole pipeline starting from a .dat file. It requires WSL and the scripts prepared for 
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

:: configuration of the first script to obtain the vectors 
set DIMENSION=200
set WIN_SIZE=5
set EPOCHS=10
set WORKERS=4


:: configuration of the second script to split the database_name
set CLUSTERING=k_means
set GRANULARITY=transaction
set NUM_CLUSTERS=4
:: set NORMALIZE to -normalize if we want to normalize the vectors
set NORMALIZE=
set PRUNING_THRESHOLD=0

:: configuration of the third script
:: set ALL_RATIOS to -all_ratios to calculate the partial ratios
set ALL_RATIOS=-all_ratios
set MERGE_METHOD=pruning

:: %1 is the filename of the dataset
cd %PYTHON_PROJECT_PATH%
CALL calculateVectors.bat %1 %WIN_SIZE% %DIMENSION% %EPOCHS% %WORKERS%

:: we should now have database_name+'_DIMENSION_WIN_EPOCHS_sg.vect' as name of the model
set MODEL_FILE=%1_%DIMENSION%_%WIN_SIZE%_%EPOCHS%_sg.vect
echo %MODEL_FILE%
CALL splitDatabase.bat %1 %MODEL_FILE% %CLUSTERING% %GRANULARITY% %NUM_CLUSTERS% %NORMALIZE%
:: depending on the granularity we can have different names
