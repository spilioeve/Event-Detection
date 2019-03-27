import xml.etree.ElementTree as ET
import os



def score(files, path, fPath, threshold):
	avgR = 0.0
	avgP = 0.0
	totalPos = 0.0
	totalGold = 0.0
	totalOut = 0.0
	totalTypes = 0.0
	totalSubtypes = 0.0
	for file in files:
		correct=0.0
		out=0.0
		targets=[]
		gold= extractGoldACE(path+'/goldEval/'+file[:-4]+'.apf.xml')
		goldKeys=gold.keys()
		totalGold+= len(goldKeys)
		outF= open(fPath + '/' +file)
		output= outF.readlines()
		outF.close()
		for line in output:
			items= line.split('\t')
			if len(items)> 5:
				span= items[3]
				span1, span2= span.split(',')
				score=0.5
				typeSubtype= items[5] ###Fix that
				if len(items)>10:
					score= items[11]
				if float(score) > threshold and (span not in targets):
					totalOut+=1
					out+=1
					for g in goldKeys:
						if span1==str(g[0]) and span2== str(g[1]):
							totalPos+=1
							correct+= 1.0
					targets.append(span)
		# avgR+= correct/len(goldKeys)
		# avgP+= correct/out

	print("Total Precision, Recall, F1 (micro)")
	print(totalPos/ totalOut, totalPos/totalGold, 2* totalPos/(totalGold+ totalOut), totalOut, totalGold)
	print("Total Type, Subtypes")
	print(totalTypes/len(files), totalSubtypes/len(files))
	print("Avg Precision, Recall, F1 (macro)")
	#print avgP, avgR, 2* (avgP* avgR)/ (avgP + avgR)

path='dataACE'
#filePath= '/Users/evangeliaspiliopoulou/Desktop/EventEval/MergeEvents/dataACETest/merged/nuggets'
#filePath= '/Users/evangeliaspiliopoulou/Desktop/EventEval/MergeEvents/dataACETest/hector/nuggets'
filePath='/Users/evangeliaspiliopoulou/Desktop/EventEval/MergeEvents/dataACETest/merged/nuggets'

files= os.listdir(filePath)
if '.DS_Store' in files:
	score(files[1:], path, filePath, 0.0)
else:
	score(files, path, filePath, 0.0)
