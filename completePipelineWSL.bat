::===============================================================
:: File: completePipelineWSLFromDB.bat
:: Author: Carlos Bobed
:: Date: Jul 2021
:: Comments: script for Windows command line to launch the 
:: 		whole pipeline from a DB file. It requires WSL and the scripts prepared for 
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
set EPOCHS=20
set WORKERS=8
:: set ORD to force that the transactions are ordered centering the most 
:: 	supported items in the middle => it requires .db format to have the 
:: 	analysis of the database distribution
set ORD=


:: configuration of the second script to split the database_name
set CLUSTERING=k_means
set GRANULARITY=transaction
set NUM_CLUSTERS=8
:: set NORMALIZE to -normalize if we want to normalize the vectors
set NORMALIZE=
set PRUNING_THRESHOLD=10


:: configuration of the third script
:: set ALL_RATIOS to -all_ratios to calculate the partial ratios
set ALL_RATIOS=-all_ratios

:: %1 is the filename of the dataset
cd %PYTHON_PROJECT_PATH%
CALL calculateVectors.bat %1 %WIN_SIZE% %DIMENSION% %EPOCHS% %WORKERS% %ORD%

:: we should now have database_name+'_DIMENSION_WIN_EPOCHS_sg.vect' as name of the model
set MODEL_FILE=%1_%DIMENSION%_%WIN_SIZE%_%EPOCHS%_sg.vect
echo %MODEL_FILE%
CALL splitDatabase.bat %1 %MODEL_FILE% %CLUSTERING% %GRANULARITY% %NUM_CLUSTERS% %NORMALIZE%
:: depending on the granularity we can have different names

:: Transactions: we should have in output_databases => 
::  dbBasename_GRANULARITY_CLUSTERING_DIMENSIONd_kNUM_CLUSTERS_[True|False]Norm * 
for /F %%i in ("%1") do set DB_BASENAME=%%~ni
if "%NORMALIZE%"=="" (set NORM_NAME=False) ELSE (set NORM_NAME=True)
if "%CLUSTERING%"=="random" (SET TRANS_NAME=rand_clust) ELSE (
	if "%GRANULARITY%"=="transaction" (set TRANS_NAME=trans_clust) ELSE (set TRANS_NAME=item_clust)
	)
SET SPLITTED_BASENAME=%DB_BASENAME%_%GRANULARITY%_%CLUSTERING%_%DIMENSION%d_k%NUM_CLUSTERS%_%NORM_NAME%Norm_%TRANS_NAME%
:: afterwards  '_' + str(label) + '_k' + str(k) + '.dat' is added 

copy output_databases\%SPLITTED_BASENAME%* %SLIM_PROJECT_PATH%
cd %SLIM_PROJECT_PATH%
:: beware of the 
FOR %%d IN (%SPLITTED_BASENAME%*.dat) DO ( 
	for /F %%i in ("%%d") do set LOCAL_BASENAME=%%~ni
	wsl ./obtainCT-SLIM2012.sh !LOCAL_BASENAME!
	:: now, in LOCAL_BASENAME-output we have the codetable and the analysis file
	copy !LOCAL_BASENAME!-output\ct-latest.ct !OUTPUT_SPLITTED_PATH!\!LOCAL_BASENAME!.ct
	copy !LOCAL_BASENAME!-output\!LOCAL_BASENAME!.db.analysis.txt !OUTPUT_SPLITTED_PATH!\
)

cd %PYTHON_PROJECT_PATH% 

SET /A ACTUAL_NUM_CLUSTER=0
FOR %%d IN (%OUTPUT_SPLITTED_PATH%\%SPLITTED_BASENAME%*.dat) DO ( 
	SET /A ACTUAL_NUM_CLUSTER+=1
)

:: %2 is going to be the initial index 
echo We have %ACTUAL_NUM_CLUSTER% clusters
CALL calculateMergedRatio.bat %DB_BASENAME%.dat %OUTPUT_SPLITTED_PATH%\%SPLITTED_BASENAME% %ACTUAL_NUM_CLUSTER% %2 %PRUNING_THRESHOLD% %ALL_RATIOS%

cd %CURRENT_PATH%