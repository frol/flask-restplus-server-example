# -*- coding: utf-8 -*-
import oss2


def upload(key, file):
    key = 'evidence' + key
    endpoint = 'fjykt.oss-cn-hangzhou.aliyuncs.com'  # 假设你的Bucket处于杭州区域

    auth = oss2.Auth('SjwSbzZrLQB9oxO0', 'cOblvk6wRoHhVpEyGhofumS9Yvmc6e')
    bucket = oss2.Bucket(auth, endpoint, 'fjykt', True)

    # 上传
    return bucket.put_object(key, file)
