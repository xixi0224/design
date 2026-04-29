import pdfplumber
from docx import Document
import subprocess
import os
import struct
import re
from fastapi import HTTPException

# 尝试导入 textract（纯Python接口，支持多格式）
try:
    import textract
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False

# 尝试导入 olefile（纯Python，直接解析.doc二进制OLE格式）
try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

def extract_text_from_pdf(file_path: str) -> str:
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n".join(texts)

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(texts)

def extract_text_from_doc_olefile(file_path: str) -> str:
    """
    使用纯Python库 olefile 直接解析 Word 97/2000/2002/2003 (.doc) 二进制格式。
    不依赖任何外部可执行文件，适合云环境部署。
    """
    if not OLEFILE_AVAILABLE:
        raise Exception("olefile 未安装")
    if not olefile.isOleFile(file_path):
        raise ValueError("不是有效的 OLE/.doc 文件")

    ole = olefile.OleFileIO(file_path)
    try:
        if not ole.exists('WordDocument'):
            raise ValueError("WordDocument stream 不存在")

        stream = ole.openstream('WordDocument')
        data = stream.read()

        # 解析 FIB (File Information Block)
        # wIdent @0x00, nFib @0x02
        n_fib = struct.unpack_from('<H', data, 0x2)[0]

        # 根据 FIB 版本获取文本位置和长度
        if n_fib == 0x0065:
            # Word 97: ccpText @0x18, fcMin @0x20
            ccp_text = struct.unpack_from('<I', data, 0x18)[0]
            fc_min = struct.unpack_from('<I', data, 0x20)[0]
        else:
            # Word 2000/2002/2003 (0x00C1, 0x00D9, 0x0101)
            # ccpText @0x4C, fcMin @0x18
            ccp_text = struct.unpack_from('<I', data, 0x4C)[0]
            fc_min = struct.unpack_from('<I', data, 0x18)[0]

        # 检查 Unicode 标志 (fComplex @0x0A bit0)
        flags = struct.unpack_from('<H', data, 0xA)[0]
        is_unicode = (flags & 0x0001) != 0

        if is_unicode:
            text_bytes = data[fc_min:fc_min + ccp_text * 2]
            text = text_bytes.decode('utf-16-le', errors='ignore')
        else:
            text_bytes = data[fc_min:fc_min + ccp_text]
            # 优先尝试中文编码
            text = None
            for enc in ['gbk', 'gb2312', 'utf-8', 'latin-1']:
                try:
                    text = text_bytes.decode(enc)
                    break
                except Exception:
                    continue
            if text is None:
                text = text_bytes.decode('latin-1', errors='ignore')

        # 清理：保留可打印字符和换行，段落标记转为换行
        clean_chars = []
        for c in text:
            if c.isprintable() or c in '\n\r\t':
                clean_chars.append(c)
            elif ord(c) in (0x07, 0x0D):  # 段落/回车标记
                clean_chars.append('\n')

        clean_text = ''.join(clean_chars)
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

        if not clean_text.strip():
            raise ValueError("提取的文本为空")
        return clean_text.strip()

    finally:
        ole.close()

def extract_text_from_doc(file_path: str) -> str:
    """
    解析旧版 .doc 文件。按优先级尝试多种方案：
      1. 文件头检测：若是 ZIP（伪装的 .docx），用 python-docx
      2. olefile 纯Python解析（推荐，无外部依赖）
      3. textract
      4. antiword（外部工具）
      5. 都失败则抛友好错误
    """
    # 方案1：检测是否为伪装的 .docx
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
        if header == b'PK\x03\x04':  # ZIP文件头 = docx
            return extract_text_from_docx(file_path)
    except Exception:
        pass

    # 方案2：olefile 纯Python解析（云环境首选）
    if OLEFILE_AVAILABLE:
        try:
            return extract_text_from_doc_olefile(file_path)
        except Exception as e:
            print(f"[olefile] 解析失败: {e}")
            pass  # 回退到下一方案

    # 方案3：textract（纯Python接口，底层可能调用外部工具）
    if TEXTRACT_AVAILABLE:
        try:
            raw = textract.process(file_path, encoding='utf-8')
            text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
            if text and text.strip():
                return text.strip()
        except Exception:
            pass  # 回退到 antiword

    # 方案4：antiword（外部可执行工具）
    antiword_candidates = [
        r"C:\antiword\antiword.exe",
        r"antiword",
        r"antiword.exe",
    ]
    for antiword_exe in antiword_candidates:
        try:
            result = subprocess.run(
                [antiword_exe, file_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (FileNotFoundError, Exception):
            continue

    # 全部失败
    raise HTTPException(
        status_code=400,
        detail="DOC文件解析失败。建议将文件另存为 .docx 后重新上传。"
    )

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text(file_path: str, filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    if filename.endswith(".docx"):
        return extract_text_from_docx(file_path)
    if filename.endswith(".doc"):
        return extract_text_from_doc(file_path)
    if filename.endswith(".txt") or filename.endswith(".md"):
        return extract_text_from_txt(file_path)
    raise HTTPException(status_code=400, detail="暂不支持该文件格式")