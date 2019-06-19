import json


if __name__ == '__main__':
    n = 2
    path = 'case%d.json' % n
    with open(path, 'r') as fr:
        data = json.load(fr)
    print(data)

    data['intent'] = 'Person'

    dep = [{'from': {'from_offset': 0, 'value': '15195919704', 'type': 'entity'},
            'to': {'to_offset': 9, 'value': '同学', 'type': 'relation'}}]
    data['dependency'] = dep
    json.dump(data, open(path, 'w'))
