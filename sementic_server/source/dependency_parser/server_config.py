#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 用于配置斯坦福nlp服务的服务器地址

config = {
    'server_ip': '172.20.10.2',
    'server_port': '9000',
    'server_type':{
        'tokenize': 'tokenize',
        'ssplit': 'ssplit',
        'pos': 'pos',
        'lemma': 'lemma',
        'ner': 'ner',
        'parse': 'parse',
        'depparse': 'depparse',
        'dcoref': 'dcoref'
    }
}