# novel_bot/src/plugins/ai_chat_system/utils/file_parser.py
# 职责: 提供通用的、与业务逻辑无关的文件处理功能，如下载和内容解析。

import asyncio
import json
import logging
from io import BytesIO
from typing import Optional

import aiohttp
import openpyxl
import pypdf
from PIL import Image
from bs4 import BeautifulSoup

logger = logging.getLogger("nonebot")


async def download_file(url: str) -> Optional[bytes]:
    """
    异步下载指定URL的文件内容。

    此函数负责处理从聊天消息中提取的文件URL，并将其内容下载为字节。
    它包含了对常见网络错误的健壮处理，如超时和HTTP错误状态。

    Args:
        url (str): 要下载的文件的URL。

    Returns:
        Optional[bytes]: 成功则返回文件的字节内容，否则返回None。
    """
    logger.debug(f"AI_CHAT: Attempting to download file from {url}")
    try:
        # 使用aiohttp进行异步网络请求，设置合理的超时以防止永久等待
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                response.raise_for_status()  # 如果HTTP状态码为4xx或5xx，则引发异常
                content = await response.read()
                logger.info(
                    f"AI_CHAT: Successfully downloaded {len(content)} bytes from {url}"
                )
                return content
    except asyncio.TimeoutError:
        logger.error(f"AI_CHAT: Timeout error when downloading file from {url}")
    except aiohttp.ClientResponseError as e:
        logger.error(f"AI_CHAT: HTTP error {e.status} when downloading file from {url}: {e.message}")
    except Exception as e:
        # 捕获所有其他潜在异常，并记录详细信息
        logger.error(f"AI_CHAT: Unexpected error during file download from {url}: {e}", exc_info=True)
    return None


async def parse_file_content(file_data: bytes, file_name: str) -> str:
    """
    根据文件名后缀解析文件内容为纯文本，以便AI模型能够理解。

    此函数是一个多态解析器，支持多种常见文件格式。它的设计是可扩展的，
    未来可以通过添加新的`elif`块来轻松支持更多文件类型。

    Args:
        file_data (bytes): 文件的原始字节数据。
        file_name (str): 包含后缀的文件名，用于判断文件类型。

    Returns:
        str: 解析后的纯文本内容。如果格式不支持或解析失败，则返回相应的提示信息。
    """
    logger.debug(f"AI_CHAT: Parsing file '{file_name}'...")
    try:
        if file_name.endswith(".txt"):
            # 对纯文本文件进行解码，使用errors='ignore'以处理潜在的编码问题
            return file_data.decode("utf-8", errors="ignore")
        elif file_name.endswith((".html", ".htm")):
            # 使用BeautifulSoup提取HTML中的纯文本，移除所有标签
            return BeautifulSoup(file_data, "html.parser").get_text(
                separator="\n", strip=True
            )
        elif file_name.endswith(".json"):
            # 格式化JSON以便AI更好地理解其结构
            return json.dumps(json.loads(file_data), ensure_ascii=False, indent=2)
        elif file_name.endswith(".pdf"):
            # 使用pypdf从PDF中逐页提取文本
            with BytesIO(file_data) as f:
                reader = pypdf.PdfReader(f)
                return "\n".join(
                    page.extract_text() for page in reader.pages if page.extract_text()
                )
        elif file_name.endswith(".xlsx"):
            # 使用openpyxl从Excel中提取数据，data_only=True确保我们得到的是计算结果而非公式
            with BytesIO(file_data) as f:
                workbook = openpyxl.load_workbook(f, read_only=True, data_only=True)
                content = []
                for sheet in workbook:
                    content.append(f"--- Sheet: {sheet.title} ---")
                    for row in sheet.iter_rows(values_only=True):
                        content.append(
                            "\t".join(
                                str(cell) if cell is not None else "" for cell in row
                            )
                        )
                return "\n".join(content)
        else:
            logger.warning(f"AI_CHAT: Unsupported file format for parsing: {file_name}")
            return "[不支持的文件格式或解析失败]"
    except Exception as e:
        # 捕获所有解析过程中可能发生的异常
        logger.error(f"AI_CHAT: Critical error while parsing file '{file_name}': {e}", exc_info=True)
        return f"[文件解析时发生严重错误: {type(e).__name__}]"