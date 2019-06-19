import yaml
import copy
from server_request import ServerRequest

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
    def replace_entities_relations(self,sentence, entities, relations):
        replace_words = yaml.load(
            open(u"D:\Files\面试\项目经验\项目代码\sementic_server_v2\sementic_server\data\yml\\replaceword.yml",
                 encoding="utf-8"), Loader=yaml.SafeLoader)
        #replace_words = yaml.load(open(join(dir_yml, "replaceword.yml"), encoding="utf-8"), Loader=yaml.SafeLoader)
        # 防止引用传递把原始数据修改掉
        sentence = copy.deepcopy(sentence)
        entities = copy.deepcopy(entities)
        relations = copy.deepcopy(relations)

        # 对实体进行从小到大排序
        entities.sort(key=lambda x: x['start'])

        # 替换后的实体数组
        entities_replace = []
        for entity in entities:
            new_entity = copy.deepcopy(entity)
            # 保存原来的信息，用于后面换回来
            new_entity['origin_word'] = new_entity['value']
            new_entity['origin_start'] = new_entity['start']
            new_entity['origin_end'] = new_entity['end']

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
                new_entity['value'] = str(replace_words['NUM'][0])

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
            for update_relation in relations:
                # 将原来的关系保存下来，用于后面替换回来
                update_relation['origin_start'] = update_relation['start']
                update_relation['origin_end'] = update_relation['end']
                if update_relation['start'] > entity['start']:
                    update_relation['start'] = update_relation['start'] - move_len
                    update_relation['end'] = update_relation['end'] - move_len

            entities_replace.append(new_entity)
        print(sentence)
        print(entities_replace)
        print(relations)
        return sentence, entities_replace, relations

if __name__ == '__main__':
    sentence = '在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆'
    entities = [{'type': 'Tel', 'value': '15842062826', 'start': 19, 'end': 30}, {'type': 'ADDR', 'value': '东莞常平司马村珠江啤酒厂', 'start': 1, 'end':13}]
    relations = [{'id': 'HusbandToWife', 'start': 31,'end':33, 'type': 'HusbandToWife', 'value': '老婆'}]

    # 替换实体，更新关系
    sentence_replaced, entities_replaced, relations_updated = DependencyParser().replace_entities_relations(sentence,
                                                                                                            entities,
                                                                                                            relations)
    # 还原回去
    #dependency_tree_recovered, tokens_recovered = DependencyParser().recover_tokens(dependency_tree, tokens,
    #                                                                                sentence_relation_replaced,
    #                                                                                entities, relations)

    dependency_tree, tokens = ServerRequest().get_dependency(sentence_replaced)

    # 将依存分析的结果里面的实体进行复原
    # 将依存分析返回的tokens的每个值都进行更新
    for token in tokens:
        # 假如碰到之前替换过的字段，替换回去
        for entity_replaced in entities_replaced:
            if entity_replaced['start'] == token['characterOffsetBegin']:
                # 获得替换过的字段和原始字段的长度差
                move_len = len(token['word']) - len(entity_replaced['origin_word'])

                token['word'] = entity_replaced['origin_word']
                token['originalText'] = entity_replaced['origin_word']
                token['characterOffsetBegin'] = entity_replaced['origin_start']
                token['characterOffsetEnd'] = entity_replaced['origin_end']
                # 每当匹配成功一个，将其他的字段的start和end都进行更新
                for token_back in tokens:
                    if token_back['characterOffsetBegin'] > entity_replaced['start']:
                        token_back['characterOffsetBegin'] = token_back['characterOffsetBegin'] - move_len
                        token_back['characterOffsetEnd'] = token_back['characterOffsetEnd'] - move_len
    # 更新边
    print(str(tokens))
    for node in dependency_tree:
        #node['dependentGloss'] = tokens[]
        if node['governorGloss'] != 'ROOT':
            node['governorGloss'] = tokens[node['governor']-1]['word']
        node['dependentGloss'] = tokens[node['dependent']-1]['word']

    print(str(dependency_tree))
    #print('--------------')
    print(str(tokens))