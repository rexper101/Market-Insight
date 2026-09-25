import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse

from MarketInsight.components.agent import agent
from MarketInsight.utils.logger import get_logger
from config.config import RequestObject

logger = get_logger(__name__)
app = FastAPI(title="Market Insight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

langfuse = None
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )
else:
    logger.warning("Langfuse credentials not configured; tracing is disabled.")


@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring and keep-alive pings."""
    return {"status": "ok", "message": "Service is running"}


@app.post("/api/chat")
async def chat(request: RequestObject):
    if agent is None:
        async def unavailable_response():
            yield "The AI service is not configured. Set OPENAI_API_KEY and OPENAI_MODEL to enable chat responses."

        return StreamingResponse(
            unavailable_response(),
            media_type="text/plain",
            status_code=503,
            headers={
                "cache-control": "no-cache, no-transform",
                "connection": "keep-alive",
            },
        )

    config = {"configurable": {"thread_id": request.threadId}}

    async def generate():
        try:
            if langfuse is not None:
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="chat-request",
                    input=request.prompt.content,
                ) as span:
                    span.update(metadata={"user_id": request.threadId})

                    with langfuse.start_as_current_observation(
                        as_type="generation",
                        name="agent-stream",
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        input=request.prompt.content,
                    ) as generation:
                        full_response = ""
                        for token, _ in agent.stream(
                            {
                                "messages": [
                                    SystemMessage(
                                        content="You are a professional stock market analyst. For every user query, first determine whether a relevant tool can provide accurate or real-time data. If an appropriate tool exists, you must use it before answering. If the user does not provide an exact stock ticker, use the available tool to identify or resolve the correct ticker when required. Only when no suitable tool applies should you respond using your own reasoning and general market knowledge. Never guess, assume, or fabricate any financial data."
                                    ),
                                    HumanMessage(content=request.prompt.content),
                                ]
                            },
                            stream_mode="messages",
                            config=config,
                        ):
                            if hasattr(token, "content") and token.content:
                                full_response += token.content
                                yield token.content

                        generation.update(output=full_response)

                    span.update(output="Request completed successfully")
            else:
                full_response = ""
                for token, _ in agent.stream(
                    {
                        "messages": [
                            SystemMessage(
                                content="You are a professional stock market analyst. For every user query, first determine whether a relevant tool can provide accurate or real-time data. If an appropriate tool exists, you must use it before answering. If the user does not provide an exact stock ticker, use the available tool to identify or resolve the correct ticker when required. Only when no suitable tool applies should you respond using your own reasoning and general market knowledge. Never guess, assume, or fabricate any financial data."
                            ),
                            HumanMessage(content=request.prompt.content),
                        ]
                    },
                    stream_mode="messages",
                    config=config,
                ):
                    if hasattr(token, "content") and token.content:
                        full_response += token.content
                        yield token.content

        except Exception as exc:
            logger.error(f"Error in chat: {exc}")
            raise

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-cache, no-transform",
            "connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    logger.info("App Initiated Successfully")
    uvicorn.run(app, host="0.0.0.0", port=8000)