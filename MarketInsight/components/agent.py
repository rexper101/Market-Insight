import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from MarketInsight.utils.logger import get_logger
from MarketInsight.utils.tools import (
    get_analyst_recommendations,
    get_analyst_recommendations_summary,
    get_balance_sheet,
    get_cash_flow,
    get_company_info,
    get_dividends,
    get_historical_data,
    get_income_statement,
    get_insider_transactions,
    get_institutional_holders,
    get_major_shareholders,
    get_mutual_fund_holders,
    get_splits,
    get_stock_news,
    get_stock_price,
    get_ticker,
)

load_dotenv()
logger = get_logger(__name__)


def build_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "OPENAI_API_KEY is not set. The AI agent is disabled until a valid key is configured."
        )
        return None

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    agent = create_agent(
        model,
        tools=[
            get_stock_price,
            get_historical_data,
            get_stock_news,
            get_balance_sheet,
            get_income_statement,
            get_cash_flow,
            get_company_info,
            get_dividends,
            get_splits,
            get_institutional_holders,
            get_major_shareholders,
            get_mutual_fund_holders,
            get_insider_transactions,
            get_analyst_recommendations,
            get_analyst_recommendations_summary,
            get_ticker,
        ],
        checkpointer=MemorySaver(),
    )
    logger.info("Agent Initiated Successfully")
    return agent


agent = build_agent()