# -*- coding: utf-8 -*-
import timeit
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.ner_task.system_info import SystemInfo
from sementic_server.source.ner_task.account import get_account_sets

semantic = SemanticSearch()

logger = logging.getLogger("server_log")


@csrf_exempt
def get_result(request):
    """
    input: 接收客户端发送的POST请求：{"sentence": "raw_sentence"}
    output: 服务器返回JSON格式的数据，返回的数据格式如下：
    {
        “status”: "200",
        "sen_raw": raw_sentence,
        "template": 在COMPANY工作的NAME,
        "label": [每个 字/词 对应的标签],
        "which_candidate": "0",
        "similarity": "[0, 1)"
    }
    其中 status             接口请求信息反馈编码表
        sen_raw            原始的问句
        label              问句中每个字/词对应的标签
        which_candidate    对应的是可能的模板类别
        template           对应的是具体的模板句子
        similarity         对应的是计算的模板相似度值

    为了方便java后期处理数据，所有字段的值均是 str 类型的

    :param request: 用户输入的查询句子
    :return 如果返回的是空字符串表示没有匹配到合适的模板
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

    logger.info("Account and NER model...")
    t_ner = timeit.default_timer()

    result_account = get_account_sets(sentence)

    result = semantic.sentence_ner_entities(result_account)

    logger.info(result)

    logger.info("NER model done. Time consume: {0}".format(timeit.default_timer() - t_ner))

    logger.info("Another model...")
    # 添加其他模块调用
    logger.info("End Another model...")
    end_time = timeit.default_timer()

    logger.info("Full time consume: {0} S.\n".format(end_time - start_time))

    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
