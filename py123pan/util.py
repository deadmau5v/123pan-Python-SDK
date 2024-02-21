import datetime

import requests

import const


def assert_json(json_data: dict):
    try:
        assert json_data["code"] == 0
    except AssertionError:
        raise AssertionError(json_data["message"])


def validate_access_token(expiredAt: str) -> bool:
    now = datetime.datetime.now()
    # 2024-03-22T23:54:53+08:00
    expiredAt = datetime.datetime.strptime(expiredAt, "%Y-%m-%dT%H:%M:%S+08:00")
    if now > expiredAt:
        print("access_token expired.")
        return False
    else:
        print("ok access_token not expired.", expiredAt)
        return True


def get_access_token(clientID: str, clientSecret: str) -> (str, str):
    """
    获取access_token
    API： POST 域名 +/api/v1/access_token

    注：此接口有访问频率限制。
    请获取到access_token后本地保存使用，
    并在access_token过期前及时重新获取。
    access_token有效期根据返回的expiredAt字段判断。

    :param clientID:
    :param clientSecret:
    :return: accessToken  string	必填	访问凭证
             expiredAt	  string	必填	access_token过期时间
    """
    API = "/api/v1/access_token"
    res = requests.post(const.URL + API, json={
        "clientID": clientID,
        "clientSecret": clientSecret
    }, headers={
        "Platform": "open_platform"
    })
    assert_json(res.json())

    accessToken = res.json()["data"]["accessToken"]
    expiredAt = res.json()["data"]["expiredAt"]
    return accessToken, expiredAt
