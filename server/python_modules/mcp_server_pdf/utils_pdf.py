import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, List, Tuple, Dict
import logging
import pdfplumber

# 设置日志
logger = logging.getLogger(__name__)

def is_file_within_workspace(file_path: Path, workspace_path: Path) -> bool:
    """检查文件是否在工作区内"""
    try:
        return str(file_path.resolve()).startswith(str(workspace_path.resolve()))
    except Exception:
        return False


def read_pdf_file(file_path: Union[str, Path],
                  workspace_path: Optional[Union[str, Path]] = None,
                  pages: Optional[List[int]] = None,
                  include_tables: bool = False) -> Tuple[bool, Dict]:
    """读取PDF文件内容

    Args:
        file_path: PDF文件路径
        workspace_path: 工作区路径
        pages: 要读取的页码列表，None则读取所有页面
        include_tables: 是否提取表格数据

    Returns:
        Tuple[bool, Dict]: (是否成功, 包含PDF信息)
    """
    try:
        # 处理文件路径
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # 处理工作区路径
        if workspace_path is not None:
            workspace = Path(workspace_path)
        else:
            workspace = Path.cwd()

        # 处理相对路径
        if not file_path.is_absolute():
            file_path = workspace / file_path

        # 安全检查
        if not is_file_within_workspace(file_path, workspace):
            return False, {"error": "文件不在当前工作区内"}

        if not file_path.exists():
            return False, {"error": f"文件不存在: {file_path}"}

        if file_path.suffix.lower() != ".pdf":
            return False, {"error": "文件不是PDF格式"}

        # 打开PDF文件
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

            # 确定要处理的页面
            if pages is None:
                target_pages = list(range(total_pages))
            else:
                # 验证页码有效性
                valid_pages = []
                for page_num in pages:
                    if 1 <= page_num <= total_pages:
                        valid_pages.append(page_num - 1)  # 转换为0-based索引
                    else:
                        logger.warning(f"跳过无效页码: {page_num}")
                target_pages = valid_pages

            # 提取页面内容
            pages_content = []
            for page_idx in target_pages:
                page = pdf.pages[page_idx]

                # 提取文本
                page_text = page.extract_text() or ""

                page_info = {
                    "page_number": page_idx + 1,
                    "text": page_text,
                    "words_count": len(page_text.split()),
                    "characters_count": len(page_text),
                    "width": page.width,
                    "height": page.height
                }

                # 提取表格（如果需要）
                if include_tables:
                    tables = page.extract_tables()
                    if tables:
                        page_info["tables"] = []
                        for table_idx, table in enumerate(tables):
                            table_data = []
                            for row in table:
                                row_data = []
                                for cell in row:
                                    row_data.append(str(cell) if cell is not None else "")
                                table_data.append(row_data)

                            page_info["tables"].append({
                                "table_index": table_idx,
                                "data": table_data,
                                "rows": len(table_data),
                                "columns": len(table_data[0]) if table_data else 0
                            })

                pages_content.append(page_info)

            result = {
                "file_path": str(file_path),
                "total_pages": total_pages,
                "processed_pages": len(pages_content),
                "pages": pages_content,
                "total_text": "\n".join([page["text"] for page in pages_content])
            }

        logger.info(f"成功读取PDF文件: {file_path}, 处理了 {len(pages_content)} 页")
        return True, result

    except Exception as e:
        logger.error(f"读取PDF文件失败: {e}")
        return False, {"error": f"读取PDF文件失败: {e}"}


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
    try:
        # 处理文件路径
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # 处理工作区路径
        if workspace_path is not None:
            workspace = Path(workspace_path)
        else:
            workspace = Path.cwd()

        # 处理相对路径
        if not file_path.is_absolute():
            file_path = workspace / file_path

        # 安全检查
        if not is_file_within_workspace(file_path, workspace):
            return False, {"error": "文件不在当前工作区内"}

        if not file_path.exists():
            return False, {"error": f"文件不存在: {file_path}"}

        # 打开PDF文件
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

            # 确定要搜索的页面
            if pages is None:
                target_pages = list(range(total_pages))
            else:
                valid_pages = []
                for page_num in pages:
                    if 1 <= page_num <= total_pages:
                        valid_pages.append(page_num - 1)
                target_pages = valid_pages

            # 执行搜索
            results = []
            search_pattern = re.escape(search_text)
            flags = 0 if case_sensitive else re.IGNORECASE

            for page_idx in target_pages:
                page = pdf.pages[page_idx]
                page_text = page.extract_text() or ""

                # 使用正则表达式搜索
                matches = list(re.finditer(search_pattern, page_text, flags))

                if matches:
                    for match in matches:
                        # 获取上下文
                        start_pos = max(0, match.start() - 50)
                        end_pos = min(len(page_text), match.end() + 50)
                        context = page_text[start_pos:end_pos]

                        # 高亮匹配文本（在上下文中）
                        context_display = context.replace(
                            match.group(),
                            f"**{match.group()}**"
                        )

                        results.append({
                            "page_number": page_idx + 1,
                            "position": match.start(),
                            "matched_text": match.group(),
                            "context": context_display,
                            "line": extract_line_from_text(page_text, match.start())
                        })

            result = {
                "file_path": str(file_path),
                "search_text": search_text,
                "total_pages": total_pages,
                "searched_pages": len(target_pages),
                "matches": results,
                "total_matches": len(results)
            }

        logger.info(f"在PDF中找到 {len(results)} 个匹配项")
        return True, result

    except Exception as e:
        logger.error(f"搜索PDF文件失败: {e}")
        return False, {"error": f"搜索失败: {e}"}


