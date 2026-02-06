from mcp.server.fastmcp import FastMCP
import utils_word
from typing import Tuple, List, Dict, Optional, Union
from pathlib import Path
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("word document manage mcp")

@mcp.tool()
def read_word_file(file_path: Union[str, Path],
                   workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Dict]:
    """读取Word文档内容

    Args:
        file_path: Word文档路径
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, Dict]: (是否成功, 包含文本、段落和表格信息)
    """
    return utils_word.read_word_file(file_path, workspace_path)


@mcp.tool()
def create_word_file(file_path: Union[str, Path],
                     content: List[str] = None,
                     workspace_path: Optional[Union[str, Path]] = None,
                     overwrite: bool = False) -> Tuple[bool, str]:
    """创建新的Word文档

    Args:
        file_path: 文件路径
        content: 段落内容列表
        workspace_path: 工作区路径
        overwrite: 是否覆盖已存在文件

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_word.create_word_file(file_path, content, workspace_path, overwrite)


@mcp.tool()
def add_paragraph_to_word(file_path: Union[str, Path],
                          paragraph_text: str,
                          workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """向Word文档添加段落

    Args:
        file_path: Word文档路径
        paragraph_text: 要添加的段落文本
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_word.add_paragraph_to_word(file_path, paragraph_text, workspace_path)


@mcp.tool()
def add_table_to_word(file_path: Union[str, Path],
                      table_data: List[List[str]],
                      workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """向Word文档添加表格

    Args:
        file_path: Word文档路径
        table_data: 表格数据（二维列表）
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_word.add_table_to_word(file_path, table_data, workspace_path)


@mcp.tool()
def search_in_word(file_path: Union[str, Path],
                   search_text: str,
                   workspace_path: Optional[Union[str, Path]] = None,
                   case_sensitive: bool = False) -> Tuple[bool, Dict]:
    """在Word文档中搜索文本

    Args:
        file_path: Word文档路径
        search_text: 要搜索的文本
        workspace_path: 工作区路径
        case_sensitive: 是否区分大小写

    Returns:
        Tuple[bool, Dict]: 是否成功和搜索结果
    """
    return utils_word.search_in_word(file_path, search_text, workspace_path, case_sensitive)

logger.info('config WORD mcp server successfully.')
# 导出服务器实例
word_manage_server = mcp

if __name__ == '__main__':
    mcp.run('stdio')