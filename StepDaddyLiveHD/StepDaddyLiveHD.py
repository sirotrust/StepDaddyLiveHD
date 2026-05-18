import sys
import os

# Force Python to recognize the current directory for imports
sys.path.append(os.getcwd())

import httpx
import re
from typing import List
from pydantic import BaseModel
from curl_cffi.requests import AsyncSession
import reflex as rx

# --- DATA & SCRAPER MODULE ---
class Channel(BaseModel):
    id: str
    name: str
    tvg_id: str
    logo: str
    group: str

class StepDaddy:
    def __init__(self):
        # Updated to the current working live domain
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
            response = await self._session.get(f"{self._base_url}/24-7-channels.php", headers=self._headers())
            if response.status_code == 200:
                self._channels = self._parse_channels(response.text)
            else:
                print(f"Failed to load channels: Status {response.status_code}")
        except Exception as e:
            print(f"Error loading channels: {str(e)}")

    def _parse_channels(self, html_content: str) -> List[Channel]:
        parsed_list = []
        matches = re.findall(r'href=["\'](?:.*?stream/)?stream-(\d+)\.php["\'].*?>(.*?)</a>', html_content, re.IGNORECASE)
        for ch_id, ch_name in matches:
            parsed_list.append(
                Channel(
                    id=ch_id,
                    name=ch_name.strip(),
                    tvg_id=f"dlhd-{ch_id}",
                    logo="",
                    group="DaddyLive Live TV"
                )
            )
        return parsed_list

    def get_channels(self) -> List[Channel]:
        return self._channels

# Initialize backend scraper instance
step_daddy = StepDaddy()

# Mock backend routing module expected by your compilation template
class BackendMock:
    @property
    def fastapi_app(self):
        return None
    async def update_channels(self):
        await step_daddy.load_channels()
    def get_channels(self):
        return step_daddy.get_channels()

backend = BackendMock()

# --- REFLEX UI APP STATE ---
class State(rx.State):
    channels: List[Channel] = []
    search_query: str = ""

    @rx.var
    def filtered_channels(self) -> List[Channel]:
        if not self.search_query:
            return self.channels
        return [ch for ch in self.channels if self.search_query.lower() in ch.name.lower()]

    async def on_load(self):
        self.channels = backend.get_channels()

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value

# --- REFLEX UI DESIGN ---
@rx.page("/", on_load=State.on_load)
def index() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    placeholder="Search channels...",
                    on_change=State.set_search_query,
                    value=State.search_query,
                    width="100%",
                    max_width="25rem",
                    size="3",
                ),
                padding="1rem",
                background_color="var(--gray-2)",
            ),
        ),
        rx.center(
            rx.cond(
                State.channels,
                rx.grid(
                    rx.foreach(
                        State.filtered_channels,
                        lambda channel: rx.box(
                            rx.text(channel.name, font_weight="bold"),
                            rx.text(channel.group, size="1", color="var(--gray-11)"),
                            padding="1rem",
                            border_radius="8px",
                            background_color="var(--gray-3)",
                        ),
                    ),
                    grid_template_columns="repeat(auto-fill, minmax(250px, 1fr))",
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.spinner(),
                    height="50vh",
                ),
            ),
            padding="1rem",
            padding_top="4rem",
        ),
    )

# --- APP CONFIGURATION ---
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
)

# Register the background live stream fetch
app.register_lifespan_task(backend.update_channels)

# Trick the Reflex compiler into finding the module path it's screaming about
sys.modules["StepDaddyLiveHD.StepDaddyLiveHD"] = sys.modules[__name__]
