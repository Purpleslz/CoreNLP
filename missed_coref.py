# -*- coding:utf-8 -*-

from __future__ import print_function
import json
import os
import sys

__author__ = "Zhenhua.Fan"
__date__ = "2017-08-01"

def get_parse_list(fo, demand=12):
    parse_list = []
    for line in fo:
        line = line.strip()
        if line:
            temp = line.split('\t')
            if len(temp) >= demand:
                # ignore BEGIN OF DOCUMENT & END OF DOCUMENT
                if ("#begin" in temp[0]) or ("#end" in temp[0]):
                    parse_list.append("")
                else:
                    parse_list.append(temp[-1])
            else:
                parse_list.append("")
    return parse_list

def get_parse_set(parse_list):
    parse_set = set()
    stack = []

    for lnum, token in enumerate(parse_list):
        for ch in token:
            if ch == '(':
                stack.append(lnum)
            elif ch == ')':
                parse_set.add((stack[-1], lnum))
                stack.pop()

    return parse_set

if __name__ == "__main__":
    try:
        pred_file = sys.argv[1]
    except IndexError:
        print("USAGE: python {} pred_file gt_file".format(sys.argv[0]))
        exit(1)

    try:
        gt_file = sys.argv[2]
    except IndexError:
        print("USAGE: python {} pred_file gt_file".format(sys.argv[0]))

    with open(pred_file, 'r') as f: 
        pred = get_parse_set(get_parse_list(f))
    with open(gt_file, 'r') as f:
        gt = get_parse_set(get_parse_list(f))

    tp = pred & gt
    missed = gt - tp

    lines = []
    doc_id = []
    sent_id = []

    doc_index = -1
    with open(pred_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                if line.startswith("#begin"):
                    doc_index += 1
                    sent_index = 0
                lines.append(line)
                doc_id.append(doc_index)
                sent_id.append(sent_index)
            else:
                sent_index += 1

    ret = dict()
    for l, r in missed:
        ret[(doc_id[l], sent_id[l], int(lines[l].split('\t')[2]), int(lines[r].split('\t')[2]) + 1)] = ['\n'.join(lines[max(0, l - 20):min(r + 20, len(lines))])]

    filename_list = ['all.txt.new',
                     'pleonastic.txt.new',
                     'quantrule.txt.new',
                     'partitiveRule.txt.new',
                     'bareNPRule.txt.new',
                     'percentsymbol.txt.new',
                     'percentandmoney.txt.new',
                     'isAdjectival.txt.new',
                     'stoplist.txt.new', 'nested.txt.new',
                    ]

    root_path = './logs'

    for filename in filename_list:
        allofit = None
        with open(os.path.join(root_path, filename), 'r') as f:
            allofit = json.load(f)

        for key, extra in allofit:
            key = tuple(key)
            if key in ret:
                ret[key].append(filename)
                if extra:
                    ret[key].append(extra)

    for key, value in ret.items():
        print('doc_id:', key[0])
        print('sent_id:', key[1])
        print('bidx:', key[2])
        print('eidx:', key[3])
        for s in value:
            print(s)
            print('')
        print('\n\n')
