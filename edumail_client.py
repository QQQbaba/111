import requests
import json
import time
import re
import html
from typing import Optional, Dict, List


class EdumailClient:
    def __init__(self):
        self.base_url = "https://edumail.su"
        self.session = requests.Session()
        self.csrf_token = None
        self.email = None
        self.component_data = None  # 存储从页面提取的 Livewire 组件数据

        # 设置通用请求头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })

    def _extract_csrf_token(self, page_html: str) -> Optional[str]:
        """从HTML中提取CSRF Token"""
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page_html)
        return match.group(1) if match else None

    def _extract_livewire_component(self, page_html: str, component_name: str) -> Optional[dict]:
        """从HTML中提取指定Livewire组件的初始数据"""
        matches = re.findall(r'wire:initial-data="([^"]+)"', page_html)
        for m in matches:
            decoded = html.unescape(m)
            try:
                data = json.loads(decoded)
                if data.get("fingerprint", {}).get("name") == component_name:
                    return data
            except json.JSONDecodeError:
                continue
        return None

    def init_session(self) -> bool:
        """初始化会话,获取CSRF Token和Livewire组件数据"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()

            self.csrf_token = self._extract_csrf_token(response.text)
            if not self.csrf_token:
                print("❌ 无法提取CSRF Token")
                return False

            self.component_data = self._extract_livewire_component(response.text, "frontend.actions")
            if not self.component_data:
                print("❌ 无法提取Livewire组件数据")
                return False

            print(f"✅ CSRF Token: {self.csrf_token}")
            print(f"✅ 组件ID: {self.component_data['fingerprint']['id']}")
            print(f"✅ 可用域名: {', '.join(self.component_data['serverMemo']['data']['domains'])}")
            return True
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False

    def set_domain(self, domain: str = "oxfor.edu.pl") -> bool:
        """选择邮箱域名"""
        if not self.component_data:
            print("❌ 请先调用 init_session()")
            return False

        payload = {
            "fingerprint": self.component_data["fingerprint"],
            "serverMemo": self.component_data["serverMemo"],
            "updates": [{
                "type": "callMethod",
                "payload": {
                    "id": "w8lb",
                    "method": "setDomain",
                    "params": [domain]
                }
            }]
        }

        try:
            response = self.session.post(
                f"{self.base_url}/livewire/message/frontend.actions",
                json=payload,
                headers={
                    "X-CSRF-TOKEN": self.csrf_token,
                    "X-Livewire": "true",
                    "Content-Type": "application/json",
                    "Referer": f"{self.base_url}/"
                }
            )
            response.raise_for_status()

            data = response.json()
            # 更新 serverMemo（合并服务器返回的更新）
            self._merge_server_memo(data)
            print(f"✅ 域名设置成功: {domain}")
            return True
        except Exception as e:
            print(f"❌ 设置域名失败: {e}")
            return False

    def _merge_server_memo(self, response_data: dict):
        """合并服务器返回的 serverMemo 数据"""
        if "serverMemo" in response_data:
            server_memo = response_data["serverMemo"]
            # 更新 checksum
            if "checksum" in server_memo:
                self.component_data["serverMemo"]["checksum"] = server_memo["checksum"]
            # 更新 htmlHash
            if "htmlHash" in server_memo:
                self.component_data["serverMemo"]["htmlHash"] = server_memo["htmlHash"]
            # 更新 data
            if "data" in server_memo:
                self.component_data["serverMemo"]["data"].update(server_memo["data"])

    def generate_random_email(self) -> Optional[str]:
        """生成随机邮箱"""
        if not self.component_data:
            print("❌ 请先调用 init_session()")
            return None

        payload = {
            "fingerprint": self.component_data["fingerprint"],
            "serverMemo": self.component_data["serverMemo"],
            "updates": [{
                "type": "callMethod",
                "payload": {
                    "id": "4illj",
                    "method": "random",
                    "params": []
                }
            }]
        }

        try:
            response = self.session.post(
                f"{self.base_url}/livewire/message/frontend.actions",
                json=payload,
                headers={
                    "X-CSRF-TOKEN": self.csrf_token,
                    "X-Livewire": "true",
                    "Content-Type": "application/json",
                    "Referer": f"{self.base_url}/"
                }
            )
            response.raise_for_status()

            data = response.json()
            self._merge_server_memo(data)
            self.email = self.component_data["serverMemo"]["data"].get("email")
            print(f"✅ 生成邮箱: {self.email}")
            return self.email
        except Exception as e:
            print(f"❌ 生成邮箱失败: {e}")
            return None


if __name__ == "__main__":
    client = EdumailClient()

    if client.init_session():
        if client.set_domain("oxfor.edu.pl"):
            email = client.generate_random_email()
            if email:
                print(f"\n📧 您的edu邮箱: {email}")
