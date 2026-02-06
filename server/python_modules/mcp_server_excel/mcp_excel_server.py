from mcp.server.fastmcp import FastMCP
import utils_excel
from typing import Tuple, List, Dict, Optional, Union, Any
from pathlib import Path
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("excel document manage mcp")


@mcp.tool()
def read_excel_file(file_path: Union[str, Path],
                    workspace_path: Optional[Union[str, Path]] = None,
                    sheet_name: Optional[str] = None) -> Tuple[bool, Dict]:
    """读取Excel文件内容

    Args:
        file_path: Excel文件路径
        workspace_path: 工作区路径
        sheet_name: 工作表名称

    Returns:
        Tuple[bool, Dict]: (是否成功, 包含工作簿信息)
    """
    return utils_excel.read_excel_file(file_path, workspace_path, sheet_name)


@mcp.tool()
def create_excel_file(file_path: Union[str, Path],
                      data: List[List[Any]] = None,
                      sheet_name: str = "Sheet1",
                      workspace_path: Optional[Union[str, Path]] = None,
                      overwrite: bool = False) -> Tuple[bool, str]:
    """创建新的Excel文件

    Args:
        file_path: 文件路径
        data: 初始数据
        sheet_name: 工作表名称
        workspace_path: 工作区路径
        overwrite: 是否覆盖已存在文件

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_excel.create_excel_file(file_path, data, sheet_name, workspace_path, overwrite)


@mcp.tool()
def write_cell_to_excel(file_path: Union[str, Path],
                        cell_address: str,
                        value: Any,
                        sheet_name: Optional[str] = None,
                        workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """向Excel单元格写入数据

    Args:
        file_path: Excel文件路径
        cell_address: 单元格地址
        value: 要写入的值
        sheet_name: 工作表名称
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_excel.write_cell_to_excel(file_path, cell_address, value, sheet_name, workspace_path)


@mcp.tool()
def read_cell_from_excel(file_path: Union[str, Path],
                         cell_address: str,
                         sheet_name: Optional[str] = None,
                         workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Any]:
    """读取Excel单元格数据

    Args:
        file_path: Excel文件路径
        cell_address: 单元格地址
        sheet_name: 工作表名称
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, Any]: 是否成功和单元格值
    """
    return utils_excel.read_cell_from_excel(file_path, cell_address, sheet_name, workspace_path)


@mcp.tool()
def add_sheet_to_excel(file_path: Union[str, Path],
                       sheet_name: str,
                       data: List[List[Any]] = None,
                       workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, str]:
    """向Excel文件添加新工作表

    Args:
        file_path: Excel文件路径
        sheet_name: 新工作表名称
        data: 初始数据
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, str]: 是否成功和消息
    """
    return utils_excel.add_sheet_to_excel(file_path, sheet_name, data, workspace_path)


logger.info('config EXCEL mcp server successfully.')
# 导出服务器实例
excel_manage_server = mcp


if __name__ == '__main__':
    mcp.run('stdio')