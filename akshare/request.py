import time

import requests
from requests.exceptions import RequestException

from akshare.exceptions import NetworkError, APIError, RateLimitError, DataParsingError
from akshare.utils.context import config
from akshare.proxy_manager import proxy_manager


def make_request_with_retry_json(
    url, params=None, headers=None, proxies=None, max_retries=3, retry_delay=1
):
    """
    发送 HTTP GET 请求，支持重试机制和代理设置。

    :param url: 请求的 URL
    :param params: URL 参数 (可选)
    :param headers: 请求头 (可选)
    :param proxies: 代理设置 (可选)
    :param max_retries: 最大重试次数
    :param retry_delay: 初始重试延迟（秒）
    :return: 解析后的 JSON 数据
    """
    if proxies is None:
        proxies = config.proxies
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, params=params, headers=headers, proxies=proxies
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data:
                        raise DataParsingError("Empty response data")
                    return data
                except ValueError:
                    raise DataParsingError("Failed to parse JSON response")
            elif response.status_code == 429:
                raise RateLimitError(
                    f"Rate limit exceeded. Status code: {response.status_code}"
                )
            else:
                raise APIError(
                    f"API request failed. Status code: {response.status_code}"
                )

        except (RequestException, RateLimitError, APIError, DataParsingError) as e:
            if attempt == max_retries - 1:
                if isinstance(e, RateLimitError):
                    raise
                elif isinstance(e, (APIError, DataParsingError)):
                    raise
                else:
                    raise NetworkError(
                        f"Failed to connect after {max_retries} attempts: {str(e)}"
                    )

            time.sleep(retry_delay)
            retry_delay *= 2  # 指数退避策略

    raise NetworkError(f"Failed to connect after {max_retries} attempts")


def make_request_with_retry_text(
    url, params=None, headers=None, proxies=None, max_retries=3, retry_delay=1
):
    """
    发送 HTTP GET 请求，支持重试机制和代理设置。

    :param url: 请求的 URL
    :param params: URL 参数 (可选)
    :param headers: 请求头 (可选)
    :param proxies: 代理设置 (可选)
    :param max_retries: 最大重试次数
    :param retry_delay: 初始重试延迟（秒）
    :return: 解析后的 JSON 数据
    """
    if proxies is None:
        proxies = config.proxies
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, params=params, headers=headers, proxies=proxies
            )
            if response.status_code == 200:
                try:
                    data = response.text
                    if not data:
                        raise DataParsingError("Empty response data")
                    return data
                except ValueError:
                    raise DataParsingError("Failed to parse JSON response")
            elif response.status_code == 429:
                raise RateLimitError(
                    f"Rate limit exceeded. Status code: {response.status_code}"
                )
            else:
                raise APIError(
                    f"API request failed. Status code: {response.status_code}"
                )

        except (RequestException, RateLimitError, APIError, DataParsingError) as e:
            if attempt == max_retries - 1:
                if isinstance(e, RateLimitError):
                    raise
                elif isinstance(e, (APIError, DataParsingError)):
                    raise
                else:
                    raise NetworkError(
                        f"Failed to connect after {max_retries} attempts: {str(e)}"
                    )

            time.sleep(retry_delay)
            retry_delay *= 2  # 指数退避策略

    raise NetworkError(f"Failed to connect after {max_retries} attempts")


def make_request(url, params=None, max_retries=10, method="GET", **kwargs):
    """
    发送HTTP请求，支持自动重试和代理切换
    :param url: 请求URL
    :param params: 请求参数
    :param max_retries: 最大重试次数
    :param method: 请求方法，支持 "GET", "POST", "PUT", "DELETE"
    :param kwargs: 其他requests参数
    :return: requests.Response对象
    """
    for attempt in range(max_retries):
        try:
            # 确保使用代理
            if "proxies" not in kwargs:
                kwargs["proxies"] = proxy_manager.get_proxies()
            
            # 设置默认超时
            if "timeout" not in kwargs:
                kwargs["timeout"] = 15

            # 根据方法发送请求
            if method.upper() == "GET":
                response = requests.get(url, params=params, **kwargs)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, **kwargs)
            elif method.upper() == "PUT":
                response = requests.put(url, params=params, **kwargs)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=params, **kwargs)
            else:
                raise ValueError(f"不支持的请求方法: {method}")

            response.raise_for_status()
            proxy_manager.record_success()  # 记录成功
            return response
        except (requests.RequestException, ValueError) as e:
            print(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            proxy_manager.record_failure()  # 记录失败
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待一段时间后重试
            else:
                raise

# 为了向后兼容，提供与requests模块类似的接口
def get(url, params=None, **kwargs):
    """发送GET请求"""
    return make_request(url, params=params, method="GET", **kwargs)

def post(url, params=None, **kwargs):
    """发送POST请求"""
    return make_request(url, params=params, method="POST", **kwargs)

def put(url, params=None, **kwargs):
    """发送PUT请求"""
    return make_request(url, params=params, method="PUT", **kwargs)

def delete(url, params=None, **kwargs):
    """发送DELETE请求"""
    return make_request(url, params=params, method="DELETE", **kwargs)
