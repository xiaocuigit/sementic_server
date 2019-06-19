import yaml
import copy
import json
import pprint
from sementic_server.source.dependency_parser.server_request import ServerRequest

from os.path import join, abspath
from os import getcwd
class DependencyParser:

    # 用于替换句子中的一个词
    '''
        raw_str: 原始句子
        sub_str: 原始句子中需要替换的词（用于计算需要替换的长度）
        replace_str: 想替换后的词
        offset: 需要替换词的位置
    '''
    def replace_string(self, raw_str, sub_str, replace_str, start):
        front_str = raw_str[:start]
        mid_str = replace_str
        rear_str = raw_str[start + len(sub_str):]
        return front_str + mid_str + rear_str

    # 用于替换原始句子中的实体，替换的同时关系也要更新
    def replace_entities_relations(self, sentence, entities, relations_replaced):
        dir_yml = join(abspath(getcwd()), "..", "..", "data", "yml")
        replace_words = yaml.load(open(join(dir_yml, "replaceword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        #replace_words = yaml.load(open(join(dir_yml, "replaceword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        # 防止引用传递把原始数据修改掉
        sentence = copy.deepcopy(sentence)
        entities = copy.deepcopy(entities)
        relations_replaced = copy.deepcopy(relations_replaced)

        # 对实体进行从小到大排序
        entities.sort(key=lambda x: x['start'])

        # 替换后的实体数组
        entities_replaced = []
        for entity in entities:
            new_entity = copy.deepcopy(entity)
            # 保存原来的信息，用于后面换回来
            new_entity['origin_word'] = copy.deepcopy(new_entity['value'])
            new_entity['origin_start'] = copy.deepcopy(new_entity['start'])
            new_entity['origin_end'] = copy.deepcopy(new_entity['end'])

            # 构造新实体，替换值
            if entity['type'] == 'NAME':
                new_entity['value'] = replace_words['NAME'][0]
            elif entity['type'] == 'COMPANY':
                new_entity['value'] = replace_words['NAME'][0]
            elif entity['type'] == 'ADDR':
                new_entity['value'] = replace_words['ADDR'][0]
            elif entity['type'] == 'DATE':
                new_entity['value'] = replace_words['DATE'][0]
            elif entity['type'] == 'Qiu' or entity['type'] == 'Tel' or entity['type'] == 'Ftel' \
                    or entity['type'] == 'Idcard' or entity['type'] == 'MblogUid' or entity['type'] == 'Email':
                new_entity['value'] = str(replace_words['NAME'][0])

            # 替换的新实体初始位置不变，但长度变化了，所以更新一下end字段
            new_entity['end'] = new_entity['start'] + len(new_entity['value'])
            # 替换原句子中的词
            sentence = self.replace_string(sentence, entity['value'], new_entity['value'], entity['start'])

            # 替换完之后，更新实体和关系的start和end
            move_len = len(entity['value']) - len(new_entity['value'])

            # 在new_entity之后的字段的初始和结束位置都要更新
            for update_entity in entities:
                if update_entity['start'] > entity['start']:
                    update_entity['start'] = update_entity['start'] - move_len
                    update_entity['end'] = update_entity['end'] - move_len

            # 替换完之后，new_entity后面的关系的start和end也要更新
            for update_relation in relations_replaced:
                # 将原来的关系保存下来，用于后面替换回来
                update_relation['origin_start'] = update_relation['start']
                update_relation['origin_end'] = update_relation['end']
                if update_relation['start'] > entity['start']:
                    update_relation['start'] = update_relation['start'] - move_len
                    update_relation['end'] = update_relation['end'] - move_len
            entities_replaced.append(new_entity)
        print(sentence)
        #print("entities_replaced="+str(entities_replaced))
        #print("relations_replaced="+str(relations_replaced))
        return sentence, entities_replaced, relations_replaced


    # 将依存分析的结果里面的实体进行复原
    def recover_tokens(self, dependency_tree, tokens, entities_replaced):
        #print("entities_replaced="+str(entities_replaced))
        entities_replaced = copy.deepcopy(entities_replaced)
        # 将依存分析返回的tokens的每个值都进行更新
        for token in tokens:
            # 假如碰到之前替换过的字段，替换回去
            for entity_replaced in entities_replaced:
                if entity_replaced['start'] == token['characterOffsetBegin']:
                    #print("entity_replaced="+entity_replaced['value'])
                    # 获得替换过的字段和原始字段的长度差
                    move_len = len(token['word']) - len(entity_replaced['origin_word'])
                    token['word'] = entity_replaced['origin_word']
                    token['originalText'] = entity_replaced['origin_word']
                    token['characterOffsetBegin'] = entity_replaced['origin_start']
                    token['characterOffsetEnd'] = entity_replaced['origin_end']
                    # 每当匹配成功一个，将其他的字段的start和end都进行更新
                    for token_back in tokens:
                        # entities_replaced中的变量也要更新
                        if token_back['characterOffsetBegin'] > entity_replaced['start']:
                            for entity_replaced in entities_replaced:
                                # entities_replaced中的变量也要更新
                                if entity_replaced['start'] == token_back['characterOffsetBegin']:
                                    entity_replaced['start'] = token_back['characterOffsetBegin'] - move_len
                            token_back['characterOffsetBegin'] = token_back['characterOffsetBegin'] - move_len
                            token_back['characterOffsetEnd'] = token_back['characterOffsetEnd'] - move_len

        # 更新边
        for node in dependency_tree:
            if node['governorGloss'] != 'ROOT':
                node['governorGloss'] = tokens[node['governor'] - 1]['word']
            node['dependentGloss'] = tokens[node['dependent'] - 1]['word']



        return dependency_tree, tokens


    # 将树中关系节点和实体节点之外的点删除
    def find_dependency_graph(self, dependency_tree_recovered, tokens, entities_replaced, relations_updated):
        """
            dependency_tree_recovered:
            tokens_recovered: 原始句子中需要替换的词（用于计算需要替换的长度）
            entities_replaced: 想替换后的词
        """
        # 将实体和关系整合起来
        entities_reltions = []
        entities_reltions_index = []
        for entity in entities_replaced:
            entities_reltions.append(entity['value'])
        for relation in relations_updated:
            entities_reltions.append(relation['value'])

        print("entities_reltions="+str(entities_replaced))
        '''
        dependents = []
        governors = []
        for edge in dependency_tree:
            dependents.append(edge['dependentGloss'])
            governors.append(edge['governorGloss'])
        '''
        '''
        # 获得需要删除的节点的集合
        del_tokens = []
        for token_recovered in tokens_recovered:
            if token_recovered['word'] not in entities_reltions:
                del_tokens.append(token_recovered)
        # print("del_tokens = "+str(del_tokens))
        dependency_tree_recovered = copy.deepcopy(dependency_tree_recovered)
        tokens_recovered = copy.deepcopy(tokens_recovered)

        # 删除边的条件：不是在实体和关系的数组中就要删除
        pprint.pprint("del_tokens=")
        pprint.pprint(del_tokens)
        '''

        # 遍历依存树的边，将树中所有实体和关系节点，和树中最接近根的那个实体或者关系对应
        entity_dependency_list = []
        for edge in dependency_tree_recovered:
            # 当边的尾部的值属于 实体或者关系
            if edge['dependentGloss'] in entities_reltions:
                # 循环往上找，直到找到另一个实体或者边。若是找到根节点就说明没有前置实体或者关系
                governor = copy.deepcopy(edge)
                # 非根节点
                if governor['governorGloss'] != 'ROOT':
                    # 当上方关系不是实体或者关系时
                    while governor['governorGloss'] not in entities_reltions:
                        # 往根节点查
                        for pre_edge in dependency_tree_recovered:
                            if pre_edge['dependent'] == governor['governor']:
                                #print("=="+str(governor['governorGloss']))
                                governor = copy.deepcopy(pre_edge)
                                #print("after"+str(governor['governorGloss']))
                    print("tokens="+str(tokens[edge['dependent']-1]))
                    entity_dependency_list.append({'from': edge['dependentGloss'],'from_offset':tokens[edge['dependent']- 1]['characterOffsetBegin'], 'to': governor['governorGloss'], 'to_offset' : tokens[edge['governor'] - 1]['characterOffsetBegin']})
                    #print("=="+edge['dependentGloss'])
                    #print("--"+governor['governorGloss'])
        print(entity_dependency_list)

if __name__ == '__main__':
    sentence = '在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆'
    entities = [{'type': 'Tel', 'value': '15842062826', 'start': 19, 'end': 30}, {'type': 'ADDR', 'value': '东莞常平司马村珠江啤酒厂', 'start': 1, 'end':13}]
    relations = [{'id': 'HusbandToWife', 'start': 31, 'end': 33, 'type': 'HusbandToWife', 'value': '老婆'}]

    # 替换实体，更新关系
    sentence_replaced, entities_replaced, relations_updated = DependencyParser().replace_entities_relations(sentence,
                                                                                                            entities,
                                                                                                            relations)

    dependency_tree, tokens = ServerRequest().get_dependency(sentence_replaced)
    dependency_tree_recovered, tokens_recovered = DependencyParser().recover_tokens(dependency_tree, tokens, entities_replaced)

    DependencyParser().recover_tokens(dependency_tree, tokens, entities_replaced)

    print("dependency_tree_recovered="+str(dependency_tree_recovered))

    DependencyParser().find_dependency_graph(dependency_tree_recovered, tokens, entities, relations)