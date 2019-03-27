
import json
import os
import time
import ast
import re
import enchant
import pdb


startTime= time.time()
verbTags= ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
nounTags=['NN', 'NNS', 'JJ', 'NNP']
depTypes= {"nsubj": "Agent" , "iobj": "Theme", "nsubjpass": "Patient", "dobj": "Patient", "xsubj": "Agent"}

class EventDetector:
    def __init__(self, dataset, opendomain=False):
        self.dataset=dataset
        self.opendomain= opendomain
        self.EvFrames= self.getEventFrames()
        f=open('../data/VerbSemRoles.txt')
        self.verbSemRoles= ast.literal_eval(f.read())
        f.close()
        f = open('../data/NounSemRoles.txt')
        self.nounSemRoles = ast.literal_eval(f.read())
        f.close()
        f = open('../data/OntFrameArg.txt')
        self.frameArgs = ast.literal_eval(f.read())
        f.close()

    def getInfoFromJsonStanford(self, fileName):
        jsonfile = open('../data/'+ self.dataset+ '/outputStanford/'+ fileName+ '.json', 'r')
        jsonstr = jsonfile.read()
        jsonfile.close()
        data = json.loads(jsonstr)
        tokens={}
        sentenceSpans={}
        times={}
        locations={}
        sentenceMap={}
        for i in range(len(data['sentences'])):
            sentTokens= data['sentences'][i]['tokens']
            sentenceStart= sentTokens[0]["characterOffsetBegin"]
            sentenceEnd=  sentTokens[len(sentTokens)-1]["characterOffsetEnd"]
            sentenceSpans.update({i: (sentenceStart, sentenceEnd)})
            mapping={}
            prevLocation= (0, 0)
            prevTime= (0, 0)
            for index in range(len(sentTokens)):
                token= sentTokens[index]['originalText']
                pos=  str(sentTokens[index]['pos'])
                ind= int(sentTokens[index]['index'])
                start= int(sentTokens[index]["characterOffsetBegin"])
                end= int(sentTokens[index]["characterOffsetEnd"])
                ner= str(sentTokens[index]['ner'])
                tokens.update({(start, end): [token, pos]})
                mapping.update({ind: (start, end)})
                try:
                    if ner== 'LOCATION'and not ("href" in str(token)):
                        if (start-prevLocation[0] <4) and (prevLocation in locations.keys()):
                            #previous= locations[prevLocation]
                            textLoc= locations[prevLocation]+ ' '+ token
                            del locations[prevLocation]
                            locations.update({(prevLocation[0], end): textLoc})
                            prevLocation= (prevLocation[0], end)
                        else:
                            locations.update({(start, end):str(token)})
                            prevLocation=(start, end)
                    elif (ner=='DATE' or ner=='DURATION') and not ("href" in str(token)):
                        if (start - prevTime[0] < 4) and (prevTime in times.keys()):
                            textTime = str(times[prevTime])+ ' '+str(token)
                            del times[prevTime]
                            times.update({(prevTime[0], end): textTime})
                            prevTime = (prevTime[0], end)
                        else:
                            times.update({(start, end): str(token)})
                            prevTime = (start, end)
                except:
                    pass
            sentenceMap.update({i: mapping})
        dependencies = {}
        for i in range(len(data['sentences'])):
            depCurr= data['sentences'][i]['enhancedPlusPlusDependencies']
            sentTokens= sentenceMap[i]
            for dependency in depCurr:
                if dependency['dep']!= "ROOT":
                    govern= sentTokens[int(dependency['governor'])]
                    dependent= sentTokens[int(dependency['dependent'])]
                    try:
                        dependentText= dependency['dependentGloss']
                    except:
                        print(dependency)
                        dependentText="unk"
                    dep = dependency['dep']
                    if govern in dependencies.keys():
                        list= dependencies[govern]
                        list.update({dependent: [dep, dependentText]})
                        dependencies.update({govern: list})
                    else:
                        list={dependent: [dep, dependentText]}
                        dependencies.update({govern: list})
        return tokens, dependencies, sentenceSpans, times, locations

    def getInfoFromSemafor(self, fileName):
        file= open('../data/'+ self.dataset+ '/outputSemafor/'+ fileName+'.json')
        text= file.read()
        file.close()
        allText= text.split('\n')
        targets={}
        for sent in allText:
            newText=str(sent)
            if 'target' in newText:
                data= json.loads(newText)
                tokens=[]
                for i in range(len(data['offsets'])):
                    offset= data['offsets'][i]['offset']
                    start= int(offset[0])
                    end= int(offset[1])
                    tokens.append((start, end))
                tokens.sort()
                for i in range(len(data['frames'])):
                    details= data['frames'][i]
                    text= str(details['target']['spans'][0]['text'])
                    start= int(details['target']['spans'][0]['start'])
                    end= int(details['target']['spans'][0]['end'])
                    type= str(details['target']['name'])
                    span1= tokens[start]
                    span2= tokens[end-1]
                    span= (span1[0], span2[1])
                    targets.update({span: [type, text, {}]})
        return targets

    def findAllNouns(self, stanTokens):
        nouns={}
        keys= list(stanTokens.keys())
        keys.sort()
        for curr in range(len(keys)):
            index= keys[curr]
            text= stanTokens[index][0]
            pos= stanTokens[index][1]
            if pos in nounTags:
                prev= 'Start'
                next= 'End'
                if curr>1:
                    try:
                        prev= str(stanTokens[keys[curr-2]][0])+ " "+ str(stanTokens[keys[curr-1]][0])
                    except:
                        prev='unk'
                if curr<len(stanTokens)-2:
                    try:
                        next = str(stanTokens[keys[curr + 1]][0]) +" " +str(stanTokens[keys[curr + 2]][0])
                    except:
                        next='unk'
                nouns.update({index: [text, prev, next]})
        return nouns

    def findAllVerbs(self, stanTokens):
        verbs={}
        keys= list(stanTokens.keys())
        keys.sort()
        for curr in range(len(keys)):
            index= keys[curr]
            text= stanTokens[index][0]
            pos= stanTokens[index][1]
            if pos in verbTags:
                prev= 'Start'
                next= 'End'
                if curr>0:
                    try:
                        prev= str(stanTokens[keys[curr-2]][0])+ " "+ str(stanTokens[keys[curr-1]][0])
                    except:
                        prev= 'unk'
                if curr<len(stanTokens)-1:
                    try:
                        next= str(stanTokens[keys[curr+1]][0]) +" " +str(stanTokens[keys[curr + 2]][0])
                    except:
                        next='unk'
                verbs.update({index: [text, prev, next]})
        return verbs

    def filterTargetsPOS(self, heads, allTargets):
        events = {}
        for span in heads.keys():
            if span in allTargets.keys():
                events.update({span: allTargets[span]})
        return events


    def filterTargets(self, allTargets, verbs, nouns):
        target1= self.filterTargetsPOS(verbs, allTargets)
        target2 = self.filterTargetsPOS(nouns, allTargets)
        target= self.merge(target1, target2)
        events={}
        for span in target.keys():
            details= target[span]
            frame= details[0]
            if frame in self.EvFrames.keys():
                details.append(self.EvFrames[frame])
                events.update({span: details})
        return events

    def filterTargetsOntology(self, targets, posGroup, ontology):
        newEvents = {}
        events= self.filterTargetsPOS(posGroup, targets)
        for span in events:
            typeFr = str(events[span][0])
            for type in ontology.keys():
                for subtype in ontology[type].keys():
                    listTypes = ontology[type][subtype]
                    if typeFr in listTypes:
                        event = [(type, subtype), events[span][1], events[span][2], typeFr]
                        newEvents.update({span: event})
        return newEvents

    def getEventFrames(self):
        EvFrames={}
        f= open('../data/eventDict.txt')
        lines= f.readlines()
        for line in lines:
            l=line.split('\t')
            frRel= l[1].split(',')[0]
            EvFrames.update({l[0]: frRel})
        return EvFrames

    def completeAllFrames(self, allEvents, deps):
        newEvents = {}
        for key in allEvents.keys():
            frame = allEvents[key]
            newFrame = self.completeFrame(frame[2], deps, key)
            finalFrame = frame[2]
            type, subtype = frame[0]
            frameStructure = self.frameArgs[type][subtype]
            filled = []
            for depKey in newFrame.keys():
                filled.append(newFrame[depKey][0])
            i = 0
            j = 0
            if len(frameStructure) == 1:  ##Two agents
                i = 1
            if len(frameStructure) < 3:
                j = 1
            for depKey in newFrame.keys():
                role, text = newFrame[depKey]
                if role == 'Agent':
                    finalFrame.update({depKey: [frameStructure[0], text]})
                elif role == 'Patient':
                    finalFrame.update({depKey: [frameStructure[1 - i], text]})
                elif 'Patient' in filled:
                    finalFrame.update({depKey: [frameStructure[2 - j - i], text]})  # +i??
                else:
                    finalFrame.update({depKey: [frameStructure[1 - i], text]})
            frame[2]=finalFrame
            newEvents.update({key: frame})
        return newEvents

    def completeFrame(self, frame, deps, frameKey):
        newFrame = {}
        for govern in deps.keys():
            if str(govern) == str(frameKey):
                for dependent in deps[govern].keys():
                    dep = str(deps[govern][dependent][0])
                    if dep in depTypes.keys():
                        (startDep, endDep) = dependent
                        found = False
                        for (start, end) in frame.keys():
                            if (start >= startDep and start <= endDep) or (end >= startDep and end <= endDep) or (
                                    start <= startDep and end >= endDep):
                                found = True
                        if not found:
                            entity = self.completeFrameEnt(dependent, deps[govern][dependent][1], deps)
                            newFrame.update({dependent: [depTypes[dep], entity]})
        return newFrame

    def completeFrameEnt(self, entKey, entity, deps):
        newEnt = entity
        for key in deps.keys():
            if str(entKey) == str(key):
                for dependent in deps[key].keys():
                    dep = str(deps[key][dependent][0])
                    if dep == 'compound':
                        if int(key[0]) < int(dependent[0]):
                            newEnt = newEnt + " " + deps[key][dependent][1]
                        else:
                            newEnt = deps[key][dependent][1] + " " + newEnt
        return newEnt

    def detectEvents(self):
        files = os.listdir('../data/'+ self.dataset+ '/outputStanford')
        total=0.0
        for fileName in files:
            print(fileName)
            if not ("DS_Store" in fileName):
                name = fileName[:-5]
                if 'outputs' not in os.listdir('../data/'+ self.dataset):
                    os.mkdir('outputs')
                    os.mkdir('outputs/events')
                outFile = open('../data/'+ self.dataset+'/outputs/events/' + name + '.txt', 'w')
                targets = self.getInfoFromSemafor(name)
                tokens, dependencies, sentenceSpans, times, locations = self.getInfoFromJsonStanford(name)
                allVerbs = self.findAllVerbs(tokens)
                allNouns = self.findAllNouns(tokens)
                if self.opendomain:
                    events= self.filterTargets(targets, allVerbs, allNouns)
                else:
                    nominal_events= self.filterTargetsOntology(targets, allNouns, self.nounSemRoles)
                    verbal_events= self.filterTargetsOntology(targets, allVerbs, self.verbSemRoles)
                    verbal_events= self.completeAllFrames(verbal_events, dependencies)
                    events= self.merge(nominal_events, verbal_events)
                index=1
                total+= len(events.keys())
                for span in events.keys():
                    outFile.write('EvaEDSystem\t'+ str(index)+ '\t'+ str(span[0])+','+ str(span[1]) +'\t'+ events[span][1]+ '\t' + events[span][0][0]+'.'+events[span][0][1]+ '\t'+ events[span][3] + '\t' + str(events[span][2])+ '\n')
                    index+=1
                outFile.close()
            else:
                print("Error in file processing")

    def merge(self, events1, events2):
        events=events2
        for index in events1.keys():
            if index not in events2.keys():
                events.update({index: events1[index]})
        return events



detector= EventDetector('ACE2005_nw')
detector.detectEvents()