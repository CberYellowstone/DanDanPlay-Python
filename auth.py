import hashlib
import time
import uuid
from typing import Optional, Tuple

import jwt

from database import regUser, vaildPassword, vaildUserIfExists



def vaildLogin(username: str, password: str) -> Tuple[bool, str]:
    if not vaildUserIfExists(username):
        return False, '用户不存在'
    if not vaildPassword(username, password):
        return False, '密码不正确'
    return True, '登陆成功'


def generateUUID(username: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_DNS, username).__str__()


# 86400 = 60 * 60 * 24, or rather, 24 hours
def generateToken(username: str, exp: int = time.time().__int__() + 86400) -> str:
    return jwt.encode({"exp": exp, "id": generateUUID(username), "name": username}, 'pas', algorithm="HS256")


def vaildToken(token: Optional[str]) -> Tuple[bool, str]:
    '''Return: is_vaild, username or failed_message'''
    if token is None:
        return False, 'Token required'
    try:
        decoded = jwt.decode(token, 'pas', algorithms=['HS256'])
        return True, decoded['name']
    except jwt.ExpiredSignatureError:
        return False, 'Token expired'
    except jwt.InvalidTokenError:
        return False, 'Token invalid'


def addUser():
    while True:
        username = input('请输入用户名：')
        if not vaildUserIfExists(username):
            break
        print('用户已存在，请重新输入！')
    password = input('请输入密码：')
    regUser(username, hashlib.sha256(password))
