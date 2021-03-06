from csv import DictWriter, DictReader
from bs4 import BeautifulSoup
import multiprocessing
import importlib
import time
import xlrd
import lxml
import re
import os

data = []


def addToList(object):
    data.extend(object)


def pullLeg(scriptList, partyDict):
    name = multiprocessing.current_process().name
    print 'Process {0} is starting on {1}'.format(name, scriptList[0])
    mod = importlib.import_module(scriptList[0])
    dictList = eval(str('mod.' + scriptList[1] + '(partyDict)'))
    print 'process {0} completed {1} with {2} records'.format(name, scriptList[0], len(dictList))
    return dictList


def parallelPull(scripts, partyDict):
    pool = multiprocessing.Pool(processes=20)
    for script in scripts:
        pool.apply_async(pullLeg, args=(script, partyDict), callback = addToList)
    pool.close()
    pool.join()


def downloadLegislators():
    scripts = [['MALeg', 'getMAHouse'], ['NCLeg', 'getNCLeg'], ['MALeg', 'getMASenate'], ['TXLeg', 'getTXLeg'], ['PALeg', 'getPALeg'], ['AKLeg', 'getAKLeg'], ['KSLeg', 'getKSLeg'], ['ALLeg', 'getALLeg'], ['ARLeg', 'getARLeg'], ['AZLeg', 'getAZLeg'], ['CALeg', 'getCALeg'], ['COLeg', 'getCOLeg'], ['CTLeg', 'getCTLeg'], ['DELeg', 'getDELeg'], ['FLHouse', 'getFLHouse'], ['FLSenate', 'getFLSen'], ['GAHouse', 'getGAHouse'], ['GASenate', 'getGASenate'], ['HILeg', 'getHILeg'], ['IALeg', 'getIALeg'], ['IDLeg', 'getIDLeg'], ['ILLeg', 'getILLeg'], ['INLeg', 'getINLeg'], ['KYLeg', 'getKYLeg'], ['LALeg', 'getLALeg'], ['MDLeg', 'getMDLeg'], ['MELeg', 'getMELeg'], ['MILeg', 'getMILeg'], ['MNHouse', 'getMNHouse'], ['MNSenate', 'getMNSenate'], ['MOLeg', 'getMOLeg'], ['MSLeg', 'getMSLeg'], ['MTLeg', 'getMTLeg'], ['NDLeg', 'getNDLeg'], ['NELeg', 'getNELeg'], ['NHLeg', 'getNHLeg'], ['NJLeg', 'getNJLeg'], ['NMLeg', 'getNMLeg'], ['NVLeg', 'getNVLeg'], ['NYAssembly', 'getNYAssembly'], ['NYSenate', 'getNYSenate'], ['OHLeg', 'getOHLeg'], ['OKLeg', 'getOKLeg'], ['ORLeg', 'getORLeg'], ['ORLeg', 'getORLeg('], ['RILeg', 'getRILeg'], ['SCLeg', 'getSCLeg'], ['SDLeg', 'getSDLeg'], ['TNLeg', 'getTNLeg'], ['UTLeg', 'getUTLeg'], ['VALeg', 'getVALeg'], ['VTLeg', 'getVTLeg'], ['WALeg', 'getWALeg'], ['WILeg', 'getWILeg'], ['WVLeg', 'getWVLeg'], ['WYLeg', 'getWYLeg']]
    partyDict = {'d+r': 'Unknown', 'd': 'Democratic', 'r': 'Republican', '(R)': 'Republican', '(D)': 'Democratic', '(I)': 'Independent', 'R': 'Republican', 'D': 'Democratic', '': 'Unknown', 'I': 'Independent', 'Democrat': 'Democratic', 'Republican': 'Republican', 'Democratic': 'Democratic', 'Independent': 'Independent', 'U': 'Independent', '': 'Unknown', 'DFL': 'Democratic-Farmer Labor', 'Dem': 'Democratic', 'Rep': 'Republican'}
    parallelPull(scripts, partyDict)
    dictList = data
    legObject = {}
    for item in dictList:
        if str(item['District']) not in legObject.keys():
            legObject[str(item['District'])] = {str(item['Name'].lower().replace('.', '')): item}
        elif str(item['Name'].lower()) not in legObject[str(item['District'])].keys():
            legObject[str(item['District'])][str(item['Name'].lower().replace('.', ''))] = item
        else:
            print 'duplicates in Web', item['District'], item['Name']
    return legObject


