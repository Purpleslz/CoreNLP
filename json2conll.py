# -*- coding:utf-8 -*-

from __future__ import print_function
import json
import sys

__author__ = "Zhenhua.Fan"
__date__ = "2017-08-03"

"""
    Convert a json file to CoNLL format.
    Format:
        Column  1: Document ID
        Column  2: Part Number
        Column  3: Word Number
        Column  4: Word itself
        Column  5: Part-of-Speech
        Column  6: Parse bit
        Column  7: Predicate lemma
        Column  8: Predicate Frameset ID
        Column  9: Word sense
        Column 10: Speaker / Author
        Column 11: Named Entities
        Column 12: N Predicate Arguments
                   N Coreference
"""

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def compare_mentions(a, b):
    """
        Compare two mentions.
        if a < b returns 1
        if a = b returns 0
        if a > b returns -1
    """
    if a["SentNum"] != b["SentNum"]:
        if a["SentNum"] < b["SentNum"]:
            return 1
        else:
            return -1
    elif a["StartIndex"] != b["StartIndex"]:
        if a["StartIndex"] < b["StartIndex"]:
            return 1
        else:
            return -1
    elif a["EndIndex"] != b["EndIndex"]:
        # if a.EndIndex > b.EndIndex returns 1
        if a["EndIndex"] > b["EndIndex"]:
            return 1
        else:
            return -1
    else:
        return 0

def add_mention_item(dic, key1, key2, val):
    # add item to dict
    if key1 not in dic:
        dic[key1] = dict()
    if key2 not in dic[key1]:
        dic[key1][key2] = []
    dic[key1][key2].append(val)

def process_parse(parse, nb_tokens):
    ret = []
    token_count = 0
    stack = []
    last_bracket = 'none'
    token = ""

    for ch in parse:
        if ch == "(":
            if token:
                stack.append(token)
                token = ""
            last_bracket = "("
            token = ""
        elif ch == ")":
            if token:
                stack.append(token)
                token = ""
            
            if last_bracket == '(':
                token_count += 1

                # pop out token itself and its pos
                stack.pop()
                stack.pop()
                
                prefix = ""
                while stack:
                    prefix = ''.join(('(', stack[-1], prefix))
                    stack.pop()
                ret.append(''.join((prefix, "*")))
            else:
                ret[-1] = ''.join((ret[-1], ")"))
                    
            last_bracket = ")"
            token = ""
        elif (ch == '\n') or (ch == ' '):
            # split symbol
            if token:
                stack.append(token)
            token = ""
        else:
            token = ''.join((token, ch))

    # token_count is supposed to be the same as nb_tokens
    assert token_count == nb_tokens

    return ret
    
def mention_str(m_begin, m_end, m_begin_end, sent_index, token_index):
    ret = ""

    # the begin of a mention add one ( before it
    if sent_index in m_begin:
        if token_index in m_begin[sent_index]:
            for entity_name in m_begin[sent_index][token_index]:
                if ret:
                    ret = ''.join((ret, '|'))
                ret = ''.join((ret, '(', entity_name))

    # single token mention add brackets around it
    if sent_index in m_begin_end:
        if token_index in m_begin_end[sent_index]:
            for entity_name in m_begin_end[sent_index][token_index]:
                if ret:
                    ret = ''.join((ret, '|'))
                ret = ''.join((ret, '(', entity_name, ')'))

    # the end of a mention only add one ) after it
    if sent_index in m_end:
        if token_index in m_end[sent_index]:
            for entity_name in m_end[sent_index][token_index]:
                if ret:
                    ret = ''.join((ret, '|'))
                ret = ''.join((ret, entity_name, ')'))

    # there is no mention here
    if not ret:
        ret = '-'
    return ret

