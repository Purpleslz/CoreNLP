# -*- coding:utf-8 -*-

from __future__ import print_function
import json
import os
import sys

from json2conll import add_mention_item, cmp_to_key, compare_mentions, convert, mention_str, process_parse

__author__ = "Zhenhua.Fan"
__date__ = "2017-08-03"

"""
    Convert all json files in the directory to CoNLL format.
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

if __name__ == "__main__":
    try:
        json_dir = sys.argv[1]
    except IndexError:
        print("USAGE: python {} json_dir [nomention]".format(sys.argv[0]))
        print("conll file will be created in the same direcory, filename = json_file + '.conll'")
        exit(1)

    nomention = False
    try:
        temp = sys.argv[2]
        if temp == "nomention":
            nomention = True
    except IndexError:
        # do nothing
        pass

    for root, dirs, files in os.walk(json_dir):
        for json_file_name in files:
            json_file = os.path.join(root, json_file_name)
            if json_file.endswith(".json"):
                target_file = ''.join((json_file, '.conll'))
                with open(json_file, 'r') as jsonf:
                    js = json.load(jsonf)

                with open(target_file, 'w') as f:
                    convert(js, f, nomention)
