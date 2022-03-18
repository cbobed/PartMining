###############################################################################
# Author: Carlos Bobed
# Date: Dec 2021
# Comments: Code to get all the information of different batches gathered
#   using ./gatherData.sh script from the logs of the different executions
#   WARNING: script completely ADHOC for the dir structure of the test, it
#       is done this way on purpose :)
# Modifications:
###############################################################################

from xlwt import Workbook, easyxf
import os
import csv

class Headers:
    GLOBAL_VOCAB_SIZE = 'global_vocab_size'
    GLOBAL_FILE_ENTROPY = 'global_file_entropy'
    GLOBAL_FILE_WEIGHTED_ENTROPY = 'global_file_weighted_entropy'
    NUM_CLUSTERS = 'num_clusters'
    METHOD = 'method'
    VECTOR_TIME = 'vector_time'
    SPLIT_TIME = 'split_time'
    MERGE_TIME = 'merge_time'
    RATIOS = 'ratios'
    MERGED_RATIO = 'merged_ratio'
    MERGED_CODES = 'merged_codes'
    MINING_TIMES = 'mining_times'
    PARTITION_INFO = 'partition_info'
    VOCAB_SIZE = 'vocab_size'
    ADJUSTED_VOCAB_SIZE = 'adjusted_vocab_size'
    ENTROPY = 'entropy'
    NORMAL_ENTROPY = 'normal_entropy'
    WEIGHTED_ENTROPY = 'weighted_entropy'
    # average partition entropy
    AVERAGE_ENTROPY = 'avg_entropy'
    AVERAGE_NORM_ENTROPY = 'avg_norm_entropy'
    TOTAL_WEIGHTED_ENTROPY = 'weighted_norm_entropy'
    AVERAGE_RATIO = 'avg_ratio'
    AVERAGE_VOCAB_SIZE = 'avg_vocab_size'
    TIME_MAX = 'time_max'
    TIME_AVG = 'time_avg'
    NON_VALID_COUNT = 'not_valid_count'
    INVALID_BATCH = 'invalid_batch'
    EXECS = 'executions'

DATASET_NAMES = [
	"adult.dat",
	"anneal.dat",
	"breast.dat",
	"chessBig.dat",
	"chess.dat",
	"connect.dat",
	"heart.dat",
	"ionosphere.dat",
	"iris.dat",
	"led7.dat",
	"letrecog.dat",
	"mushroom.dat",
	"nursery.dat",
	"pageblocks.dat",
	"pendigits.dat",
	"pima.dat",
	"tictactoe.dat",
	"wine.dat"
                 ]

BATCH_NUMBER = 6
NUMBER_BLOCKS = 2 
#BATCH_DIR = os.path.join('.', 'statisticalRelevance', 'batch_results')
BATCH_DIR = os.path.join('.', 'batch_results', '200d-5-10-neg30')
OUTPUT_FILE='200d-5-10-neg30-grouped.xls'

def treat_time_cell (content):
    aux = content.split('m')
    min = float(aux[0])
    secs = float(aux[1].split('s')[0])
    return min*60+secs

def skip_row (csv_object, lines):
    for i in range(lines):
        csv_object.__next__()

