"""
Script used for the segmentation of czech corpora into
Linear Dependency Segments
"""
import conll3
import pandas as pd
import re

def is_finite_verb(tree, i):
    """
    Are considered finite verbs tokens with xpos:
    - Vc
    - Vs
    - VB
    - Vi
    - And Vp when their parent is not an AUX (otherwise the auxiliary is head of the clause)
    """
    if tree[i]["xpos"][:2] in ["Vc", "Vs", "VB", "Vi"]:
        return True
    elif tree[i]["xpos"][:2] == "Vp":
        idgov, _ = tree.idgovRel(i)
        if idgov == 0:
            return True
        else:
            upos_gov = tree[idgov]["tag"]
            if upos_gov != "AUX":
                return True
            else:
                return False
    elif tree[i]["tag"] == "AUX":
        for k in tree[i]['kids']:
            if tree[k]["xpos"][:2] == "Vp":
                return True
        return False
    else:
        return False

def is_finite_verb_or_sconj(tree,i):
    """
    Clauses begin with a finite verbe (not preceded by sconj) or a SCONJ that governs a finite verb
    """
    if tree[i]["tag"] == "SCONJ":
        kids = tree[i]["kids"]
        for k in kids:
            if is_finite_verb(tree, k):
                return True
        return False
    elif is_finite_verb(tree,i):
        idgov, _ = tree.idgovRel(i)
        if idgov == 0:
            return True
        elif tree[idgov]["tag"] == "SCONJ":
            return False
        else:
            return True

def get_descendants(tree, i):
    """
    Given a tree and an id finds all descendants (recursive)
    in:
    - object of type conll3.Tree
    out:
    [1,3,4]
    """
    descendants = []
    children = tree.get_kids(i)
    descendants.extend(children)
    if children:
        for c in children:
            x = get_descendants(tree, c)
            if x:
                descendants.extend(x)
    return descendants

def get_descendants_until_Fin_Verb(tree, i):
    """
    Given a tree and an id finds all descendants (recursive).
    Stop when you encounter a Finite Verb
    This is used to segment into clauses

    in:
    - object of type conll3.Tree
    out:
    [1,3,4]
    """
    descendants = []
    children = tree.get_kids(i)
    children = [c for c in children if not is_finite_verb_or_sconj(tree, c)]
    descendants.extend(children)
    if children:
        for c in children:
            x = get_descendants_until_Fin_Verb(tree, c)
            if x:
                x = [z for z in x if not is_finite_verb_or_sconj(tree, z)]
                descendants.extend(x)
    return descendants


def clause_segmentation(tree):
    clauses = []
    tree.addkids()
    fin_verbs = [i for i in tree if is_finite_verb_or_sconj(tree, i)]
    if not fin_verbs:
        return []
    else:
        for root in fin_verbs:
            descendants = get_descendants_until_Fin_Verb(tree, root)
            clause = sorted(descendants+[root])
            clauses.append(clause)
        return clauses

def is_syntactic_bigram(tree, id_1, id_2):
    idgov_1, _ = tree.idgovRel(id_1)
    if idgov_1 == id_2:
        return True
    idgov_2, _ = tree.idgovRel(id_2)
    if idgov_2 == id_1:
        return True
    return False

def is_complete(tree):
    for i in tree:
        idgov, _ = tree.idgovRel(i)
        if idgov == -1:
            return False
    return True


def syntactically_linked_ngrams_1(tree, clause):
    """

    segments are cut off when one word isn't linked to its right neighbour
    in the linear order of the clause
    """
    # initialization
    segments = [[clause[0]]]
    for i in range(1, len(clause)):
        # print(i)
        if is_syntactic_bigram(tree, clause[i], clause[i-1]):
            segments[-1].append(clause[i])
        else:
            segments.append([clause[i]])
    return segments


def syntactically_linked_ngrams_2(tree, clause):
    """

    segments are cut off when one word isn't linked to its right neighbour
    in the linear order of the sentence
    """
    # initialization
    segments = [[clause[0]]]
    for i in range(1, len(clause)):
        if clause[i-1]+1 == clause[i] and is_syntactic_bigram(tree, clause[i], clause[i-1]):
            segments[-1].append(clause[i])
        else:
            segments.append([clause[i]])
    return segments




## 1 - Small example to show how the functions work

