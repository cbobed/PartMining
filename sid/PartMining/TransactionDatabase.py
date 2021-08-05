###############################################################################
# File: TransactionDatabase.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Factorized methods from the original notebooks related to the
#   management of transaction databases
#   Transaction Databases in this project are just a dictionary with an array
#       of strings / words
# Modifications:
##############################################################################

## to keep track of the transactions id in the database, we read them in a different method
def read_database_db (filename):
    transactions = {}
    label = 0
    with open(filename, mode='rt', encoding='UTF-8') as file:
        for line in open(filename, mode='rt', encoding='UTF-8'):
            if (line.split(':')[0].isnumeric()):
                aux = line.split(':')[1].rstrip('\n')
                words = filter(None,aux.split(' '))
                transactions[label] = list(words)
                label+=1
    return transactions

def read_database_dat(filename):
    transactions = {}
    label = 0
    with open(filename, mode='rt', encoding='UTF-8') as file:
        for line in open(filename, mode='rt', encoding='UTF-8'):
            aux = line.rstrip('\n')
            words = filter(None,aux.split(' '))
            transactions[label] = list(words)
            label+=1
    return transactions

## read information from the analysis to get back to the .dat file and select them
## we can cluster them according just to the items, or to the transactions themselves

def read_analysis_table (filename):
    table = {}
    with open(filename, mode='rt', encoding='UTF-8') as file:
        # skip the first  lines
        for i in range(15):
            file.readline()
        current_line = file.readline()
        while (current_line != "\n"):
            aux = current_line.split()[0].split('=>')
            table[int(aux[0])] = int(aux[1])
            current_line = file.readline()
    return table

## read information from the analysis to get back to the .dat file and select them
## we can cluster them according just to the items, or to the transactions themselves
## added the bidir table
def read_analysis_table_bidir (filename):
    db_dat_table = {}
    dat_db_table = {}
    with open(filename, mode='rt', encoding='UTF-8') as file:
        # skip the first  lines
        for i in range(15):
            file.readline()
        current_line = file.readline()
        while (current_line != "\n"):
            aux = current_line.split()[0].split('=>')
            db_dat_table[int(aux[0])] = int(aux[1])
            dat_db_table[int(aux[1])] = int(aux[0])
            current_line = file.readline()
    return db_dat_table, dat_db_table