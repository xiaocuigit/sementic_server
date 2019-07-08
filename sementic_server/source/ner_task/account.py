"""
@description: 账户识别模块   账户种类：
                身份证号、手机号、电话号、邮箱、微信、支付宝账户、京东账户、微博、设备MAC号、设备IMEI号、
                设备IMSI号、QQ号、QQ群、车牌号、车架号、发动机号、公司工商注册号
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-07-08
@version: 0.1.1
"""
import re
import yaml

from pprint import pprint
from sementic_server.source.ner_task.entity_code import EntityCode
from sementic_server.source.ner_task.system_info import SystemInfo


def is_legal_id_card(candidate):
    """
    判断身份证号码是否合法，包含15位和18位身份证号码两种情况
    :param candidate:
    :return:
    """
    area = {"11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古", "21": "辽宁", "22": "吉林", "23": "黑龙江",
            "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东", "41": "河南",
            "42": "湖北",
            "43": "湖南", "44": "广东", "45": "广西", "46": "海南", "50": "重庆", "51": "四川", "52": "贵州", "53": "云南",
            "54": "西藏",
            "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆", "71": "台湾", "81": "香港", "82": "澳门",
            "91": "国外"}
    candidate = str(candidate)
    candidate = candidate.strip()
    candidate_list = list(candidate)

    if not area[candidate[0:2]]:
        return False
    if len(candidate) == 15:
        if ((int(candidate[6:8]) + 1900) % 4 == 0 or (
                (int(candidate[6:8]) + 1900) % 100 == 0 and (int(candidate[6:8]) + 1900) % 4 == 0)):
            ereg = re.compile(
                r"[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|"
                r"[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}$")  # //测试出生日期的合法性
        else:
            ereg = re.compile(
                r"[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|"
                r"[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}$")  # //测试出生日期的合法性
        if re.match(ereg, candidate):
            return True
        else:
            return False
    elif len(candidate) == 18:
        # 出生日期的合法性检查
        # 闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
        # 平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
        if int(candidate[6:10]) % 4 == 0 or (int(candidate[6:10]) % 100 == 0 and int(candidate[6:10]) % 4 == 0):
            # 闰年出生日期的合法性正则表达式
            ereg = re.compile(
                r"[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|"
                r"(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9Xx]$")
        else:
            # 平年出生日期的合法性正则表达式
            ereg = re.compile(
                r"[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|"
                r"(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9Xx]$")
            # 测试出生日期的合法性
        if re.match(ereg, candidate):
            # 计算校验位
            S = (int(candidate_list[0]) + int(candidate_list[10])) * 7 + (
                    int(candidate_list[1]) + int(candidate_list[11])) * 9 + (
                        int(candidate_list[2]) + int(candidate_list[12])) * 10 + (
                        int(candidate_list[3]) + int(candidate_list[13])) * 5 + (
                        int(candidate_list[4]) + int(candidate_list[14])) * 8 + (
                        int(candidate_list[5]) + int(candidate_list[15])) * 4 + (
                        int(candidate_list[6]) + int(candidate_list[16])) * 2 + int(candidate_list[7]) * 1 + int(
                candidate_list[8]) * 6 + int(candidate_list[9]) * 3
            Y = S % 11
            JYM = "10X98765432"
            M = JYM[Y]  # 判断校验位
            if M == candidate_list[17]:  # 检测ID的校验位
                return True
            else:
                return False
        else:
            return False
    return True


def is_email(candidate):
    """
    判断candidate是否为合法的邮箱账户
    :param candidate:
    :return:
    """
    pattern_email = r"([0-9a-zA-Z_!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[" \
                    r"\w](?:[\w-]*[0-9a-zA-Z_])?)$"
    result = re.match(pattern_email, candidate)
    if result is not None:
        return True
    return False


def is_phone(candidate):
    """
    判断candidate是否为合法的电话号码
    :param candidate:
    :return:
    """
    pattern_phone = r"^(\d{3}-\d{8}|\d{4}-\{7,8})$"
    result = re.match(pattern_phone, candidate)
    if result is not None:
        return True
    return False


def is_mobile_phone(candidate):
    """
    判断candidate是否为合法的手机号码
    :param candidate:
    :return:
    """
    pattern_mobile_phone = r"^((13[0-9]|14[0-9]|15[0-9]|166|17[0-9]|18[0-9]|19[8|9])\d{8})$"
    result = re.match(pattern_mobile_phone, candidate)
    if result is not None:
        return True
    return False


