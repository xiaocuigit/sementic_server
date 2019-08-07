"""
@description: Django 服务入口文件，提供 get_result 接口返回查询图
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-02
@version: 0.0.1
"""
import timeit
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sementic_server.source.ner_task.system_info import SystemInfo
from sementic_server.source.ner_task.account import Account
from sementic_server.source.ner_task.semantic_tf_serving import SemanticSearch
from sementic_server.source.ner_task.utils import convert_data_format
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from sementic_server.source.qa_graph.query_parser import QueryParser
from sementic_server.source.qa_graph.query_interface import QueryInterface
from sementic_server.source.dependency_parser.dependency_parser import DependencyParser
from sementic_server.source.recommend.recommend_server import RecommendServer

# 在这里定义在整个程序都会用到的类的实例
account_model = Account()
semantic = SemanticSearch()
item_matcher = ItemMatcher(new_actree=True)
dependency_parser = DependencyParser()
recommend_server = RecommendServer()

logger = logging.getLogger("server_log")


def account_recognition(sentence):
    """
    账号识别模块调用
    :param sentence:
    :return:
    """
    logger.info("Account Recognition model...")
    t_account = timeit.default_timer()
    accounts_info = account_model.get_account_labels_info(sentence)
    logger.info(accounts_info)
    logger.info("Account Recognition model done. Time consume: {0}".format(timeit.default_timer() - t_account))
    return accounts_info


def error_correction_model(sentence, accounts_info):
    """
    包括：纠错模块、账户识别模块、意图识别模块
    :param sentence:
    :return:
    """
    logger.info("Error Correction model...")
    t_error = timeit.default_timer()
    # 账户识别、纠错、意图识别模块
    result_intent = item_matcher.match(sentence, accounts_info=accounts_info)
    logger.info(result_intent)
    logger.info("Error Correction model done. Time consume: {0}".format(timeit.default_timer() - t_error))
    return result_intent


def ner_model(result_intent):
    """
    NER模块
    :param result_intent:
    :return:
    """
    logger.info("NER model...")
    t_ner = timeit.default_timer()
    # 实体识别模块
    result, unlabel_result = semantic.sentence_ner_entities(result_intent)

    logger.info(result)
    logger.info("NER model done. Time consume: {0}".format(timeit.default_timer() - t_ner))
    return result, unlabel_result


def dependency_parser_model(result, sentence):
    """
    依存分析模块
    :param result:
    :param sentence:
    :return:
    """
    logger.info("Dependency Parser model...")
    t_dependence = timeit.default_timer()
    # 依存分析模块
    entity = result.get('entity') + result.get('accounts')
    relation = result.get('relation')
    intention = result.get('intent')
    data = dict(entity=entity, relation=relation, intent=intention)

    logger.info("Dependency Parser model done. Time consume: {0}".format(timeit.default_timer() - t_dependence))
    return data, None


