import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from MarketInsight.utils.tools import *
from MarketInsight.utils.logger import get_logger
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

load_dotenv()
logger = get_logger(__name__)

model = ChatOpenAI(
        model = "c1/openai/gpt-5/v-20250930",
        base_url = "https://api.thesys.dev/v1/embed/"
    )