def is_wechat_candidate(candidate):
    """
    判断candidate是否为合法的微信号码
    :param candidate:
    :return:
    """
    pattern_wechat = r"^([a-zA-Z]([-_a-zA-Z0-9]{5,19})+)$"
    result = re.match(pattern_wechat, candidate)
    if result is not None:
        return True
    return False


def is_qq(candidate):
    """
    判断candidate是否为合法的 QQ 号码
    :param candidate:
    :return:
    """
    pattern_qq = r"(^[1-9][0-9]{4,12})$"
    result = re.match(pattern_qq, candidate)
    if result is not None:
        return True
    return False


def is_imei(candidate):
    """
    判断设备IMEI号码
    :param candidate:
    :return:
    """
    pattern_imei = r"^(\d{15})$"
    result = re.match(pattern_imei, candidate)
    if result:
        return True
    else:
        return False


def is_mac(candidate):
    """
    判断设备MAC号码
    :param candidate:
    :return:
    """
    pattern_mac = r"^([0-9a-fA-F]{2})(([:][0-9a-fA-F]{2}){5})$"
    result = re.match(pattern_mac, candidate)
    if result:
        return True
    else:
        return False


class Account:
    """
    账户识别类
    """

    def __init__(self):
        """
        初始化一些必要的全局变量
        """
        system_info = SystemInfo()
        entity = EntityCode()
        self.account_label = entity.get_account_label()
        self.entity_code = entity.get_entity_code()
        self.account_identify = yaml.load(open(system_info.get_account_label_path(), encoding='utf-8'),
                                          Loader=yaml.SafeLoader)
        self.identity_account = {value: k for k, v in self.account_identify.items() for value in v}

    def get_closest_account_label(self, raw_str):
        """
        获取最靠近账户的那个账户标识符
        :param raw_str:
        :return:
        """
        max_id = -1
        max_label = None

        for identity, label in self.identity_account.items():
            id = -1
            for match in re.finditer(identity, raw_str):
                if match.start() > id:
                    id = match.start()

            if id != -1 and id == max_id and identity[-1] == '群':
                max_id = id + 1
                if identity in self.account_label['WX_GROUP']:
                    max_label = 'WX_GROUP'
                elif identity in self.account_label['QQ_GROUP']:
                    max_label = 'QQ_GROUP'
                else:
                    max_label = label

            if id != -1 and id > max_id:
                max_id = id
                max_label = label
        return max_label

    def is_id_card(self, candidate):
        """
        判断candidate是否为合法的身份证号码，包含15位和18位身份证号码两种情况
        :param candidate:
        :return:
        """
        pattern_id = r"^(([1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx])|([" \
                     r"1-9]\d{5}\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}))$"
        result = re.match(pattern_id, candidate)
        if result is not None:
            return is_legal_id_card(candidate)
        return False

    def is_wechat_wxid(self, raw_input, candidate):
        """
        判断candidate是否为合法的微信号码
        :param candidate:
        :return:
        """

        pattern_wxid = r"^(wxid_([-_a-zA-Z0-9]{5,15})+)$"
        result_wxid = re.match(pattern_wxid, candidate)
        if result_wxid is not None:
            return True
        else:
            label = self.get_closest_account_label(raw_input)
            if label == self.account_label['WECHAT']:
                return True
            else:
                return False

    def match_vehicle_num(self, raw_string):
        """
        判断raw_string里面是否有车牌号
        :param raw_string:
        :return:
        """
        pattern_veh = re.compile(
            "([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}(([0-9]{5}[DF])|(DF[0-9]{4})))|"
            "([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}[A-HJ-NP-Z0-9]{4}"
            "[A-HJ-NP-Z0-9挂学警港澳]{1})")
        vehicles = []
        for match in re.finditer(pattern_veh, raw_string):
            begin = match.start()
            end = match.end()
            if begin != -1:
                plate_num = raw_string[begin:end]
                vehicles.append({"value": plate_num, "type": "VEHCARD_VALUE", "begin": begin, "end": end,
                                 "code": self.entity_code['VEHCARD_VALUE']})

        return vehicles

    def get_candidate_label(self, raw_input, account):
        """
        判断账户是否有对应的账户标识符，如果有则返回
        :param raw_input:
        :param account:
        :param qq_group:
        :return:
        """
        index = raw_input.find(account)
        if index != -1:
            label = self.get_closest_account_label(raw_input[:index])
            if label:
                return self.account_label[label]
            return None
        return None

    def get_account_labels_info(self, raw_input):
        """
        找出所有可能是账户的字符串，如果该字符串符合账户的正则，或者有对应的账户标识符，则给该字符串对应的账户标签
        否则给该字符串一个 UNLABEL 标签，需要跟用户交互具体账户类型
        :param raw_input:
        :return:
        """
        pattern_account = r"([a-zA-Z0-9@_\-\.:]{7,})"
        account_list = []
        sentence = raw_input
        vehicles = self.match_vehicle_num(sentence)
        if len(vehicles) != 0:
            account_list.extend(vehicles)

        for match in re.finditer(pattern_account, raw_input):
            begin = match.start()
            end = match.end()
            is_veh = False
            if len(vehicles) != 0:
                for veh in vehicles:
                    if veh['begin'] <= begin <= veh['end']:
                        is_veh = True
            if is_veh:
                continue
            result = raw_input[begin: end]

            if is_mac(result):
                label_name = 'MAC_VALUE'
                sentence = sentence.replace(result, 'MAC_VALUE')
            elif is_email(result):
                label = self.get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = self.account_label['EMAIL']
                    sentence = sentence.replace(result, self.account_label['EMAIL'])
            elif self.is_id_card(result):
                label_name = self.account_label['ID']
                sentence = sentence.replace(result, self.account_label['ID'])
            elif is_imei(result):
                label = self.get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = self.account_label['UNLABEL']
                    sentence = sentence.replace(result, self.account_label['UNLABEL'])
            elif is_wechat_candidate(result):
                label = self.get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                elif self.is_wechat_wxid(raw_input, result):
                    label_name = self.account_label['WECHAT']
                    sentence = sentence.replace(result, self.account_label['WECHAT'])
                else:
                    label_name = self.account_label['UNLABEL']
                    sentence = sentence.replace(result, self.account_label['UNLABEL'])
            elif is_mobile_phone(result):
                label = self.get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = self.account_label['MPHONE']
                    sentence = sentence.replace(result, self.account_label['MPHONE'])
            elif is_phone(result):
                label_name = self.account_label['PHONE']
                sentence = sentence.replace(result, self.account_label['PHONE'])
            elif is_qq(result):
                label = self.get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = self.account_label['UNLABEL']
                    sentence = sentence.replace(result, self.account_label['UNLABEL'])
            else:
                # 未识别账户标识为 UNLABEL 标签
                label_name = self.account_label['UNLABEL']
                sentence = sentence.replace(result, self.account_label['UNLABEL'])
            account_list.append(
                {"value": result, "type": label_name, "begin": begin, "end": end,
                 "code": self.entity_code[label_name]})

        account_result = {'raw_input': raw_input, 'accounts': account_list}
        return account_result


