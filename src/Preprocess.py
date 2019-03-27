import os
import string
import xml.etree.ElementTree as ET
import json

types=[ 'Unk', 'Life', 'Conflict', 'Justice', 'Contact', 'Movement', 'Personnel', 'Transaction', 'Business']
subtypes=['Unk', 'Be-Born', 'Marry', 'Divorce', 'Attack', 'Demonstrate', 'Injure', 'Die', 'Transport',  'Transfer-Ownership', 'Transfer-Money', 'Meet', 'Phone-Write', 'Start-Position', 'End-Position', 'Nominate', 'Elect', 'Arrest-Jail', 'Pardon', 'Appeal', 'Acquit', 'Extradite', 'Execute', 'Fine', 'Sentence', 'Convict', 'Sue', 'Charge-Indict', 'Release-Parole', 'Trial-Hearing', 'End-Org', 'Declare-Bankruptcy', 'Start-Org', 'Merge-Org']

subDic={'Transport-Artifact': 'Transport', 'Transport-Person': 'Transport', 'Transaction': 'Transfer-Money', 'Broadcast':'Phone-Write',  'Correspondence': 'Phone-Write'}

def extractGoldACE(fileName):
	goldEv={}
	tree= ET.parse(fileName)
	root= tree.getroot()
	doc= root[0]
	for event in doc.findall('event'):
		type= event.get('TYPE')
		subtype= event.get('SUBTYPE')
		for mention in event.findall('event_mention'):
			seq= mention.find('anchor').find('charseq')
			predicateStart= int(seq.get('START'))
			predicateEnd = int(seq.get('END'))+1
			predicate= seq.text
			frames={}
			for arg in mention.findall('event_mention_argument'):
				seqArg= arg[0][0]
				argStart= int(seqArg.get('START'))
				argEnd= int(seqArg.get('END'))+1
				role= arg.get('ROLE')
				text= seqArg.text
				frames.update({role: text})
			goldEv.update({(predicateStart, predicateEnd): [predicate, frames, type, subtype]})
	return goldEv


def getSubtype(word):
    out = word.translate(string.maketrans("", ""), string.punctuation)
    out=out.lower()
    type= "Unk"
    for s in subtypes:
        sK= s.translate(string.maketrans("", ""), string.punctuation)
        sK= sK.lower()
        if sK== out:
            type= s
    for s in subDic.keys():
        sK= s.translate(string.maketrans("", ""), string.punctuation)
        sK= sK.lower()
        if sK== out:
            type= subDic[s]
    return type

def  writeF(lines, path):
    file= open(path+'/aaa.txt', 'w')
    for l in lines:
        if '#BeginOfDoc' in l:
            file.close()
            name= l.split(' ')[1][:-1]
            file= open(path+ name+ '.txt', 'w')
        file.write(l)
    file.close()


def getPlainText(file):
    f= open(file)
    text= f.read()
    f.close()
    plText=""
    index=0
    while index< len(text):
        char= text[index]
        if char== "<":
            while char!= ">":
                index+=1
                char= text[index]
            index+=1
        plText+= text[index]
        index+=1
    return plText

#Just Use StanfordCore NLP output tokens to get them!

def getTokensStanford(fileName):
    jsonfile = open('/Users/evangeliaspiliopoulou/Desktop/DataVersion2/TAC_NW_2016/outputStanford/'+ fileName+ '.json', 'r')
    jsonstr = jsonfile.read()
    data = json.loads(jsonstr)
    tokens={}
    sentenceSpans={}
    sentenceMap={}
    words=[]
    for i in range(len(data['sentences'])):
        sentTokens= data['sentences'][i]['tokens']
        sentenceStart= sentTokens[0]["characterOffsetBegin"]
        sentenceEnd=  sentTokens[len(sentTokens)-1]["characterOffsetEnd"]
        sentenceSpans.update({i: (sentenceStart, sentenceEnd)})
        match={}
        for index in range(len(sentTokens)):
            token= sentTokens[index]['originalText']
            #pos=  str(sentTokens[index]['pos'])
            ind= int(sentTokens[index]['index'])
            start= int(sentTokens[index]["characterOffsetBegin"])
            end= int(sentTokens[index]["characterOffsetEnd"])
            tokens.update({(start, end): [ind-1, token]})
            words.append(token)
            match.update({ind: (start, end)})
        sentenceMap.update({i: match})
    return words, tokens, sentenceSpans

def keyFilter(keys, sent):
    spans = list(keys)
    spans.sort()
    start= sent[0]
    end= sent[1]
    allKeys=[]
    for s, e in spans:
        if s>start-2 and e<end+2:
            allKeys.append((s, e))
    return allKeys


def processFrameNet():
    EventFrames={}
    file= '/Users/evangeliaspiliopoulou/Desktop/fndata/frRelation.xml'
    tree= ET.parse(file)
    root= tree.getroot()
    EventFrames={}
    interest= ['Inheritance', 'Subframe', 'See_also']
    relTypes= root.findall('{http://framenet.icsi.berkeley.edu}frameRelationType')
    for type in relTypes:
        typeName= type.get('name')
        if typeName== 'Metaphor':
            rels= type.findall('{http://framenet.icsi.berkeley.edu}frameRelation')
            for relation in rels:
                superRel= relation.get('superFrameName')
                subRel= relation.get('subFrameName')
                print(subRel)
                if subRel in EventFrames.keys():
                    ex= EventFrames[subRel]
                    ex.append(typeName)
                    EventFrames[subRel]= ex
                else:
                    EventFrames[subRel]= [typeName]
    relTypes= root.findall('{http://framenet.icsi.berkeley.edu}frameRelationType')
    for type in relTypes:
        typeName= type.get('name')
        if typeName== 'Inheritance3':
            rels= type.findall('{http://framenet.icsi.berkeley.edu}frameRelation')
            for relation in rels:
                superRel= relation.get('superFrameName')
                subRel= relation.get('subFrameName')
                if superRel== 'Event':
                    if subRel in EventFrames.keys():
                        ex= EventFrames[subRel]
                        ex.append(typeName)
                        EventFrames[subRel]= ex
                    else:
                        EventFrames[subRel]= [typeName]

def fix(file):
    exc=0
    f=open('/Users/evangeliaspiliopoulou/Desktop/SemaforTACKBP2016/'+file+'.txt')
    text=f.read()
    textList= eval(text)
    f.close()
    targets={}
    for frame in textList:
        targetDetails = frame["target"]
        type = str(targetDetails["name"])
        s = int(targetDetails["spans"][0]["start"])
        e = int(targetDetails["spans"][0]["end"])
        frText = str(targetDetails["spans"][0]["text"])
        targets[(s, e)] = [type, frText]
    k= targets.keys()
    keys= list(k)
    keys.sort()
    words, tokens, sentences= getTokensStanford(file)
    output=[]
    offsets=[]
    # sentOutput={}
    spans= tokens.keys()
    spans= list(spans)
    spans.sort()
    prevIndex = 0
    curr=0
    for k in keys:
        term = targets[k][1]
        if term not in words[prevIndex:]:
            #print("Exception " + term)
            exc+=1
        else:
            index = words[prevIndex:].index(term) + prevIndex
            prevIndex = index + 1
            span= spans[index]
            offsets.append({"surface": term, "offset": [span[0], span[1]]})
            output.append({"target": {"name": targets[k][0],
                                      "spans": [{"start": curr, "end": curr + 1, "text": term}]}})
            curr+=1
    print("Exceptions")
    print(exc)
    print(len(output))
    return output, offsets, words