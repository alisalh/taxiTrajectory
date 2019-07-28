"""
Description     : Simple Python implementation of the Apriori Algorithm
Usage:
    $python apriori.py -f DATASET.csv -s minSupport  -c minConfidence
    $python apriori.py -f DATASET.csv -s 0.15 -c 0.6
"""

import sys

from itertools import chain, combinations
from collections import defaultdict
from optparse import OptionParser
import numpy as np

num_long = 200
num_att = 200



def rolling_window(a, size):
    shape = a.shape[:-1] + (a.shape[-1] - size + 1, size)
    strides = a.strides + (a. strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def array_subset(array, subarray):
    #print(array.shape, subarray.shape)
    if len(array) < len(subarray):
        return False
    rolling_array = rolling_window(array, subarray.shape[0])
    return np.any(np.all(rolling_array == subarray, axis=1))

# def subsets(arr):
#     """ Returns non empty subsets of arr"""
#     item_str_list = arr.split("_")
#     item_list = [it for it in item_str_list]
#     if len(item_list) == 1:
#         return [[None, arr]]
#     else:
#         sub_1 = "_".join(item_list[1:])
#         sub_2 = "_".join(item_list[:-1])
#     return [(item_list[0], sub_1), (item_list[-1], sub_2)]
#     #return chain(*[combinations(arr, i + 1) for i, a in enumerate(arr)])
def encode_item_list(item_tmp):
    if len(item_tmp) > 6:
        start_length = 3
    else:
        start_length = max(1, len(item_tmp) // 2)
    start_points = sorted(item_tmp[:start_length])
    end_points = sorted(item_tmp[-start_length:])
    item_tmp_str = "_".join([str(start_length)] + start_points + sorted(item_tmp) + end_points)
    return item_tmp_str


def returnItemsWithMinSupport(itemSet, transactionList, minSupport, freqSet):
    """calculates the support for items in the itemSet and returns a subset
   of the itemSet each of whose elements satisfies the minimum support"""
    if len(itemSet) == 0:
        return set(), {}
    _itemSet = set()
    _itemMap = {}
    localSet = defaultdict(int)

    # for item in itemSet:
    #     item_list = item.split("_")
    #     item_list = [int(it) for it in item_list]
    #     item_array = np.array(item_list)
    #     for transaction in transactionList:
    #         if array_subset(transaction, item_array):
    #             freqSet[item] += 1
    #             localSet[item] += 1
    tmp = itemSet.pop()
    tmp_list = tmp.split("_")
    item_length = len(tmp_list)-1-2*int(tmp_list[0])
    itemSet.add(tmp)
    for transaction in transactionList:
        for ti in range(len(transaction)-item_length+1):
            item_tmp = transaction[ti:ti+item_length]
            item_tmp = [str(it) for it in item_tmp]

            item_tmp_str = encode_item_list(item_tmp)
            if item_tmp_str in itemSet:
                freqSet[item_tmp_str] += 1
                localSet[item_tmp_str] += 1
                item_tmp_str_set = _itemMap.get(item_tmp_str, set())
                item_tmp_str_set.add("_".join(item_tmp))
                _itemMap[item_tmp_str] = item_tmp_str_set


    supports = []
    for item, count in localSet.items():
        support = float(count) / len(transactionList)
        supports.append(support)
        if support >= minSupport:
            _itemSet.add(item)
        else:
            freqSet.pop(item, None)
            _itemMap.pop(item, None)
            # del freqSet[item]
            # del _itemMap[item]

    return _itemSet, _itemMap


def joinSet(itemSet, itemMap, road_to_road_map):
    """Join a set with itself and returns the n-element itemsets"""
    _itemSet = set()
    for item in itemSet:
        item_instance_list = list(itemMap[item])
        for item_instance in item_instance_list:
            item_str_list = item_instance.split("_")
            item_list = [int(it) for it in item_str_list]
            start_nearby = road_to_road_map[item_list[0]]
            for point in start_nearby:
                new_item_str_list = [str(point)] + item_str_list[:-1]
                new_item_str = encode_item_list(new_item_str_list)
                if new_item_str in itemSet:
                    join_new_item_str_list = [str(point)] + item_str_list
                    join_new_item_str = encode_item_list(join_new_item_str_list)
                    _itemSet.add(join_new_item_str)

            end_nearby = road_to_road_map[item_list[-1]]
            for point in end_nearby:
                new_item_str_list = item_str_list[1:]+[str(point)]
                new_item_str = encode_item_list(new_item_str_list)
                if new_item_str in itemSet:
                    join_new_item_str_list = sorted(item_str_list + [str(point)])
                    join_new_item_str = encode_item_list(join_new_item_str_list)
                    _itemSet.add(join_new_item_str)
    return _itemSet


def getItemSetTransactionList(data_iterator):
    transactionList = list()
    itemSet = set()
    for record in data_iterator:
        transaction = record
        transactionList.append(np.array(transaction))
        for item in transaction:
            str_key = "_".join(['1']+3*[str(item)])
            itemSet.add(str_key)  # Generate 1-itemSets
    return itemSet, transactionList


def runApriori(data_iter, minSupport, road_to_road_map):
    """
    run the apriori algorithm. data_iter is a record iterator
    Return both:
     - items (tuple, support)
     - rules ((pretuple, posttuple), confidence)
    """
    itemSet, transactionList = getItemSetTransactionList(data_iter)

    freqSet = defaultdict(int)
    largeSet = dict()
    # Global dictionary which stores (key=n-itemSets,value=support)
    # which satisfy minSupport

    assocRules = dict()
    # Dictionary which stores Association Rules

    oneCSet, itemMap = returnItemsWithMinSupport(itemSet,
                                        transactionList,
                                        minSupport,
                                        freqSet)

    currentLSet = oneCSet
    currentLMap = itemMap
    k = 2
    while (currentLSet != set([])):
        largeSet[k - 1] = (currentLSet, currentLMap)
        currentLSet = joinSet(currentLSet, currentLMap, road_to_road_map)
        currentCSet, currentCMap = returnItemsWithMinSupport(currentLSet,
                                                transactionList,
                                                minSupport,
                                                freqSet)
        currentLSet = currentCSet
        currentLMap = currentCMap

        print("%s: %s"%(k, len(currentLSet)))
        k = k + 1

    def getSupport(item):
        """local function which Returns the support of an item"""
        return float(freqSet[item]) / len(transactionList)


    toRetItems = []
    for key, value in largeSet.items():
        toRetItems.extend([(item, getSupport(item))
                           for item in value[0]])

    # toRetRules = []
    # for (key, value) in list(largeSet.items()):
    #     for item in value:
    #         _subsets = subsets(item)
    #         for element in _subsets:
    #             remain = element[0]
    #             if remain is not None:
    #                 confidence = getSupport(item) / getSupport(element[1])
    #                 if confidence >= minConfidence:
    #                     toRetRules.append((element[1], remain, item,
    #                                        confidence))
    return largeSet, freqSet, toRetItems


# def printResults(items, rules):
#     """prints the generated itemsets sorted by support and the confidence rules sorted by confidence"""
#     for item, support in sorted(items, key=lambda (item, support): support):
#         print("item: %s , %.3f" % (str(item), support))
#     print("\n------------------------ RULES:"
#     for rule, confidence in sorted(rules, key=lambda (rule, confidence): confidence):
#         pre, post = rule
#         print("Rule: %s ==> %s , %.3f" % (str(pre), str(post), confidence))


def dataFromFile(fname):
    """Function which reads from the file and yields a generator"""
    file_iter = open(fname, 'rU')
    for line in file_iter:
        line = line.strip().rstrip(',')  # Remove trailing comma
        record = frozenset(line.split(','))
        yield record


if __name__ == "__main__":

    optparser = OptionParser()
    optparser.add_option('-f', '--inputFile',
                         dest='input',
                         help='filename containing csv',
                         default=None)
    optparser.add_option('-s', '--minSupport',
                         dest='minS',
                         help='minimum support value',
                         default=0.15,
                         type='float')
    optparser.add_option('-c', '--minConfidence',
                         dest='minC',
                         help='minimum confidence value',
                         default=0.6,
                         type='float')

    (options, args) = optparser.parse_args()

    inFile = None
    if options.input is None:
        inFile = sys.stdin
    elif options.input is not None:
        inFile = dataFromFile(options.input)
    else:
        print('No dataset filename specified, system with exit\n')
        sys.exit('System will exit')

    minSupport = options.minS
    minConfidence = options.minC

    items, rules = runApriori(inFile, minSupport, minConfidence)

    # printResults(items, rules)
