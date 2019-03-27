# Event Detection Using Frame-Semantic Parser

<br> This Repo contains the code for Event Detection associated with the paper: </br>

Spiliopoulou, Evangelia, Eduard Hovy, and Teruko Mitamura. "Event detection using frame-semantic parser." Proceedings of the Events and Stories in the News Workshop. 2017.

http://www.aclweb.org/anthology/W17-2703

In order to run the code, you need to preprocess the data with Semafor and Stanford CoreNLP and place them in the corresponding folders (data/project_Name/outputSemafor and data/project_Name/outputStanford). The data that the paper was tested on is from ACE 2005, which is not provided here due to data sharing policies.

The output of the code is a set of txt files (1 per input file) that contain the generated events, their types/ subtypes (as defined by the ACE 2005 Ontology) and their corresponding arguments. This output can be used as features in several ML algorithms in order to refine the generated events, as described in the paper.

If you use parts of this code, please cite our paper.