def openCSV(location):
    dictList = []
    with open(location, 'r') as inputFile:
        drObject = DictReader(inputFile)
        for row in drObject:
            dictList.append(row)
    return dictList


def writeCSV(dictList, location, headers):
    with open(location, 'w') as outputFile:
        dwObject = DictWriter(outputFile, headers, restval='')
        dwObject.writeheader()
        for row in dictList:
            dwObject.writerow(row)


def checkLeg(webLeg, csvLeg):
    incorrectCSV = []
    for legislator in csvLeg:
        legName = str(legislator['Official Name'].lower().replace('.', ''))
        legDist = legislator['Office Name']
        if str(legDist) in webLeg.keys():
            if str(legName) in webLeg[legDist].keys():
                del webLeg[legDist][legName]

                if len(webLeg[legDist]) == 0:
                    del webLeg[legDist]
            else:
                incorrectCSV.append(legislator)
        else:
            print legDist, 'is missing'
            incorrectCSV.append(legislator)
    return webLeg, incorrectCSV


def suggestReplacements(unmatchedWeb, unmatchedCSV):
    suggestions = []
    for legislator in unmatchedCSV:
        suggestion = {}
        legName = legislator['Official Name'].lower()
        legDist = legislator['Office Name']
        if legDist in unmatchedWeb.keys():
            if legName not in unmatchedWeb[legDist].keys():
                if len(unmatchedWeb[legDist]) == 1:
                    suggestion = unmatchedWeb[legDist][unmatchedWeb[legDist].keys()[0]]
                    suggestion['UID'] = legislator['UID']
                    suggestion['oldName'] = legName
                else:
                    suggestion['UID'] = legislator['UID']
                    suggestion['District'] = legDist
                    suggestion['oldName'] = legName
                    suggestion['Name'] = str(unmatchedWeb[legDist].keys())
        else:
            suggestion['UID'] = legislator['UID']
            suggestion['District'] = legDist
            suggestion['oldName'] = legName
        testName = ''
        testOldName = ''
        if 'Name' in suggestion.keys():
            testName = suggestion['Name']
        if 'oldName' in suggestion.keys():
            testOldName = suggestion['oldName']
        if not ((testName == '' or re.search('([Vv][Aa][Cc][Aa][Nn][Tt])|([Dd][Ii][Ss][Tt][Rr][Ii][Cc][Tt])', testName)) and (testOldName == '' or re.search('([Vv][Aa][Cc][Aa][Nn][Tt])', testOldName))):
            suggestions.append(suggestion)
    return suggestions


def main():
    dropbox = os.environ['DROPBOX']
    startTime = time.time()
    webLeg = downloadLegislators()
    csvLeg = openCSV('{0}/noBIP/social_media_collection/office_holders/SL Office Holders.csv'.format(dropbox))
    unmatchedWeb, unmatchedCSV = checkLeg(webLeg, csvLeg)
    suggestedReplacements = suggestReplacements(unmatchedWeb, unmatchedCSV)
    writeCSV(suggestedReplacements, '{0}/noBIP/suggestions.csv'.format(dropbox), headers=['UID', 'District', 'oldName', 'Name', 'Party', 'Phone', 'Address', 'Website', 'Email', 'Facebook', 'Twitter', 'Youtube', 'DOB'])
    endTime = time.time()
    print 'completed in', endTime - startTime


if __name__ == '__main__':
    main()
