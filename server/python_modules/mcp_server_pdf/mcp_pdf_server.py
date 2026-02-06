from mcp.server.fastmcp import FastMCP
import utils_pdf
from typing import Tuple, List, Dict, Optional, Union
from pathlib import Path
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("pdf document manage mcp")

@mcp.tool()
def read_pdf_file(file_path: Union[str, Path],
                  workspace_path: Optional[Union[str, Path]] = None,
                  pages: Optional[List[int]] = None,
                  include_tables: bool = False) -> Tuple[bool, Dict]:
    """读取PDF文件内容

    Args:
        file_path: PDF文件路径
        workspace_path: 工作区路径
        pages: 要读取的页码列表
        include_tables: 是否提取表格数据

    Returns:
        Tuple[bool, Dict]: (是否成功, 包含PDF信息)
    """
    return utils_pdf.read_pdf_file(file_path, workspace_path, pages, include_tables)


@mcp.tool()
def search_in_pdf(file_path: Union[str, Path],
                  search_text: str,
                  workspace_path: Optional[Union[str, Path]] = None,
                  case_sensitive: bool = False,
                  pages: Optional[List[int]] = None) -> Tuple[bool, Dict]:
    """在PDF文件中搜索文本

    Args:
        file_path: PDF文件路径
        search_text: 要搜索的文本
        workspace_path: 工作区路径
        case_sensitive: 是否区分大小写
        pages: 要搜索的页码列表

    Returns:
        Tuple[bool, Dict]: 是否成功和搜索结果
    """
    return utils_pdf.search_in_pdf(file_path, search_text, workspace_path, case_sensitive, pages)


@mcp.tool()
def get_pdf_metadata(file_path: Union[str, Path],
                     workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Dict]:
    """获取PDF文件元数据

    Args:
        file_path: PDF文件路径
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, Dict]: 是否成功和元数据信息
    """
    return utils_pdf.get_pdf_metadata(file_path, workspace_path)

logger.info('config PDF mcp server successfully.')
# 导出服务器实例
pdf_manage_server = mcp

if __name__ == '__main__':
    mcp.run('stdio')