# -*- coding:utf-8 -*-

from __future__ import print_function
import sys

__author__ = "Zhenhua.Fan"
__date__ = "2017-07-28"

def get_parse_list(fo, demand=6):
    parse_list = []
    for line in fo:
        line = line.strip()
        temp =  line.split('\t')
        # temp = list(filter(lambda x: len(x.strip()) > 0, line.split(' ')))
        if len(temp) >= demand:
            # ignore BEGIN OF DOCUMENT & END OF DOCUMENT
            if ("#begin" in temp[0]) or ("#end" in temp[0]):
                parse_list.append("")
            else:
                parse_list.append(temp[demand - 1])
        else:
            parse_list.append("")
    return parse_list

def get_parse_set(parse_list):
    parse_set = set()
    stack = []

    for lnum, token in enumerate(parse_list):
        # token must be:
        # [left brackets and tags] + [*] + [right brackets]
        nb_rbs = 0
        while token.endswith(')') or token.endswith('*'):
            if token.endswith(')'):
                nb_rbs += 1
            token = token[:-1]

        for tags in token.split('('):
            if tags.strip():
                stack.append((tags.strip(), lnum))

        for times in range(nb_rbs):
            tag, l = stack[-1]
            parse_set.add((tag, l, lnum))
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
        pred = get_parse_set(get_parse_list(f, 6))
        # pred = get_parse_set(get_parse_list(f, 11))
    with open(gt_file, 'r') as f:
        gt = get_parse_set(get_parse_list(f, 6))
        # gt = get_parse_set(get_parse_list(f, 11))

    tp = len(pred & gt)

    recall = float(tp) / float(len(gt))
    precision = float(tp) / float(len(pred))
    f1 = 2.0 * recall * precision / (recall + precision)

    print("recall: {}".format(recall))
    print("precision: {}".format(precision))
    print("f1: {}".format(f1))
