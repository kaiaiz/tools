# 归属地查询：https://www.lddgo.net/common/phone
# 移动测试号码示例
# 号段规则：134-139、147、150-152、157-159、182-184、187、188、198
# 示例号码：19812345678
# 说明：需在阿里云控制台的“发送测试”页面完成绑定 
 

# 联通测试号码示例
# 号段规则：130-132、145、155、156、166、171、175、176、185、186
# 示例号码：18600001111
# 说明：需确保号码已通过验证码授权，否则调用API时会报错isv.SMS_TEST_NUMBER_LIMIT 

# 电信测试号码示例
# 号段规则：133、149、153、173、177、180、181、189、199
# 示例号码：17755556666



# 发送手机号
# 接口：https://your_url/api/sendCode
# 参数：{"phone":"your_phone","nonceStr":"your_nonceStr","sign":"your_sign"}


# 加密规则：(js语法)
# function encrypt(param) {
    
#     const nonceStr = purefn.StrUtil.radomString(5)+Date.now();
#     // 1.拼接公共参数
#     param = Object.assign({}, param, {nonceStr});
#     // 2.去空 按字典排序参数 格式化参数 添加key md5加密 转换大写 得到sign
#     param.sign = md5(purefn.ObjUtil.queryString(new purefn.ObjUtil(param).clearEmpty().filter(item=>typeof item!=='object').clearEmpty().sort().value)+ '&key=coalmsg_token').toUpperCase();
#     return param;
# }

import requests
import hashlib
import time
import random
import string
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def random_string(length):
    """生成指定长度的随机字符串"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def encrypt(param):
    """
    加密参数
    
    Args:
        param: 包含请求参数的字典
    
    Returns:
        添加了nonceStr和sign的参数字典
    """
    # 生成nonceStr（5个随机字符+当前时间戳）
    nonce_str = random_string(5) + str(int(time.time() * 1000))
    
    # 1.拼接公共参数
    param = {**param, "nonceStr": nonce_str}
    
    # 2.处理参数
    # 去空并过滤掉object类型的值
    filtered_param = {k: v for k, v in param.items() if v is not None and not isinstance(v, (dict, list))}
    
    # 按字典排序
    sorted_param = {k: filtered_param[k] for k in sorted(filtered_param.keys())}
    
    # 格式化参数为查询字符串
    query_string = "&".join([f"{k}={v}" for k, v in sorted_param.items()])
    
    # 添加key并进行md5加密
    sign_str = query_string + "&key=coalmsg_token"
    sign = hashlib.md5(sign_str.encode()).hexdigest().upper()
    
    # 添加sign到参数中
    param["sign"] = sign
    
    return param

def get_config():
    """
    从环境变量读取配置
    
    Returns:
        dict: 包含dev和pro环境配置的字典
    """
    return {
        "dev": {
            "url": os.getenv("DEV_URL", "https://your_dev_url"),
            "token": os.getenv("DEV_TOKEN", "")
        },
        "pro": {
            "url": os.getenv("PRO_URL", "https://your_pro_url"),
            "token": os.getenv("PRO_TOKEN", "")
        }
    }

def is_production():
    """
    判断是否使用生产环境
    
    Returns:
        bool: True表示生产环境，False表示开发环境
    """
    is_pro = os.getenv("IS_PRO", "true").lower()
    return is_pro in ("true", "1", "yes")

def send_verification_code(phone):
    """
    发送手机验证码
    
    Args:
        phone: 手机号
    
    Returns:
        API响应
    """
    config = get_config()
    is_pro = is_production()
    web_info = config['pro' if is_pro else 'dev']
    url = web_info["url"]
    
    # 准备参数
    param = {"phone": phone}
    
    # 加密参数
    encrypted_param = encrypt(param)
    
    # 设置请求头，添加token
    headers = {
        "token": web_info["token"],
        "Content-Type": "application/json"
    }
    
    # 发送请求
    response = requests.post(url, json=encrypted_param, headers=headers)
    
    return response.json()

# 移动：13934544931
# 联通:13015464562
# 电信：15392685573

if __name__ == "__main__":
    # 示例使用
    phone = input("请输入手机号: ")
    result = send_verification_code(phone)
    print(f"发送结果: {json.dumps(result, ensure_ascii=False, indent=2)}")


# 批量发送手机号
# select GROUP_CONCAT(r.phone) from (
# select * from t_user_dep WHERE depid=75 LIMIT 10
# ) r  GROUP BY depid 

# 批量发送手机号
def send_verification_code_batch(phones):
    """
    批量发送手机验证码
    
    Args:
        phones: 手机号列表,格式为逗号分隔的字符串或列表
        
    Returns:
        dict: 发送结果字典,key为手机号,value为发送结果
    """
    # 处理输入格式
    if isinstance(phones, str):
        phone_list = phones.split(',')
    elif isinstance(phones, list):
        phone_list = phones
    else:
        raise ValueError("phones参数必须是逗号分隔的字符串或列表")
        
    results = {}
    
    # 遍历发送
    for phone in phone_list:
        phone = phone.strip() # 去除空格
        try:
            result = send_verification_code(phone)
            results[phone] = result
        except Exception as e:
            results[phone] = {"error": str(e)}
            
        # 加入延迟避免请求过快
        time.sleep(1)
        
    return results

# if __name__ == "__main__":
#     # 批量发送示例
#     phones = input("请输入手机号(多个号码用逗号分隔): ")
#     results = send_verification_code_batch(phones)
#     print("批量发送结果:")
#     for phone, result in results.items():
#         print(f"{phone}: {json.dumps(result, ensure_ascii=False, indent=2)}")

