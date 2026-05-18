import httpx
import re
from typing import List, Optional
from pydantic import BaseModel
from curl_cffi.requests import AsyncSession

class Channel(BaseModel):
    id: str
    name: str
    tvg_id: str
    logo: str
    group: str

class StepDaddy:
    def __init__(self):
        # Updated dead 'dlhd.dad' to the functional live domain
        self._base_url = "https://daddylives.click"
        self._session = AsyncSession()
        self._channels: List[Channel] = []

    def _headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"{self._base_url}/",
            "Origin": self._base_url
        }

    async def load_channels(self):
        try:
            # This line will now resolve cleanly without throwing a DNSError
            response = await self._session.get(f"{self._base_url}/24-7-channels.php", headers=self._headers())
            if response.status_code == 200:
                self._channels = self._parse_channels(response.text)
            else:
                print(f"Failed to load channels: Status {response.status_code}")
        except Exception as e:
            print(f"Error loading channels from source: {str(e)}")
            raise e

    def _parse_channels(self, html_content: str) -> List[Channel]:
        parsed_list = []
        # Matches the typical daddylive link layout: href="stream/stream-X.php" >Channel Name</a>
        matches = re.findall(r'href=["\'](?:.*?stream/)?stream-(\d+)\.php["\'].*?>(.*?)</a>', html_content, re.IGNORECASE)
        
        for ch_id, ch_name in matches:
            clean_name = ch_name.strip()
            parsed_list.append(
                Channel(
                    id=ch_id,
                    name=clean_name,
                    tvg_id=f"dlhd-{ch_id}",
                    logo="",
                    group="DaddyLive Live TV"
                )
            )
        return parsed_list

    def get_channels(self) -> List[Channel]:
        return self._channels

step_daddy = StepDaddy()
