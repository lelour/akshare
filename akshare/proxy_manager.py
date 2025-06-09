import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ProxyManager:
    def __init__(self):
        self.auth_key = os.getenv("PROXY_AUTH_KEY")  # 不设默认值作为后备
        self.password = os.getenv("PROXY_PASSWORD")  # 不设默认值作为后备
        self.proxy_list = []
        self.current_proxy_index = 0
        self.proxies = None
        self.failure_count = 0
        self.max_failures = 3  # 最大连续失败次数
        self.query_proxy_list()

    def query_proxy_list(self):
        """查询当前可用的代理IP列表"""
        try:
            url = f"https://exclusive.proxy.qg.net/query?key={self.auth_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data["code"] == "SUCCESS":
                self.proxy_list = []
                for task in data["data"]["tasks"]:
                    for ip_info in task["ips"]:
                        self.proxy_list.append({
                            "addr": ip_info["server"],
                            "auth_key": self.auth_key,
                            "password": self.password,
                            "proxy_ip": ip_info["proxy_ip"],
                            "area": ip_info["area"],
                            "isp": ip_info["isp"],
                            "deadline": ip_info["deadline"]
                        })
                print(f"当前可用代理IP数量: {len(self.proxy_list)}")
                
                # 如果没有获取到代理IP，尝试更换IP
                if not self.proxy_list:
                    print("未获取到代理IP，尝试更换IP...")
                    if self.rotate_proxy():
                        print("成功更换IP并获取到新的代理列表")
                    else:
                        print("更换IP失败")
                elif self.proxy_list:
                    self.proxies = self._get_proxy_config()
            else:
                print(f"查询代理IP列表失败: {data}")
                # 查询失败时也尝试更换IP
                print("尝试更换IP...")
                if self.rotate_proxy():
                    print("成功更换IP并获取到新的代理列表")
                else:
                    print("更换IP失败")
        except Exception as e:
            print(f"查询代理IP列表时发生错误: {str(e)}")
            # 发生异常时也尝试更换IP
            print("尝试更换IP...")
            if self.rotate_proxy():
                print("成功更换IP并获取到新的代理列表")
            else:
                print("更换IP失败")

    def _is_proxy_expired(self, proxy_info):
        """检查代理是否过期"""
        try:
            deadline = datetime.strptime(proxy_info["deadline"], "%Y-%m-%d %H:%M:%S")
            return datetime.now() > deadline
        except Exception:
            return True

    def _check_and_rotate_if_needed(self):
        """检查当前代理是否需要更换"""
        if not self.proxy_list:
            return self.rotate_proxy()

        current_proxy = self.proxy_list[self.current_proxy_index]
        
        # 检查是否过期
        if self._is_proxy_expired(current_proxy):
            print(f"当前代理IP已过期: {current_proxy['addr']}")
            return self.rotate_proxy()
        
        # 检查连续失败次数
        if self.failure_count >= self.max_failures:
            print(f"当前代理IP连续失败{self.failure_count}次: {current_proxy['addr']}")
            self.failure_count = 0
            return self.rotate_proxy()
        
        return True

    def _get_proxy_config(self):
        """获取当前代理配置"""
        if not self.proxy_list:
            self.query_proxy_list()
            if not self.proxy_list:
                raise Exception("没有可用的代理IP")

        # 检查是否需要更换代理
        if not self._check_and_rotate_if_needed():
            raise Exception("无法获取有效的代理IP")

        current_proxy = self.proxy_list[self.current_proxy_index]
        proxy_url = "http://%(user)s:%(password)s@%(server)s" % {
            "user": current_proxy["auth_key"],
            "password": current_proxy["password"],
            "server": current_proxy["addr"],
        }
        return {
            "http": proxy_url,
            "https": proxy_url,
        }

    def rotate_proxy(self, num=1, keep_alive=None, area=None, isp=None, distinct=False):
        """
        更换代理IP
        :param num: 提取数量，默认为1
        :param keep_alive: 资源存活时间（分钟），默认为套餐支持最大值
        :param area: 地区ID，默认查询全部
        :param isp: 运营商ID，默认0（不限），1:电信 2:移动 3:联通
        :param distinct: IP去重，默认False
        """
        try:
            # 构建请求参数
            params = {
                "key": self.auth_key,
                "num": num
            }
            if keep_alive is not None:
                params["keep_alive"] = keep_alive
            if area is not None:
                params["area"] = area
            if isp is not None:
                params["isp"] = isp
            if distinct:
                params["distinct"] = "true"

            # 发送更换IP请求
            url = "https://exclusive.proxy.qg.net/replace"
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data["code"] == "SUCCESS":
                # 更新代理列表
                self.proxy_list = []
                for ip_info in data["data"]["ips"]:
                    self.proxy_list.append({
                        "addr": ip_info["server"],
                        "auth_key": self.auth_key,
                        "password": self.password,
                        "proxy_ip": ip_info["proxy_ip"],
                        "area": ip_info["area"],
                        "isp": ip_info["isp"],
                        "deadline": ip_info["deadline"]
                    })
                self.current_proxy_index = 0
                self.proxies = self._get_proxy_config()
                self.failure_count = 0  # 重置失败计数
                
                current_proxy = self.proxy_list[self.current_proxy_index]
                print(f"成功更换代理IP: {current_proxy['addr']} ({current_proxy['area']} {current_proxy['isp']})")
                return True
            else:
                print(f"更换代理IP失败: {data}")
                return False
        except Exception as e:
            print(f"更换代理IP时发生错误: {str(e)}")
            return False

    def get_proxies(self):
        """获取当前代理配置"""
        if not self.proxies:
            self.proxies = self._get_proxy_config()
        return self.proxies

    def get_proxy_info(self):
        """获取当前代理的详细信息"""
        if not self.proxy_list:
            return None
        return self.proxy_list[self.current_proxy_index]

    def record_failure(self):
        """记录代理访问失败"""
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            print(f"代理访问失败次数达到{self.max_failures}次，准备更换代理")
            self._check_and_rotate_if_needed()

    def record_success(self):
        """记录代理访问成功"""
        self.failure_count = 0

# 创建全局代理管理器实例
proxy_manager = ProxyManager() 