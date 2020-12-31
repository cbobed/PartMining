# From Visualizing Notebook ... the horror, don't try this at home ...

## method to read for the Vreeken's codetable format
## we don't need it to be a generator
## we do label each code and honor the order in the code table (length, support, lexicographical)
## following Pierre's suggestion, we keep track of the codes and the transaction IDs
def read_codetable(filename, load_all):
    codes = {}
    label = 0
    with open(filename, mode='rt', encoding='UTF-8') as file:
        for line in file:
            item_line = list(filter(None, line.rstrip('\n').split(' ')))
            ## only_used => those codes whose usage is > 0
            ## we get the last token, check whether it ends with )
            ## then, we get exactly the contents and check whether the first
            ## component is different from 0
            if (item_line[-1].endswith(')')):
                usage,support = item_line[-1][1:-1].split(',')
                if (load_all or int(usage) != 0):
                    codes[label]={'code': item_line[:-1], 'usage':int(usage), 'support':int(support)}
                    label+=1
    return codes


def calculate_cover(transaction, code_table):
    item_set = set(transaction)
    codes = []
    current_code = 0
    while (len(item_set) != 0 and current_code < len(code_table) ):
        aux_code_set = set(code_table[current_code]['code'])
        if (aux_code_set.issubset(item_set)):
            codes.append(current_code)
            item_set.difference_update(aux_code_set)
        current_code+=1
    return codes