# conll_example = """
# # generator = UDPipe 2, https://lindat.mff.cuni.cz/services/udpipe
# # udpipe_model = czech-pdt-ud-2.6-200830
# # udpipe_model_licence = CC BY-NC-SA
# # newdoc
# # newpar
# # sent_id = 1
# # text = Včera jsem řekla, že Jana je nemocná.
# 1	Včera	včera	ADV	Db-------------	_	3	advmod	_	TokenRange=0:5
# 2	jsem	být	AUX	VB-S---1P-AA---	Mood=Ind|Number=Sing|Person=1|Polarity=Pos|Tense=Pres|VerbForm=Fin|Voice=Act	3	aux	_	TokenRange=6:10
# 3	řekla	říci	VERB	VpQW---XR-AA---	Aspect=Perf|Gender=Fem,Neut|Number=Plur,Sing|Polarity=Pos|Tense=Past|VerbForm=Part|Voice=Act	0	root	_	SpaceAfter=No|TokenRange=11:16
# 4	,	,	PUNCT	Z:-------------	_	8	punct	_	TokenRange=16:17
# 5	že	že	SCONJ	J,-------------	_	8	mark	_	TokenRange=18:20
# 6	Jana	Jana	PROPN	NNFS1-----A----	Case=Nom|Gender=Fem|NameType=Giv|Number=Sing|Polarity=Pos	8	nsubj	_	TokenRange=21:25
# 7	je	být	AUX	VB-S---3P-AA---	Mood=Ind|Number=Sing|Person=3|Polarity=Pos|Tense=Pres|VerbForm=Fin|Voice=Act	8	cop	_	TokenRange=26:28
# 8	nemocná	nemocný	ADJ	AAFS1----1A----	Case=Nom|Degree=Pos|Gender=Fem|Number=Sing|Polarity=Pos	3	ccomp	_	SpaceAfter=No|TokenRange=29:36
# 9	.	.	PUNCT	Z:-------------	_	3	punct	_	SpaceAfter=No|TokenRange=36:37
# """

# # transform the conll into a tree
# tree_example = conll3.conll2tree(conll_example)

# # remove the punctuation
# tree_example = conll3.unpunctATree_2(tree_example)

# print sentence
# print(tree_example.sentence())

# # segment into clauses
# clauses = clause_segmentation(tree_example)
# print("clause segmentation: ", clauses)

# # segment the 2nd clause into linear dependency segments (method 1)
# segments = syntactically_linked_ngrams_1(tree_example, clauses[1])
# print("2nd clause segmented into LDS using method 1: ", segments)

# # segment the 2nd clause into linear dependency segments (method 2)
# segments = syntactically_linked_ngrams_2(tree_example, clauses[1])
# print("2nd clause segmented into LDS using method 2: ", segments)


## 2- Main program : create a tsv file with the clause segmentation and linear dependency segmentation


# # folder with the conllu files
# input_folder = "../czech-sud-merged/"

# # create the list of trees
# new_trees = conll3.conllFolder2trees_unpuncted(input_folder)

# # method 1 :
# output_name_1 = "segmentation_results_sud_method1_v2_pdt_fictree.tsv"
# results = []
# clause_c = 0
# segment_c = 0

# for t_id, t in enumerate(new_trees):
#     if not is_complete(t):
#         continue
#     results.append(["sentence", t_id, "None", "None", t.sentence()])
#     clauses = clause_segmentation(t)

#     # this will print sentences with no clauses
#     if not clauses:
#         print(t.sentence())
    
#     for c in clauses:
#         results.append(["clause", t_id, clause_c, "None", " ".join([t[x]["t"] for x in c])])
#         # syntactically linked bigrams (neighbours in clause)
        
#         segments = syntactically_linked_ngrams_1(t, c)
#         # print(segments)
#         for s in segments:
#             results.append(["segment", t_id, clause_c, segment_c, " ".join([t[x]["t"] for x in s])])
#             segment_c += 1 
#         clause_c += 1


# # output the results of method 1
# df = pd.DataFrame.from_records(results, columns=["type", "sentence_id", "clause_id", "segment_id", "text"])
# df.to_csv(output_name_1, sep="\t", index=False)

# # method 2 
# output_name_2 = "segmentation_results_sud_method2_v2_pdt_fictree.tsv"
# results = []
# clause_c = 0
# segment_c = 0

# for t_id, t in enumerate(new_trees):
#     if not is_complete(t):
#         continue
#     results.append(["sentence", t_id, "None", "None", t.sentence()])
#     clauses = clause_segmentation(t)

#     # this will print sentences with no clauses
#     if not clauses:
#         print(t.sentence())
    
#     for c in clauses:
#         results.append(["clause", t_id, clause_c, "None", " ".join([t[x]["t"] for x in c])])
#         # syntactically linked bigrams (neighbours in clause)
        
#         segments = syntactically_linked_ngrams_2(t, c)
#         # print(segments)
#         for s in segments:
#             results.append(["segment", t_id, clause_c, segment_c, " ".join([t[x]["t"] for x in s])])
#             segment_c += 1 
#         clause_c += 1


# # output the results of method 2
# df = pd.DataFrame.from_records(results, columns=["type", "sentence_id", "clause_id", "segment_id", "text"])
# df.to_csv(output_name_2, sep="\t", index=False)