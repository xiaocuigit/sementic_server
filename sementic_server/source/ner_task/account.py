"""
@description: 账户识别模块   账户种类：
                身份证号、手机号、电话号、邮箱、微信、支付宝账户、京东账户、微博、设备MAC号、设备IMEI号、
                设备IMSI号、QQ号、QQ群、车牌号、车架号、发动机号、公司工商注册号
@author: Cui Rui long
@email: xiaocuikindle@163.com
@time: 2019-05-27
@version: 0.0.1
"""

import re

from pprint import pprint
from collections import defaultdict

PUNCTUATION = [',', '，', '~', '!', '！', '。', '.', '?', '？']
EMAIL = 'EMAIL_VALUE'
MPHONE = 'MOB_NUM'
PHONE = 'PHONE_NUM'
QQ = 'QQ_NUM'
QQ_GROUP = 'QQ_GROUP_NUM'
WX_GROUP = 'WX_GROUP_NUM'
WECHAT = 'WECHAT_VALUE'
ID = 'IDCARD_VALUE'
MBLOG = 'MICROBLOG_VALUE'
ALIPAY = 'ALIPAY_VALU'
DOUYIN = 'DOUYIN_VALUE'
TAOBAO = 'TAOBAO_VALUE'
JD = 'JD_VALUE'
UNLABEL = 'UNLABEL'


def is_legal_id_card(candidate):
    """
    判断身份证号码是否合法，包含15位和18位身份证号码两种情况
    :param candidate:
    :return:
    """
    area = {"11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古", "21": "辽宁", "22": "吉林", "23": "黑龙江",
            "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东", "41": "河南", "42": "湖北",
            "43": "湖南", "44": "广东", "45": "广西", "46": "海南", "50": "重庆", "51": "四川", "52": "贵州", "53": "云南", "54": "西藏",
            "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆", "71": "台湾", "81": "香港", "82": "澳门", "91": "国外"}
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


def is_id_card(candidate):
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


def is_wechat(raw_input, candidate):
    """
    判断candidate是否为合法的微信号码
    :param candidate:
    :return:
    """
    pattern_wechat = r"^([a-zA-Z]([-_a-zA-Z0-9]{5,19})+)$"
    result = re.match(pattern_wechat, candidate)
    if result is not None:
        pattern_wxid = r"^(wxid_([-_a-zA-Z0-9]{5,15})+)$"
        result_wxid = re.match(pattern_wxid, candidate)
        if result_wxid is not None:
            return True
        else:
            wx_labels = ['微信', '微信号', '微信账户', '微信账户']
            index = raw_input.find(candidate)
            if index != -1:
                for label in wx_labels:
                    if label in raw_input[:index]:
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


def is_ali_pay(raw_input, account):
    """
    判断 account 是否为 支付宝账户
    :param raw_input:
    :param account:
    :return:
    """
    ali_labels = ['支付宝', '支付宝账户', '支付宝账号']
    index = raw_input.find(account)
    if index != -1:
        for label in ali_labels:
            if label in raw_input[:index]:
                return ALIPAY
    return None


def is_jing_dong(raw_input, account):
    """
    判断 account 是否为 京东账户
    :param raw_input:
    :param account:
    :return:
    """
    jd_labels = ['京东', '京东账户', '京东账号']
    index = raw_input.find(account)
    if index != -1:
        for label in jd_labels:
            if label in raw_input[:index]:
                return JD
    return None


def is_tao_bao(raw_input, account):
    """
    判断 account 是否为 淘宝账户
    :param raw_input:
    :param account:
    :return:
    """
    tb_labels = ['淘宝', '淘宝账户', '淘宝账号']
    index = raw_input.find(account)
    if index != -1:
        for label in tb_labels:
            if label in raw_input[:index]:
                return TAOBAO
    return None


def is_wei_bo(raw_input, account):
    """
    判断 account 是否为 微博账户
    :param raw_input:
    :param account:
    :return:
    """
    wb_labels = ['微博', '微博账户', '微博账号']
    index = raw_input.find(account)
    if index != -1:
        for label in wb_labels:
            if label in raw_input[:index]:
                return MBLOG
    return None


def is_dou_yin(raw_input, account):
    """
    判断 account 是否为 抖音账户
    :param raw_input:
    :param account:
    :return:
    """
    dy_labels = ['抖音', '抖音账户', '抖音账号']
    index = raw_input.find(account)
    if index != -1:
        for label in dy_labels:
            if label in raw_input[:index]:
                return DOUYIN
    return None


def is_qq_or_qq_group(raw_input, account):
    """
    判断 account 是否为 QQ群账户
    :param raw_input:
    :param account:
    :return:
    """
    qq_group = ['QQ群', 'qq群']
    qq_label = ['QQ', 'qq']
    index = raw_input.find(account)
    if index != -1:
        # 检测是否为QQ群
        for label in qq_group:
            if label in raw_input[:index]:
                return QQ_GROUP
        # 检测是否为QQ
        for label in qq_label:
            if label in raw_input[:index]:
                return QQ
    return None


def is_wx_group(raw_input, account):
    """
    判断 account 是否为 微信群账户
    :param raw_input:
    :param account:
    :return:
    """
    wx_group = ['微信群', 'wx群']
    index = raw_input.find(account)
    if index != -1:
        for label in wx_group:
            if label in raw_input[:index]:
                return WX_GROUP
    return None


