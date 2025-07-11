import io

import img2pdf
from PIL import Image


def convert_image_to_pdf(file: bytes) -> bytes:
    """bytes型の画像データ(.png, .jpg, .jpeg)をPDFに変換する

    Args:
        file (bytes): 画像(.png, .jpg, .jpeg)のbytesデータ

    Returns:
        bytes: PDFファイルのbytesデータ
    """
    # 画像形式を判定
    img = Image.open(io.BytesIO(file))
    format = img.format.lower()
    if format not in ["png", "jpeg", "jpg"]:
        raise ValueError(f"サポートされていない画像形式です: {format}")

    # PDFを生成
    try:
        pdf_bytes = img2pdf.convert(file)
    except Exception as e:
        raise Exception(f"PDF生成中にエラーが発生しました: {str(e)}")

    return pdf_bytes