def convert(doc_json, fo):
    """
        Arguments:
            doc_json: content in json format
            fo: target file object

        Returns:
            None
    """
    mentions = []

    # extract all entities' mentions first
    # singleton clusters are not mentioned here
    # so coref_name is not start with 1
    # all 1-based indices -> 0-based indices
    # [StartIndex, EndIndex) -> [StartIndex, EndIndex - 1]
    for coref_name, all_content in doc_json["corefs"].items():
        for content in all_content:
            temp = {
                    "EntityName": coref_name,
                    "SentNum": int(content["sentNum"]) - 1,
                    "StartIndex": int(content["startIndex"]) - 1,
                    "EndIndex": int(content["endIndex"]) - 1 - 1,
                    }
            mentions.append(temp)

    # resort mentions
    mentions.sort(key=cmp_to_key(compare_mentions))

    # add mentions.
    m_begin = dict()
    m_end = dict()
    m_begin_end = dict()
    for mention in mentions:
        if mention["StartIndex"] == mention["EndIndex"]:
            add_mention_item(m_begin_end, mention["SentNum"], mention["StartIndex"], mention["EntityName"])
        else:
            add_mention_item(m_begin, mention["SentNum"], mention["StartIndex"], mention["EntityName"])
            add_mention_item(m_end, mention["SentNum"], mention["EndIndex"], mention["EntityName"])


    # sentences
    sents = []

    # osent stands for original sentence
    for osent in doc_json["sentences"]:
        sent = []

        # str2list
        parse = osent["parse"]
        parse = process_parse(parse, len(osent["tokens"]))

        lastner = "O"

        # otoken stands for original token
        for token_index, otoken in enumerate(osent["tokens"]):
            otoken["parse"] = parse[token_index]
            if otoken["ner"] == lastner:
                lastner = otoken["ner"]
                otoken["ner"] = "*"
            else:
                if lastner != "O":
                    # single token NEs are not contain "*" symbol
                    if sent[-1]["ner"].startswith('('):
                        sent[-1]["ner"] = ''.join((sent[-1]["ner"][:-1], ")"))
                    else:
                        sent[-1]["ner"] = ''.join((sent[-1]["ner"], ")"))
                lastner = otoken["ner"]
                
                if otoken["ner"] != "O":
                    otoken["ner"] = ''.join(('(', otoken["ner"], '*'))
                else:
                    otoken["ner"] = "*"
            sent.append(otoken)

        # ner in the last token
        if lastner != "O":
            # single token NEs are not contain "*" symbol
            if sent[-1]["ner"].startswith('('):
                sent[-1]["ner"] = ''.join((sent[-1]["ner"][:-1], ")"))
            else:
                sent[-1]["ner"] = ''.join((sent[-1]["ner"], ")"))

        sents.append(sent)

    # write to file

    # doc id = file name
    # part number = 0 fixed
    docid = doc_json["docId"]
    partnb = "000"

    # begin of document
    fo.write("#begin document ({}); part {}\n".format(docid, partnb))

    # osent stands for original sentence
    for sent_index, sent in enumerate(sents):
        for token_index, token in enumerate(sent):
            column = []

            # Column  1: Document ID
            column.append(docid)
            # Column  2: Part Number
            # remove trailing zeroes
            column.append(str(int(partnb)))
            # Column  3: Word Number
            column.append(str(token_index))
            # Column  4: Word itself # attention: word is not the same as originalText
            # example: "(" - > -LBS- 
            if token["word"]:
                column.append(token["word"])
            else:
                column.append("-")
            # Column  5: Part-of-Speech
            if token["pos"]:
                column.append(token["pos"])
            else:
                column.append("-")
            # Column  6: Parse bit
            if token["parse"]:
                column.append(token["parse"])
            else:
                column.append("-")
            # Column  7: Predicate lemma
            if token["lemma"]:
                # display lemma only when it is different with word
                if token["lemma"] != token["word"]:
                    column.append(token["lemma"])
                else:
                    column.append("-")
            else:
                column.append("-")
            # Column  8: Predicate Frameset ID
            # TODO: figure out what Frameset ID is
            column.append("-")
            # Column  9: Word sense
            # TODO: figure out what Word sense is
            column.append("-")
            # Column 10: Speaker / Author
            if token["speaker"]:
                column.append(token["speaker"])
            else:
                column.append("-")
            # Column 11: Named Entities
            if token["ner"] == "O":
                column.append("*")
            else:
                column.append(token["ner"])
            # Column 12: N Predicate Arguments
            #            N Coreference
            column.append(mention_str(m_begin, m_end, m_begin_end, sent_index, token_index))

            # write to file
            fo.write('\t'.join(column))
            fo.write('\n')

        # one empty line after each sentence
        fo.write("\n")

    # end of document
    fo.write("#end document\n")

    # return None
    return None

if __name__ == "__main__":
    try:
        json_file = sys.argv[1]
    except IndexError:
        print("USAGE: python {} json_file [target_file]".format(sys.argv[0]))
        print("target_file is json_file's name + .conll by default")
        exit(1)

    try:
        target_file = sys.argv[2]
    except IndexError:
        target_file = ''.join((json_file, '.conll'))
        print("target_file =", target_file)

    with open(json_file, 'r') as jsonf:
        js = json.load(jsonf)

    with open(target_file, 'w') as f:
        convert(js, f)
