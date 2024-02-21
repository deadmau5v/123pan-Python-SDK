import json

import requests

from py123pan import const
from py123pan import util


class Py123pan:
    class User:
        def __init__(self, data: dict[str, str | int]):
            self.nickname = data["nickname"]  # 昵称
            self.uid = data["uid"]  # 用户账号id
            self.headImage = data["headImage"]  # 头像
            self.mail = data["mail"]  # 邮箱
            self.passport = data["passport"]  # 手机号码

            self.spacePermanent = data["spacePermanent"]  # 永久空间
            self.spaceUsed = data["spaceUsed"]  # 已用空间
            self.spaceTemp = data["spaceTemp"]  # 临时空间
            self.spaceTempExpr = data["spaceTempExpr"]  # 临时空间到期日

            # 单位转换
            self.spacePermanent = round(self.spacePermanent / 1024 / 1024 / 1024, 2)
            self.spaceUsed = round(self.spaceUsed / 1024 / 1024 / 1024, 2)
            self.spaceTemp = round(self.spaceTemp / 1024 / 1024 / 1024, 2)
            self.spaceUsedRate = round((self.spaceUsed + self.spaceTemp) / self.spacePermanent * 100, 2)

        def print(self):
            print("\n".join([
                f"昵称：{self.nickname if self.nickname else '无'}",
                f"用户账号id：{self.uid if self.uid else '无'}",
                f"头像：{self.headImage if self.headImage else '无'}",
                f"邮箱：{self.mail if self.mail else '无'}",
                f"手机号码：{self.passport}",
                f"永久空间：{self.spacePermanent}GB",
                f"已用空间：{self.spaceUsed}GB, {self.spaceUsedRate}%",
                f"临时空间：{self.spaceTemp}GB",
                f"临时空间到期日：{self.spaceTempExpr if self.spaceTempExpr else '无'}",
            ]))

        def refresh(self, pan):
            """刷新数据"""
            self.__init__(Py123pan._get_user_info(pan))

    class File:
        def __init__(self, data: dict):
            self.fileID = data["fileID"]  # 文件ID
            self.filename = data["filename"]  # 文件名
            self.type = data["type"]  # 0-文件  1-文件夹
            self.size = data["size"]  # 文件大小
            self.etag = data["etag"]  # md5
            self.status = data["status"]  # 文件审核状态。 大于 100 为审核驳回文件
            self.parentFileId = data["parentFileId"]  # 目录ID
            self.parentName = data["parentName"]  # 目录名
            self.category = data["category"]  # 文件分类：0-未知 1-音频 2-视频 3-图片
            self.contentType = data["contentType"]  # 文件类型

            # 单位转换
            self.size = round(self.size / 1024 / 1024, 2)
            self.type = ["文件", "文件夹"][self.type]
            try:
                self.category = ["未知", "音频", "视频", "图片"][self.category]
            except IndexError:
                self.category = "未知"

        def print(self, isOneLine: bool = False):
            """
            打印文件信息
            :param isOneLine: 是否一行打印
            :return: None
            """
            sep = "\n"
            if isOneLine:
                sep = "\t"
            print(sep.join([
                f"文件ID：{self.fileID}",
                f"文件名：{self.filename}",
                f"类型：{self.type}",
                f"大小：{str(self.size) + 'MB' if self.size < 1024 else str(round(self.size / 1024, 2)) + 'GB'}",
                f"md5：{self.etag}",
                f"文件审核状态：{self.status}",
                f"目录ID：{self.parentFileId}",
                f"目录名：{self.parentName}",
                f"文件分类：{self.category}",
                f"文件类型：{self.contentType}",
            ]))

        def __str__(self):
            return f"<{self.type}>"

        __repr__ = __str__

    def __init__(self, clientID: str, clientSecret: str):
        self.accessToken = None
        self.expiredAt = None
        self.load_config(clientID, clientSecret)
        self.user = self.User(self._get_user_info())

    def __save_config(self):
        """
        持久化token
        """
        with open(const.WORKDIR + "/.token.json", "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "accessToken": self.accessToken,
                "expiredAt": self.expiredAt
            }))
        print("Token saved.")

    def load_config(self, clientID: str, clientSecret: str):
        """
        读取token
        """
        try:
            with open(const.WORKDIR + "/.token.json", "r", encoding="utf-8") as f:
                token = json.loads(f.read())
            self.accessToken = token["accessToken"]
            self.expiredAt = token["expiredAt"]
            if not util.validate_access_token(self.expiredAt):
                raise FileNotFoundError
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            print("login...")
            self.accessToken, self.expiredAt = util.get_access_token(clientID, clientSecret)
            self.__save_config()

    def _get_user_info(self) -> dict[str, str | int]:
        """
        获取用户信息
        API： GET 域名 + /api/v1/user/info
        :return: *uid	             int	      用户账号id
                 *nickname	         string	      昵称
                 *headImage	         string	      头像
                 *passport	         string	      手机号码
                 *mail    	         string	      邮箱
                 *spaceUsed	         int	      已用空间
                 *spacePermanent     int	      永久空间
                 *spaceTemp	         int	      临时空间
                 *spaceTempExpr	     string	      临时空间到期日
        """
        headers = {
            "Authorization": self.accessToken,
            "Platform": "open_platform"
        }
        API = "/api/v1/user/info"
        res = requests.get(const.URL + API, headers=headers)
        util.assert_json(res.json())
        return res.json()["data"]

    def create_share_link(self, shareName: str, shareExpire: 0 | 1 | 7 | 30, fileIDList: list[int], sharePwd: str):
        """
        创建分享链接
        API： POST 域名 + /api/v1/share/create
        :param shareName:           str              分享链接名称
        :param shareExpire:         0 | 1 | 7 | 30   分享链接有效期(天) 固定只能填写:1、7、30、0 填写0时代表永久分享
        :param fileIDList:          list[int]        分享文件ID列表 [1,2,3,4]
        :param sharePwd:            sharePwd         提取码 四位
        :return: shareID, shareKey, shareUrl
        """
        API = "/api/v1/share/create"
        headers = {
            "Authorization": self.accessToken,
            "Platform": "open_platform"
        }
        data = {
            "shareName": shareName,
            "shareExpire": shareExpire,
            "fileIDList": ",".join([str(i) for i in fileIDList]),
            "sharePwd": sharePwd,
        }
        res = requests.post(const.URL + API, headers=headers, data=data)
        util.assert_json(res.json())

        shareID = res.json()["data"]["shareID"]
        shareKey = res.json()["data"]["shareKey"]
        shareUrl = "https://www.123pan.com/s/" + shareID
        return shareID, shareKey, shareUrl

    def get_file_list(
            self,
            parentFileId: int = 0,
            page: int = 1,
            limit: int = 100,
            orderBy: str = "file_name",
            orderDirection: str = "asc",
            trashed: bool | None = None,
            searchData: str | None = None,
            fileObject: File | None = None,
    ) -> dict[str, list[File]]:
        """
        获取文件列表
        API： GET 域名 + /api/v1/file/list
        :param fileObject:          File    文件对象支持
        :param parentFileId:        int		文件夹ID，根目录传 0
        :param page:            	int		页码数
        :param limit:           	int		每页文件数量，最大不超过100
        :param orderBy:	            str		排序字段,例如:file_id、size、file_name
        :param orderDirection:	    str		排序方向:asc、desc
        :param trashed:(选填)	    bool	是否查看回收站的文件
        :param searchData:(选填)	    str		搜索关键字
        :return: list[File]
        {
        'fileList': [{      list[dict]        文件列表
            *fileID	            int		    文件ID
            *filename	        str		    文件名
            *type	            int		    0-文件  1-文件夹
            *size	            int		    文件大小
            *etag    	        bool	    md5
            *status	            int		    文件审核状态。 大于 100 为审核驳回文件
            *parentFileId	    int		    目录ID
            *parentName	        str		    目录名
            *category	        int		    文件分类：0-未知 1-音频 2-视频 3-图片
            *contentType	    int		    文件类型
            }...],
        'total':            int         总文件数
        }
        """
        API = "/api/v1/file/list"
        headers = {
            "Authorization": self.accessToken,
            "Platform": "open_platform"
        }
        if fileObject:
            parentFileId = fileObject.fileID
        data = {
            "parentFileId": parentFileId,
            "page": page,
            "limit": limit,
            "orderBy": orderBy,
            "orderDirection": orderDirection,
            "trashed": trashed,
            "searchData": searchData
        }
        res = requests.get(const.URL + API, headers=headers, data=data)
        util.assert_json(res.json())
        fileList = res.json()["data"]
        for i in range(len(fileList["fileList"])):
            fileList["fileList"][i] = self.File(fileList["fileList"][i])
        return fileList

    def get_file_tree(self, dirIdOrFile: int | File = 0) -> dict | File:
        """
        获取文件树
        API： GET 域名 + /api/v1/file/tree
        :param dirIdOrFile: int | File  文件夹ID或文件对象 默认0为根目录
        :return: dict
        """

        if isinstance(dirIdOrFile, self.File):
            if dirIdOrFile.type == "文件":
                return dirIdOrFile
            dirIdOrFile = dirIdOrFile.fileID

        tree = {}
        try:
            fs = self.get_file_list(parentFileId=dirIdOrFile)["fileList"]
        except AssertionError as e:
            if e.args[0] == "没有文件":
                return {}
            else:
                raise e

        for i in fs:
            i: Py123pan.File = i
            if i.type == "文件夹":
                temp = self.get_file_tree(i.fileID)
                if not temp:
                    tree[i.filename] = i
                else:
                    tree[i.filename] = temp
            else:
                tree[i.filename] = i
        return tree