def get_candidate_label(raw_input, account, qq_group=False):
    """
    判断账户是否有对应的账户标识符，如果有则返回
    :param raw_input:
    :param account:
    :param qq_group:
    :return:
    """
    label = is_wei_bo(raw_input, account)
    if label:
        return label
    label = is_ali_pay(raw_input, account)
    if label:
        return label
    label = is_tao_bao(raw_input, account)
    if label:
        return label
    label = is_dou_yin(raw_input, account)
    if label:
        return label
    label = is_jing_dong(raw_input, account)
    if label:
        return label
    if qq_group:
        label = is_qq_or_qq_group(raw_input, account)
        return label

    return None


def get_account_labels_info(raw_input):
    """
    找出所有可能是账户的字符串，如果该字符串符合账户的正则，或者有对应的账户标识符，则给该字符串对应的账户标签
    否则给该字符串一个 UNLABEL 标签，需要跟用户交互具体账户类型
    :param raw_input:
    :return:
    """
    pattern_account = r"([a-zA-Z0-9@_\-\.]*)"
    account_list = []
    sentence = raw_input

    for match in re.finditer(pattern_account, raw_input):
        begin = match.start()
        end = match.end()
        result = raw_input[begin: end]
        if len(result) >= 3:
            if is_email(result):
                label = get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = EMAIL
                    sentence = sentence.replace(result, EMAIL)
            elif is_id_card(result):
                label_name = ID
                sentence = sentence.replace(result, ID)
            elif is_wechat(raw_input, result):
                label_name = WECHAT
                sentence = sentence.replace(result, WECHAT)
            elif is_mobile_phone(result):
                label = get_candidate_label(raw_input, result)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = MPHONE
                    sentence = sentence.replace(result, MPHONE)
            elif is_phone(result):
                label_name = PHONE
                sentence = sentence.replace(result, PHONE)
            elif is_qq(result):
                label = get_candidate_label(raw_input, result, qq_group=True)
                if label:
                    label_name = label
                    sentence = sentence.replace(result, label)
                else:
                    label_name = UNLABEL
                    sentence = sentence.replace(result, UNLABEL)
            else:
                if result in ['QQ', 'qq']:
                    continue
                # 未识别账户标识为 UNLABEL 标签
                label_name = UNLABEL
                sentence = sentence.replace(result, UNLABEL)
            account_list.append({"account_label": label_name, "account": result, "begin": begin, "end": end})

    account_result = {'raw_input': raw_input, 'accounts': account_list, 'template': sentence}
    # pprint(account_list)
    return account_result


def get_account_sets(raw_input):
    """
    检测 raw_input 中所有可能的账户集合
    :param raw_input: 用户输入的问句，问句内中不能包含空格
    :return:
    """
    # 识别出所有可能的账户
    pattern_account = r"([a-zA-Z0-9@_\-\.]*)"
    account_list = defaultdict(list)
    sentence = raw_input
    for result in re.findall(pattern_account, raw_input):
        if len(result) >= 3:
            if is_email(result):
                label = get_candidate_label(raw_input, result)
                if label:
                    account_list[label].append(result)
                    sentence = sentence.replace(result, label)
                else:
                    account_list[EMAIL].append(result)
                    sentence = sentence.replace(result, EMAIL)
            elif is_id_card(result):
                account_list[ID].append(result)
                sentence = sentence.replace(result, ID)
            elif is_wechat(raw_input, result):
                account_list[WECHAT].append(result)
                sentence = sentence.replace(result, WECHAT)
            elif is_mobile_phone(result):
                label = get_candidate_label(raw_input, result)
                if label:
                    account_list[label].append(result)
                    sentence = sentence.replace(result, label)
                else:
                    account_list[MPHONE].append(result)
                    sentence = sentence.replace(result, MPHONE)
            elif is_phone(result):
                account_list[PHONE].append(result)
                sentence = sentence.replace(result, PHONE)
            elif is_qq(result):
                label = get_candidate_label(raw_input, result, qq_group=True)
                if label:
                    account_list[label].append(result)
                    sentence = sentence.replace(result, label)
                else:
                    account_list[UNLABEL].append(result)
                    sentence = sentence.replace(result, UNLABEL)
            else:
                if result in ['QQ', 'qq']:
                    continue
                # 未识别账户标识为 UNLABEL 标签
                account_list[UNLABEL].append(result)
                sentence = sentence.replace(result, UNLABEL)

    account_result = {'raw_input': raw_input, 'labels': account_list, 'new_input': sentence}
    return account_result


def test():
    """
    测试函数
    :return:
    """
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
    t13 = "qq号是2656353125住在哪里？"
    t14 = "账户是wxid_3xu6v29giqqv12的人住在哪里？"
    t15 = "微信号是crlabner的人住在哪里？"
    t16 = "账户是crlabner的人住在哪里？"
    test_list = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16]
    for index, raw_input in enumerate(test_list):
        result = get_account_labels_info(raw_input)
        print("\n==============================")
        pprint(result)
        print("==============================\n")
        result = get_account_sets(raw_input)
        print("\n==============================")
        pprint(result)
        print("==============================\n")


if __name__ == '__main__':
    test()
