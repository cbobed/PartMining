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