def extract_line_from_text(text: str, position: int) -> str:
    """从文本中提取包含指定位置的行"""
    # 查找行开始
    line_start = text.rfind('\n', 0, position)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # 跳过换行符

    # 查找行结束
    line_end = text.find('\n', position)
    if line_end == -1:
        line_end = len(text)

    return text[line_start:line_end].strip()


def get_pdf_metadata(file_path: Union[str, Path],
                     workspace_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Dict]:
    """获取PDF文件元数据

    Args:
        file_path: PDF文件路径
        workspace_path: 工作区路径

    Returns:
        Tuple[bool, Dict]: 是否成功和元数据信息
    """
    try:
        # 处理文件路径
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # 处理工作区路径
        if workspace_path is not None:
            workspace = Path(workspace_path)
        else:
            workspace = Path.cwd()

        # 处理相对路径
        if not file_path.is_absolute():
            file_path = workspace / file_path

        # 安全检查
        if not is_file_within_workspace(file_path, workspace):
            return False, {"error": "文件不在当前工作区内"}

        if not file_path.exists():
            return False, {"error": f"文件不存在: {file_path}"}

        # 获取文件信息
        file_stat = file_path.stat()

        # 打开PDF获取页面信息
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

            # 提取第一页的文本长度作为示例
            sample_text = ""
            if total_pages > 0:
                sample_text = pdf.pages[0].extract_text() or ""

            metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size_bytes": file_stat.st_size,
                "file_size_mb": file_stat.st_size / (1024 * 1024),
                "created_time": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "total_pages": total_pages,
                "sample_text_length": len(sample_text),
                "sample_text_words": len(sample_text.split())
            }

        logger.info(f"成功获取PDF元数据: {file_path}")
        return True, metadata

    except Exception as e:
        logger.error(f"获取PDF元数据失败: {e}")
        return False, {"error": f"获取元数据失败: {e}"}

if __name__ == '__main__':
    print('start..')
    status,data = read_pdf_file('pdf/大运天下物流有限公司数据处理安全流程制度-初稿.pdf',
                                '../../../workspace/workspace_admin',None,False)
    status,data = search_in_pdf('pdf/大运天下物流有限公司数据处理安全流程制度-初稿.pdf',
                                '数据使用部门根据工作需要，按照规定的权限和流程获取','../../../workspace/workspace_admin',)
    print(data)