if __name__ == "__main__":
    # this is the dictionary where we will store all the data before building the spreadsheet
    gathered_data = {}
    for batch in range(1,BATCH_NUMBER):
        print(f'batch {batch}')
        current_dir = os.path.join(BATCH_DIR, 'batch-'+str(batch))
        for dataset in DATASET_NAMES:
            try:
                print(f'-- dataset {dataset}')
                current_csv = os.path.join(current_dir, dataset+'-info.csv')
                if dataset not in gathered_data:
                    gathered_data[dataset]={}
                gathered_data[dataset][batch]={}
                ## ONLY FOR CONVENIENCE - DON'T TRY THIS AT HOME
                current_data = gathered_data[dataset][batch]
                with open(current_csv) as csv_file:
                    print(current_csv + " opened ...")
                    reader = csv.reader(csv_file, delimiter=';')
                    ## first block
                    current_row = reader.__next__()
                    current_data[Headers.GLOBAL_VOCAB_SIZE] =float(current_row[1])
                    current_row = reader.__next__()
                    current_data[Headers.GLOBAL_FILE_ENTROPY] = float(current_row[1])
                    current_row = reader.__next__()
                    current_data[Headers.GLOBAL_FILE_NORMAL_ENTROPY] = float(current_row[1])

                    current_row = reader.__next__()
                    current_data[Headers.EXECS] = {}
                    ## several blocks repeated differently depending on the method used
                    for i in range(NUMBER_BLOCKS):
                        current_row = reader.__next__()
                        current_data[Headers.EXECS][i] = {}
                        current_exec = current_data[Headers.EXECS][i]
                        current_exec[Headers.NUM_CLUSTERS] = int(current_row[0].split()[1])
                        current_exec[Headers.METHOD] = current_row[0].split()[3]
                        skip_row(reader, 2)
                        current_row = reader.__next__()
                        if (current_row[1].strip() != 'NA'):
                            current_exec[Headers.VECTOR_TIME] = treat_time_cell(current_row[1])
                        else:
                            current_exec[Headers.VECTOR_TIME] = 0.0
                        skip_row(reader, 3)
                        current_row = reader.__next__()
                        current_exec[Headers.SPLIT_TIME] = treat_time_cell(current_row[1])
                        skip_row(reader, 3)
                        current_row = reader.__next__()
                        current_exec[Headers.MERGE_TIME] = treat_time_cell(current_row[1])
                        ## Ratios
                        skip_row(reader, 3)
                        # print(f' {current_data[Headers.METHOD]}')
                        current_exec[Headers.RATIOS] = {}
                        for i in range(current_exec[Headers.NUM_CLUSTERS]):
                            current_row = reader.__next__()
                            #print(f' {current_row}')
                            current_exec[Headers.RATIOS][i] = float(current_row[1])

                        current_row = reader.__next__()
                        current_exec[Headers.MERGED_RATIO] = float(current_row[1])
                        current_row = reader.__next__()
                        current_exec[Headers.MERGED_CODES] = float(current_row[1])

                        ## Mining times
                        current_row = reader.__next__()
                        current_exec[Headers.MINING_TIMES] = {}
                        for i in range(current_exec[Headers.NUM_CLUSTERS]):
                            current_row = reader.__next__()
                            current_exec[Headers.MINING_TIMES][i] = treat_time_cell(current_row[1])
                        skip_row(reader,current_exec[Headers.NUM_CLUSTERS]+4)
                        current_exec[Headers.PARTITION_INFO] = {}
                        ## partition infos
                        for i in range(current_exec[Headers.NUM_CLUSTERS]):
                            current_row = reader.__next__()

                            assert(int(current_row[0].split()[1]) == i)
                            current_row = reader.__next__()
                            current_exec[Headers.PARTITION_INFO][i] = {}
                            current_exec[Headers.PARTITION_INFO][i][Headers.VOCAB_SIZE] = float(current_row[1])
                            current_row = reader.__next__()
                            current_exec[Headers.PARTITION_INFO][i][Headers.ADJUSTED_VOCAB_SIZE] = float(current_row[1])
                            current_row = reader.__next__()
                            current_exec[Headers.PARTITION_INFO][i][Headers.ENTROPY] = float(current_row[1])
                            current_row = reader.__next__()
                            current_exec[Headers.PARTITION_INFO][i][Headers.NORMAL_ENTROPY] = float(current_row[1])
                            current_row = reader.__next__()
                            current_exec[Headers.PARTITION_INFO][i][Headers.WEIGHTED_ENTROPY] = float(current_row[1])
                            current_row = next(reader, None)
                        print(current_exec)
            except Exception as e:
                print(f'Marking {batch} as INVALID')
                print(e)
                current_data[Headers.INVALID_BATCH] = True



    for dataset in DATASET_NAMES:
        for batch in range(1, BATCH_NUMBER):
            current_data = gathered_data[dataset][batch]
            if Headers.INVALID_BATCH not in current_data:
                for id in current_data[Headers.EXECS]:
                    current_exec = current_data[Headers.EXECS][id]
                    # average partition entropy
                    current_exec[Headers.AVERAGE_ENTROPY] = sum([current_exec[Headers.PARTITION_INFO][i][Headers.ENTROPY] for i in range(current_exec[Headers.NUM_CLUSTERS])]) / current_exec[Headers.NUM_CLUSTERS]
                    current_exec[Headers.AVERAGE_NORM_ENTROPY] = sum([current_exec[Headers.PARTITION_INFO][i][Headers.NORMAL_ENTROPY] for i in range(current_exec[Headers.NUM_CLUSTERS])]) / current_exec[Headers.NUM_CLUSTERS]
                    current_exec[Headers.TOTAL_WEIGHTED_ENTROPY] = sum([current_exec[Headers.PARTITION_INFO][i][Headers.WEIGHTED_ENTROPY] for i in range(current_exec[Headers.NUM_CLUSTERS])])
                    current_exec[Headers.AVERAGE_RATIO] = sum([current_exec[Headers.RATIOS][i] for i in range(current_exec[Headers.NUM_CLUSTERS])])/current_exec[Headers.NUM_CLUSTERS]
                    current_exec[Headers.AVERAGE_VOCAB_SIZE] = sum([current_exec[Headers.PARTITION_INFO][i][Headers.VOCAB_SIZE] for i in range(current_exec[Headers.NUM_CLUSTERS])]) / current_exec[Headers.NUM_CLUSTERS]
                    current_exec[Headers.TIME_MAX] = time_max = current_exec[Headers.VECTOR_TIME] + \
                               current_exec[Headers.SPLIT_TIME] + \
                               max([current_exec[Headers.MINING_TIMES][i] for i in range(current_exec[Headers.NUM_CLUSTERS])])
                    current_exec[Headers.TIME_AVG] = current_exec[Headers.VECTOR_TIME] + \
                            current_exec[Headers.SPLIT_TIME] + \
                                                     (sum([current_exec[Headers.MINING_TIMES][i] for i in range(current_exec[Headers.NUM_CLUSTERS])]) / current_exec[Headers.NUM_CLUSTERS])
                    # print(current_exec)

    book = Workbook(style_compression=2)
    for dataset in DATASET_NAMES:
        print(f'- {dataset}')
        current_datasheet = book.add_sheet(dataset)
        invalid_batches = sum([1 for i in range(1,BATCH_NUMBER) if Headers.INVALID_BATCH in gathered_data[dataset][i]])
        current_datasheet.write(0, 0, 'batches: '+str(BATCH_NUMBER))
        current_datasheet.write(0, 1, 'invalid ones: '+str(invalid_batches))
        col = 1
        for execID in range(NUMBER_BLOCKS):
            line = 1
            ## for the sake of readability and processing it afterwards,
            ## we gather together all the data

            ## find the first valid batch
            first_valid_batch = -1
            current_batch = 1
            while first_valid_batch == -1 and current_batch <= BATCH_NUMBER:
                if Headers.INVALID_BATCH not in  gathered_data[dataset][current_batch]:
                    first_valid_batch = current_batch
                else:
                    current_batch +=1

            if first_valid_batch < BATCH_NUMBER:
                current_exec = gathered_data[dataset][first_valid_batch][Headers.EXECS][execID]
                current_datasheet.write(line, col, current_exec[Headers.METHOD])
                current_datasheet.write(line, col + 1, 'num_clusters: ' + str(current_exec[Headers.NUM_CLUSTERS]))
                line += 1

                for batch in range(1,BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.AVERAGE_ENTROPY+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.AVERAGE_ENTROPY])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.AVERAGE_NORM_ENTROPY+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.AVERAGE_NORM_ENTROPY])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.TOTAL_WEIGHTED_ENTROPY+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.TOTAL_WEIGHTED_ENTROPY])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.AVERAGE_RATIO+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.AVERAGE_RATIO])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.MERGED_RATIO+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.MERGED_RATIO])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.MERGED_CODES+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.MERGED_CODES])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.AVERAGE_VOCAB_SIZE+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.AVERAGE_VOCAB_SIZE])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.TIME_MAX+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.TIME_MAX])
                        line += 1
                line+=1

                for batch in range(1, BATCH_NUMBER):
                    if (Headers.INVALID_BATCH not in gathered_data[dataset][batch]):
                        current_datasheet.write(line, col+1, Headers.TIME_AVG+'_'+str(batch))
                        current_datasheet.write(line, col+2, gathered_data[dataset][batch][Headers.EXECS][execID][Headers.TIME_AVG])
                        line += 1
            col +=3
    book.save(OUTPUT_FILE)
