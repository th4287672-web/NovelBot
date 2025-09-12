# novel_bot/src/plugins/ai_chat_system/tools/web_search.py
# 职责: 封装所有提供给AI模型的Function Calling工具，如此处的网络搜索。

import asyncio
import logging
from typing import Dict, List, Optional

import google.generativeai as genai
from ddgs import DDGS

logger = logging.getLogger("nonebot")

# --- 工具定义：网络搜索 ---
web_search_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="web_search",
            description="当需要回答关于近期事件、事实性知识或任何当前信息时，使用此工具进行网络搜索。例如：'今天天气怎么样？'、'谁赢得了昨晚的比赛？'、'给我介绍一下最近发布的XX模型。'",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "query": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="要搜索的关键词或问题。应尽可能具体。",
                    ),
                    "timelimit": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description='可选的时间范围限制。有效值为 "d" (过去一天), "w" (过去一周), "m" (过去一月), "y" (过去一年)。',
                        enum=["d", "w", "m", "y"],
                    ),
                },
                required=["query"],
            ),
        )
    ]
)

def _format_search_results_for_llm(results: List[Dict]) -> str:
    """
    将DDGS库返回的原始搜索结果列表格式化为对LLM友好的、信息丰富的字符串。
    这种格式化旨在帮助LLM更好地理解和总结搜索内容。
    """
    if not results:
        return "网络搜索没有找到任何相关结果。"
    
    summary = "以下是为你检索到的网络信息摘要：\n\n"
    for i, res in enumerate(results):
        summary += f"--- 来源 {i+1} ---\n"
        summary += f"标题: {res.get('title', '无标题')}\n"
        summary += f"链接: {res.get('href', '无链接')}\n"
        summary += f"内容片段: {res.get('body', '无内容片段...')}\n\n"
    return summary.strip()

def _search_sync_in_thread(query: str, timelimit: Optional[str] = None):
    """
    在同步线程中执行DDGS搜索，避免阻塞asyncio事件循环。
    这是一个关键的性能优化，确保耗时的网络IO操作不会冻结整个机器人。
    """
    # 使用DDGS库进行搜索，设置中文区域和合理的超时
    return DDGS(timeout=20).text(
        query, region="cn-zh", timelimit=timelimit, max_results=5
    )


async def execute_web_search(query: str, timelimit: Optional[str] = None) -> str:
    """
    执行网络搜索并返回格式化的结果字符串。
    这是`web_search_tool`定义的Function Calling在Python中的具体实现。

    Args:
        query (str): AI模型生成的搜索查询。
        timelimit (Optional[str]): AI模型生成的时间限制。

    Returns:
        str: 格式化后的搜索结果，将作为工具的输出返回给AI模型。
    """
    logger.info(
        f"AI_CHAT: Executing web search tool for query='{query}' with timelimit='{timelimit}'..."
    )
    try:
        # 将同步的搜索操作放到线程池中执行，以实现异步调用
        results = await asyncio.to_thread(_search_sync_in_thread, query, timelimit)
        formatted_results = _format_search_results_for_llm(results)
        logger.info(f"AI_CHAT: Web search completed successfully for query='{query}'.")
        return formatted_results
    except Exception as e:
        logger.error(f"AI_CHAT: Web search failed for query='{query}': {e}", exc_info=True)
        return f"网络搜索失败: {type(e).__name__}"