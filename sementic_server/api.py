# -*- coding: utf-8 -*-
import os
import timeit
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from sementic_server.source.ner_task.system_info import SystemInfo
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.qa_graph.query_interface import QueryInterface
from sementic_server.source.dependency_parser.dependency_parser import DependencyParser

# 在这里定义在整个程序都会用到的类的实例
semantic = SemanticSearch()
item_matcher = ItemMatcher(new_actree=True)
dependency_parser = DependencyParser()

logger = logging.getLogger("server_log")


def error_correction_model(sentence):
    logger.info("Error Correction model...")
    t_error = timeit.default_timer()
    # 账户识别、纠错、意图识别模块
    result_intent = item_matcher.match(sentence)
    logger.info(result_intent)
    logger.info("Error Correction model done. Time consume: {0}".format(timeit.default_timer() - t_error))
    return result_intent


def ner_model(result_intent):
    logger.info("NER model...")
    t_ner = timeit.default_timer()
    # 实体识别模块
    result = semantic.sentence_ner_entities(result_intent)

    logger.info(result)
    logger.info("NER model done. Time consume: {0}".format(timeit.default_timer() - t_ner))
    return result


def dependency_parser_model(result, sentence):
    logger.info("Dependency Parser model...")
    t_dependence = timeit.default_timer()
    # 依存分析模块
    entity = result.get('entity') + result.get('accounts')
    relation = result.get('relation')
    intention = result.get('intent')
    data = dict(entity=entity, relation=relation, intent=intention)
    dependency_tree_recovered, tokens_recovered, dependency_graph, entities, relations = \
        dependency_parser.get_denpendency_tree(sentence, entity, relation)

    logger.info("Dependency Parser model done. Time consume: {0}".format(timeit.default_timer() - t_dependence))
    return data, dependency_graph


def query_graph_model(data, dependency_graph, sentence):
    logger.info("Query Graph model...")
    t_another = timeit.default_timer()
    # 问答图模块
    query_graph_result = dict()
    try:
        query_graph_result = dict()
        qg = QueryParser(data, dependency_graph)
        query_graph = qg.query_graph.get_data()
        if not query_graph:
            qg = QueryParser(data)
            query_graph = qg.query_graph.get_data()
        qi = QueryInterface(qg.query_graph, sentence)
        query_interface = qi.get_query_data()
        query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}
    except Exception as e:
        logger.info(e)
    logger.info("Query Graph model done. Time consume: {0}".format(timeit.default_timer() - t_another))
    return query_graph_result


@csrf_exempt
def get_result(request):
    """
    input: 接收客户端发送的POST请求：{"sentence": "raw_sentence"}
    output: 服务器返回JSON格式的数据，返回的数据格式如下：


    :param request: 用户输入的查询句子
    :return
    """

    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})

    request_data = json.loads(request.body)
    sentence = request_data['sentence']

    if len(sentence) < SystemInfo.MIN_SENTENCE_LEN:
        logger.error("输入的句子长度太短")
        return JsonResponse({"query": sentence, "status": SystemInfo.MIN_SENTENCE_LEN},
                            json_dumps_params={'ensure_ascii': False})

    if len(sentence) > SystemInfo.MAX_SENTENCE_LEN:
        logger.error("输入的句子长度太长")
        return JsonResponse({"query": sentence, "status": SystemInfo.MAX_SENTENCE_LEN},
                            json_dumps_params={'ensure_ascii': False})

    start_time = timeit.default_timer()
    result_intent = error_correction_model(sentence)
    result = ner_model(result_intent)
    if result is None:
        return JsonResponse({"query": sentence, "error": "实体识别模块返回空值"},
                            json_dumps_params={'ensure_ascii': False})
    data, dependency_graph = dependency_parser_model(result, sentence)
    query_graph_result = query_graph_model(data, None, sentence)
    end_time = timeit.default_timer()

    logger.info("Full time consume: {0} S.\n".format(end_time - start_time))
    # 返回JSON格式数据，将 result_ner 替换成需要返回的JSON数据
    return JsonResponse(query_graph_result, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def correct(request):
    print(request.method)

    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    request_data = request.POST
    print(request)
    sentence = request_data['sentence']
    need_correct = request_data.get('need_correct', True)

    start_time = timeit.default_timer()
    result = dict()
    try:
        result = item_matcher.match(sentence, need_correct)
        end_time = timeit.default_timer()
        logger.info("intent_extraction - time consume: {0} S.\n".format(end_time - start_time))
    except Exception as e:
        logger.error(f"intent_extraction - {e}")
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
