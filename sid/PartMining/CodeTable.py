###############################################################################
# File: CodeTable.py
# Author: Carlos Bobed
# Date: Dec 2020
# Comments: Factorized methods from the original notebooks related to the
#   management of code tables
#   not OO, should be refactorized
# Modifications:
##############################################################################



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

def build_SCT(database):
    sct_codetable = {}
    for trans in database:
        for singleton in [int(item) for item in database[trans]]:

            if singleton not in sct_codetable:
                sct_codetable[singleton] = {'code': str(singleton), 'support': 0, 'usage': 0}
            sct_codetable[singleton]['usage'] = sct_codetable[singleton]['usage'] + 1
            sct_codetable[singleton]['support'] = sct_codetable[singleton]['support'] + 1
    return sct_codetable

def convert_int_codetable (codetable, analysis_table):
    converted = {}
    for label in codetable:
        translated_code = [ analysis_table[int(item)] for item in codetable[label]['code']]
        converted[label] = {'code_int':translated_code,
                            'code_set':set(translated_code)}
    return converted


## naive way of merging the codetables
## for convenience we work here with integers (we kept the codetables as string tokens to be able to handle the vector models)
def merge_codetables(codetables):
    merged = {}
    non_colision_labelbase = 0
    for ct in codetables:
        for label in ct:
            current_label = str(non_colision_labelbase) + '_' + str(label)
            merged[current_label] = ct[label]
        non_colision_labelbase += 1
    # we keep track of the codes that are duplicated
    to_omit = set()
    merged_key_list = list(merged.keys())
    for i in range(len(merged_key_list)):
        if merged_key_list[i] not in to_omit:
            for j in range(i + 1, len(merged_key_list)):
                if merged_key_list[j] not in to_omit:
                    # depending on how the table has been obtained it might or not have the code_set field
                    ## converted using the analysis table (convert_int_codetable) => it has
                    ## loaded from file => it hasn't
                    if 'code_set' in merged[merged_key_list[i]]:
                        set_i = merged[merged_key_list[i]]['code_set']
                    else:
                        set_i = set([int(item) for item in merged[merged_key_list[i]]['code']])
                    if 'code_set' in merged[merged_key_list[j]]:
                        set_j = merged[merged_key_list[j]]['code_set']
                    else:
                        set_j = set([int(item) for item in merged[merged_key_list[j]]['code']])
                    if set_i == set_j:
                        to_omit.add(merged_key_list[j])
    # we get rid of the duplicated entries in the codetable
    [merged.pop(code) for code in to_omit]

    for label in merged:
        if 'code_int' in merged[label]:
            merged[label]['code'] = [str(item) for item in merged[label]['code_int']]
        merged[label]['usage'] = 0
        merged[label]['support'] = 0

    return merged

