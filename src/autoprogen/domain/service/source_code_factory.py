from autoprogen.domain.model.source_code import SourceCode


class SourceCodeDecodeError(UnicodeError):
    """提出されたソースコードの文字コードを解釈できないことを表す。"""


class SourceCodeFactory:
    """提出ファイルのバイト列を現行仕様どおりに正規化する。"""

    @staticmethod
    def _decode(source_code_bytes: bytes) -> str:
        """UTF-8を優先し、失敗した場合はShift-JISとして読み込む。"""
        try:
            return source_code_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            try:
                return source_code_bytes.decode("shift-jis", errors="strict")
            except UnicodeDecodeError as error:
                raise SourceCodeDecodeError(
                    "source file is not UTF-8 or Shift-JIS"
                ) from error

    def create(self, source_code_bytes: bytes) -> SourceCode:
        """提出時のバイト列を解釈し、正規化済みソースコードを生成する。"""
        if type(source_code_bytes) is not bytes:
            raise TypeError("source_code_bytesはbytesである必要があります")

        # 現行動作を維持し、CRLFだけをLFへ変換する。
        source_code_text = self._decode(source_code_bytes).replace("\r\n", "\n")
        return SourceCode(text=source_code_text)
