from server_config import config
import yaml
import copy

def replace_string(raw_str, sub_str, replace_str, start):
    front_str = raw_str[:start]
    mid_str = replace_str
    rear_str = raw_str[start + len(sub_str):]
    return front_str+mid_str+rear_str

replace_words = yaml.load(open(u"D:\Files\面试\项目经验\项目代码\sementic_server_v2\sementic_server\data\yml\\replaceword.yml",encoding="utf-8"), Loader=yaml.SafeLoader)

sentence = '在东莞常平司马村珠江啤酒厂斜对面合租的15842062826的老婆'
old_sentence = copy.deepcopy(sentence)
entities = [{'type': 'Tel', 'value': '15842062826', 'start': 19, 'end': 30}, {'type': 'ADDR', 'value': '东莞常平司马村珠江啤酒厂', 'start': 1, 'end':13}]

#对实体进行从小到大排序
entities.sort(key=lambda x: x['start'])
entities_replace = []
for entity in entities:
    new_entity = copy.deepcopy(entity)
    # 构造新实体，替换值
    if entity['type'] == 'NAME':
        new_entity['value'] = replace_words['NAME'][0]
    elif entity['type'] == 'COMPANY':
        new_entity['value'] = replace_words['NAME'][0]
    elif entity['type'] == 'ADDR':
        new_entity['value'] = replace_words['ADDR'][0]
    elif entity['type'] == 'DATE':
        new_entity['value'] = replace_words['DATE'][0]
    elif entity['type'] == 'Qiu' or entity['type'] == 'Tel' or entity['type'] =='Ftel'\
            or entity['type'] =='Idcard' or entity['type'] =='MblogUid' or entity['type'] =='Email':
        new_entity['value'] = str(replace_words['NUM'][0])
    # 替换原句子中的词
    sentence = replace_string(sentence,entity['value'],new_entity['value'],entity['start'])
    print(sentence)

    # 替换完之后，更新后面词的offset
    '''
    for update_entity in entities:
        if update_entity['offset'] > entity['offset']:
            update_entity['offset'] = update_entity['offset'] - (len(entity['value']) - len(new_entity['value']))
    '''

    # 替换完之后，更新实体和关系的start和end
    for update_entity in entities:
        if update_entity['start'] > entity['start']:
            move_len = len(entity['value']) - len(new_entity['value'])
            update_entity['start'] = update_entity['start'] - move_len
            update_entity['end'] = update_entity['end'] - move_len



    entities_replace.append(new_entity)
    print(new_entity)
print(entities_replace)