def test():
    t1 = "15295668658住在哪里？34.54,2656353125"
    t2 = "xiaocui-kindle@163.com住在哪里？"
    t3 = "手机号是15295668650的人住在哪里？"
    t4 = "手机号是15295668650，身份证号是610525199705165219的人住在哪里？"
    t5 = "张三的手机号是不是15295668765"
    t6 = "张三的手机15295678908和微信号是不是15295668658和xiaozhang_test？"
    t7 = "张三的手机好和微信号是不是15295668658、xiaozhang_test？"
    t8 = "手机号是15295668650，身份证号是610525199403155218的人住在哪里？"
    t9 = "支付宝是15295668650的人住在哪里？"
    t10 = "微博15295668650的人住在哪里？"
    t11 = "15295668658住在哪里？34.54,QQ群2656353125"
    t12 = "京东账户15295668658住在哪里？"
    t13 = "QQ号是2656353125住在哪里？"
    t14 = "武威美嘉源农业科技有限公司的Qq账号16850973070有哪些弟弟？"
    t15 = "武威美嘉源农业科技有限公司的15295668650有哪些弟弟？"
    t16 = "武威美嘉源农业科技有限公司的QQ_xiaocui有哪些弟弟？"
    t17 = "IMEI号码是543216789012345的设备"
    t18 = "谁的设置号44:2A:60:71:CC:8D曾经在哪里上网"
    test_list = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18]
    account = Account()
    for index, raw_input in enumerate(test_list):
        result = account.get_account_labels_info(raw_input)
        print("\n==============================")
        pprint(result)
        print("==============================\n")


def test_while():
    account = Account()
    while True:
        sentence = input("input:")
        pprint(account.get_account_labels_info(sentence))


def test_vehicle_num():
    account = Account()
    while True:
        sentence = input("input:")
        result = account.match_vehicle_num(sentence)
        pprint(result)


def test_mac():
    while True:
        sentence = input("input:")
        result = is_mac(sentence)
        pprint(result)


if __name__ == '__main__':
    test()
