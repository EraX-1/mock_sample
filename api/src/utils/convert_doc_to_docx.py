import os
import subprocess
import tempfile


def convert_doc_bytes_to_docx_bytes(doc_bytes: bytes) -> bytes:
    """
    .docファイルのバイトデータを受け取り、.docxファイルのバイトデータを返す関数。

    Parameters:
    - doc_bytes: .docファイルのバイトデータ

    Returns:
    - .docxファイルのバイトデータ
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 一時的な.docファイルのパスを作成
        tmp_doc_path = os.path.join(tmpdir, "temp_input.doc")
        # 一時的な.docxファイルのパスを作成
        tmp_docx_path = os.path.join(tmpdir, "temp_input.docx")

        # バイトデータを一時的な.docファイルに書き込み
        with open(tmp_doc_path, "wb") as f:
            f.write(doc_bytes)

        # LibreOfficeのコマンドを構築
        command = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            tmpdir,
            tmp_doc_path,
        ]

        try:
            # コマンドを実行
            subprocess.run(command, check=True)

            # 変換後の.docxファイルをバイトデータとして読み込み
            with open(tmp_docx_path, "rb") as f:
                docx_bytes = f.read()

            return docx_bytes

        except subprocess.CalledProcessError as e:
            raise Exception(f"変換中にエラーが発生しました: {str(e)}")
