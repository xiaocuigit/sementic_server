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
from sementic_server.source.ner_task.account import get_account_sets
from sementic_server.source.qa_graph.query_parser import QueryParser

# 在这里定义在整个程序都会用到的类的实例
semantic = SemanticSearch()
item_matcher = ItemMatcher(new_actree=True)

logger = logging.getLogger("server_log")


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

    logger.info("Error Correction model...")
    t_error = timeit.default_timer()
    result_intent = item_matcher.match(sentence)
    logger.info(result_intent)
    logger.info("Error Correction model done. Time consume: {0}".format(timeit.default_timer() - t_error))

    logger.info("Account and NER model...")
    t_ner = timeit.default_timer()
    result_account = get_account_sets(result_intent["query"])
    result_ner = semantic.sentence_ner_entities(result_account)
    logger.info(result_ner)
    logger.info("NER model done. Time consume: {0}".format(timeit.default_timer() - t_ner))

    logger.info("Another model...")
    t_another = timeit.default_timer()
    # 添加其他模块调用
    entity = dict(result_ner).get('entity')
    relation = result_intent.get('relation')
    intention = result_intent.get('intent')
    if intention == '0':
        intention = 'PERSON'
    data = dict(entity=entity, relation=relation, intent=intention)

    try:
        qg = QueryParser(data)
        qg.query_graph.show()

        output_path = os.path.join(os.getcwd(), 'sementic_server/output', 'graph_output')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_path = os.path.join(output_path, 'example.json')
        qg.query_graph.export(output_path)
    except Exception as e:
        print(e)
    logger.info("Another model done. Time consume: {0}".format(timeit.default_timer() - t_another))
    end_time = timeit.default_timer()

    logger.info("Full time consume: {0} S.\n".format(end_time - start_time))
    # 返回JSON格式数据，将 result_ner 替换成需要返回的JSON数据
    return JsonResponse(result_ner, json_dumps_params={'ensure_ascii': False})
