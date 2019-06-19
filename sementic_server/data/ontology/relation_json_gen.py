import json
import csv


if __name__ == '__main__':
    result = dict()
    with open('relation.csv', 'r', encoding='utf-8') as csv_file:
        csv_file.readline()
        csv_reader = csv.reader(csv_file)
        for i in csv_reader:
            k, d, r = i
            result[k] = {'domain': d, 'range': r}

    with open('relation.json', 'w') as fw:
        json.dump(result, fw)
