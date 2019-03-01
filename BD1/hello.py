# Anandh Varadarajan, 112505082

# code for CSE545 - Spring 2019 - Try the count with another approximation algorithm Flajolet Martin
# Assignment 1 - Part II
# v0.01
from pyspark import SparkContext
import re
import hashlib
from operator import add
import psutil #removes WARNS from console
nonFluencyDictionary = {'mm':'MM','oh':'OH','ah':'OH','si':'SIGH', 'ug':'SIGH', 'uh':'SIGH','um':'UM', 'hm':'UM', 'hu':'UM'}

'''
This function returns only records that has the non-fluencies
'''
def checkMatch(line):
    group = (re.search(
        r'^.*\b(mmm+|ohh+|ahh+|umm*|hmm*|huh|ugh|uh|sigh+)\b(.)*\b.*$',str(line[1]),0|re.I))
    if (group):
        return [line[0], line[1]];

'''
This function returns a tuple of the form (non-fluency group, text following group) for further reduction
'''
def returnMatch(line):
    group = re.search(r'^.*\b(mmm+|ohh+|ahh+|umm*|hmm*|huh|ugh|uh|sigh+)\b(.)*\b.*$',str(line),0|re.I)
    if (group):
        return [group.group(1),re.sub(r"[\\?+ | \\:+ | \\*+ | \\#+ | \\@+ | \\;+ | \\,+ | \\)+ | \\(+]"," ",line.split(group.group(1))[1]).strip()];


def hashMD5(word):
    hash1 = False;
    sum = 0;
    hashValue = 0;
    hv = hashlib.md5(word.encode())
    for i in hv.hexdigest():
        sum = sum + ord(i)
    hashValue = sum%100000;
    return hashValue;

def trail(hashvalue):
    num = 0;
    if hashvalue==0:
        return 0;
    else:
        while ((hashvalue) & 1) == 0:
            hashvalue = hashvalue>>1
            num = num+1;
        return num;
def FlajoletMartin(word):
    hashValue = hashMD5(word)
    return trail(hashValue)



#loads the count values into corresponding dictionary.
def loadResultDictionary(filteredAndCountedRdd,distinctPhraseCounts):
    sighRDD = filteredAndCountedRdd.filter(lambda x: x[0] == 'SIGH').map(lambda x: x[1])
    umRDD = filteredAndCountedRdd.filter(lambda x: x[0] == 'UM').map(lambda x: x[1])
    mmRDD = filteredAndCountedRdd.filter(lambda x: x[0] == 'MM').map(lambda x: x[1])
    ohRDD = filteredAndCountedRdd.filter(lambda x: x[0] == 'OH').map(lambda x: x[1])
    if (not sighRDD.isEmpty()):
        distinctPhraseCounts['SIGH'] = sighRDD.reduce(lambda x : x)

    if (not umRDD.isEmpty()):
        distinctPhraseCounts['UM'] = umRDD.reduce(lambda x : x)

    if (not mmRDD.isEmpty()):
        distinctPhraseCounts['MM'] = mmRDD.reduce(lambda x : x)

    if (not ohRDD.isEmpty()):
        distinctPhraseCounts['OH'] = ohRDD.reduce(lambda x : x)


def umbler(sc, rdd):
    # sc: the current spark context
    #    (useful for creating broadcast or accumulator variables)
    # rdd: an RDD which contains location, post data.
    #
    # returns a *dictionary* (not an rdd) of distinct phrases per um category
    distinctPhraseCounts = {'MM': 0, 'OH': 0, 'SIGH': 0, 'UM': 0}

    #Load the locations in an RDD
    locationRDD = sc.textFile('C://Users//anand//Downloads//convertcsv.csv').map(lambda inp: inp.replace('"', "")).map(
        lambda x: (x, ''))

    #Load the RDD with records containing only the non-fluencies
    nonFluenciesRDD = rdd.map(lambda x: list(x)).map(lambda x: checkMatch(x)).filter(lambda x: x != None).map(
        lambda x: (x[0], str(x[1]).replace(".", "").strip()))

    #Join the NF RDD with location RDD -> To get another RDD that includes final records to be processed for distinct words following non-fluency
    validPostsToCountRDD = nonFluenciesRDD.join(locationRDD).map(lambda x : [x[0],x[1][0]])

    # SETUP for streaming algorithms
    #custom bloom filter implementation for distinct word count
    def countDistinctUsingStreamingAlgorithm(d):
        list = (returnMatch(d[1]))
        wordToBeHashed = ""
        if (list is not None):
            words = list[1].replace(".", "").replace("!", "").split(" ")
            for word in words[:3]:
                if (word):
                    wordToBeHashed += word;
            h1 = hashMD5(wordToBeHashed)
            max_so_far = FlajoletMartin(wordToBeHashed)
            return (nonFluencyDictionary.get(list[0][:2].lower()),
                    2**max_so_far)

    filteredAndCountedRdd = validPostsToCountRDD.map(lambda  x: countDistinctUsingStreamingAlgorithm(x)).filter(lambda x : x is not None).reduceByKey(lambda x,y : max(x,y))

    loadResultDictionary(filteredAndCountedRdd,distinctPhraseCounts)

    return distinctPhraseCounts


################################################
## Testing Code (subject to change for testing)

import numpy as np
from pprint import pprint
from scipy import sparse


def runTests(sc):

    #Umbler Tests:
    print("\n*************************\n Umbler Tests\n*************************")
    testFileSmall = 'C://Users//anand\Documents//PythonProjects//BD1//publicSampleLocationTweet_small.csv'
    testFileLarge = 'C://Users//anand\Documents//PythonProjects//BD1//publicSampleLocationTweet_large.csv'

    # setup rdd
    import csv

    smallTestRdd = sc.textFile(testFileSmall).mapPartitions(lambda line: csv.reader(line))
    #pprint(smallTestRdd.take(5))  #uncomment to see data
    pprint(umbler(sc, smallTestRdd))

    largeTestRdd = sc.textFile(testFileLarge).mapPartitions(lambda line: csv.reader(line))
    ##pprint(largeTestRdd.take(5))  #uncomment to see data
    pprint(umbler(sc, largeTestRdd))

    return

sc = SparkContext(master="local[*]",appName="PythonStreamingNetworkWordCount")
runTests(sc)
sc.stop()