def query_graph_model(data, dependency_graph, sentence):
    """
    查询图模块
    :param data:
    :param dependency_graph:
    :param sentence:
    :return:
    """
    logger.info("Query Graph model...")
    t_another = timeit.default_timer()
    # 问答图模块
    query_graph = None
    error_info = None
    qg = None
    try:
        qg = QueryParser(data, dependency_graph)
        query_graph = qg.query_graph.get_data()
        error_info = qg.error_info
    except Exception as e:
        logger.info('动态问答图构建失败！')
        logger.info(e)
    query_interface = None
    try:
        qi = QueryInterface(qg.query_graph, sentence)
        query_interface = qi.get_query_data()
    except Exception as e:
        logger.info('查询接口转换失败！')
        logger.info(e)
    query_graph_result = {'query_graph': query_graph, 'query_interface': query_interface}
    logger.info("Query Graph model done. Time consume: {0}".format(timeit.default_timer() - t_another))
    return query_graph_result, error_info


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

    accounts_info = account_recognition(sentence)

    result_intent = error_correction_model(sentence, accounts_info=accounts_info)

    result, unlabel_result = ner_model(result_intent)

    if len(result.get("entity") + result.get("accounts")) == 0:
        return JsonResponse({"query": sentence, "error": "实体识别模块返回空值"},
                            json_dumps_params={'ensure_ascii': False})

    if unlabel_result:
        return JsonResponse(unlabel_result, json_dumps_params={'ensure_ascii': False})

    data, dependency_graph = dependency_parser_model(result, sentence)

    # 动态问答图
    query_graph_result, error_info = query_graph_model(data, None, sentence)
    if error_info:
        return JsonResponse({"query": sentence, "error": error_info}, json_dumps_params={'ensure_ascii': False})

    end_time = timeit.default_timer()

    logger.info("Full time consume: {0} S.\n".format(end_time - start_time))
    logger.info("Final reuslt...\n{0}".format(query_graph_result))
    # 返回JSON格式数据，将 result_ner 替换成需要返回的JSON数据
    return JsonResponse(query_graph_result, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def correct(request):
    """
    纠错模块单独测试接口
    :param request:
    :return:
    """
    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    try:
        request_data = json.loads(request.body)
    except json.JSONDecodeError:
        request_data = request.POST
    print(request)
    sentence = request_data['sentence']
    account = account_recognition(sentence)
    need_correct = request_data.get('need_correct', True)

    start_time = timeit.default_timer()
    result = dict()
    try:
        result = item_matcher.match(sentence, need_correct, account)
        end_time = timeit.default_timer()
        logger.info("intent_extraction - time consume: {0} S.\n".format(end_time - start_time))
    except Exception as e:
        logger.error(f"intent_extraction - {e}")
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def ner(request):
    """
    NER模块单独测试接口
    :param request:
    :return: JSON个数数据，示例如下：
    {
        "raw_input": "北京天气怎么样？",
        "entities": [
            {"type": "ADDR_VALUE", "value": 北京, "code": "201", "begin": 0,
                 "end": 2}
        ]
    }
    """
    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    request_data = json.loads(request.body)
    sentence = request_data['sentence']
    result = dict()
    try:
        logger.info("NER Model Test...")
        t_ner = timeit.default_timer()
        result_ner, _ = semantic.get_ner_result(sentence)
        result = {"raw_input": sentence, "entities": result_ner}

        logger.info(result)
        logger.info("NER Model Test Done. Time consume: {0}".format(timeit.default_timer() - t_ner))
    except Exception as e:
        logger.error(f"NER Model Test - {e}")
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def account(request):
    """
    账户识别模块单独测试接口
    :param request:
    :return: JSON个数数据，示例如下：
    {
        "raw_input": "15295668654的朋友？",
        "entities": [
            {"value": "15295668654", "type": "MOB_VALUE", "begin": 0, "end": 12, "code": "220"}
        ]
    }
    """
    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    request_data = json.loads(request.body)
    sentence = request_data['sentence']
    accounts_info = dict()
    try:
        logger.info("Account Recognition Model Test...")
        t_account = timeit.default_timer()
        accounts_info = account_model.get_account_labels_info(sentence)

        logger.info(accounts_info)
        logger.info("Account Recognition Model Test Done. Time consume: {0}".format(timeit.default_timer() - t_account))
    except Exception as e:
        logger.error(f"Account Recognition Test - {e}")
    return JsonResponse(accounts_info, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def account_ner(request):
    """
    老版本的账户识别和NER模块的接口
    :param request:
    :return:
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

    accounts_info = account_recognition(sentence)

    result_intent = error_correction_model(sentence, accounts_info=accounts_info)

    result, unlabel_result = ner_model(result_intent)
    result = convert_data_format(result)

    end_time = timeit.default_timer()

    logger.info("Full time consume: {0} S.\n".format(end_time - start_time))
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def recommendation(request):
    """
    推荐模块模块接口
    :param request:
    :return: JSON个数数据，示例如下：
    {
        "nodeId": "pr_value",
    }
    """
    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    try:
        request_data = json.loads(request.body)
    except Exception:
        request_data = request.POST
    logger.info("Recommendation Model...")
    request_data = dict(request_data)
    key = request_data.get("RedisKey", None)
    return_data = request_data.get("ReturnNodeType", None)
    need_related_relation = request_data.get("NeedRelatedRelationship", "False")
    no_answer = request_data.get("NeedNoAnswer", "False")
    bi_direction_edge = request_data.get("BiDirectionEdge", "False")
    if return_data and type(return_data) == str:
        return_data = json.loads(return_data)
    result = dict()
    if key is None:
        result = {"error": "Key值不能为空"}
        logger.error(f"Recommendation Error Info - Key值不能为空")
    else:
        try:
            need_relation = True if need_related_relation == "True" else False
            need_no_answer = True if no_answer == "True" else False
            t_recommend = timeit.default_timer()
            result = recommend_server.get_recommend_results(key=key,
                                                            return_data=return_data,
                                                            need_related_relation=need_relation,
                                                            no_answer=need_no_answer,
                                                            bi_direction_edge=bi_direction_edge)
            logger.info("Recommendation Model Done. Time consume: {0}".format(timeit.default_timer() - t_recommend))
        except Exception as e:
            logger.error(f"Recommendation Error Info - {e}")
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
