import argparse
import glob
import os
import re
import sys
from dataclasses import dataclass
from functools import cached_property

# WindowsでUnicode文字を出力するために標準出力をUTF-8に設定
sys.stdout.reconfigure(encoding='utf-8')


def wildcard_to_regex(pattern: str) -> str:
    """ワイルドカードパターン（*）を正規表現に変換"""
    # *を.*に変換（エスケープが必要な文字も考慮）
    escaped = re.escape(pattern)
    # エスケープされた\*を.*に変換
    regex = escaped.replace(r'\*', '.*')
    return f'^{regex}$'


def should_ignore_file(file_path: str, include_patterns: list[str], exclude_patterns: list[str]) -> bool:
    """ファイルが無視されるべきかチェック（include/excludeパターンを考慮）"""
    file_name = os.path.basename(file_path)
    
    # includeパターンが指定されている場合、一致しないものは除外
    if include_patterns:
        matched = False
        for pattern in include_patterns:
            regex_pattern = wildcard_to_regex(pattern)
            if re.match(regex_pattern, file_name):
                matched = True
                break
        if not matched:
            return True
    
    # excludeパターンに一致するものは除外
    for pattern in exclude_patterns:
        regex_pattern = wildcard_to_regex(pattern)
        if re.match(regex_pattern, file_name):
            return True
    return False


@dataclass
class FileInfo:
    """ファイル情報を保持するdataclass"""
    file_path: str
    file_normalized: str
    
    @cached_property
    def content(self) -> str:
        """ファイルの内容を遅延評価で取得"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    
    @property
    def is_empty(self) -> bool:
        """内容が空（空白文字のみ）かどうかをチェック"""
        return not self.content.strip()


def should_ignore_folder(folder_path: str, include_patterns: list[str], exclude_patterns: list[str]) -> bool:
    """フォルダが無視されるべきかチェック（include/excludeパターンを考慮）"""
    folder_name = os.path.basename(folder_path)
    # __pycache__をデフォルトで除外
    if folder_name == '__pycache__':
        return True
    
    # includeパターンが指定されている場合、一致しないものは除外
    if include_patterns:
        matched = False
        for pattern in include_patterns:
            if re.match(pattern, folder_name):
                matched = True
                break
        if not matched:
            return True
    
    # excludeパターンに一致するものは除外
    for pattern in exclude_patterns:
        if re.match(pattern, folder_name):
            return True
    return False


def walk_files(base_folder: str, file_include_patterns: list[str], file_exclude_patterns: list[str],
               folder_include_patterns: list[str], folder_exclude_patterns: list[str]):
    """検索対象のファイルを走査するジェネレータ"""
    for file in glob.glob(f"{base_folder}/**/*.py", recursive=True):
        # パス区切りを/に統一
        file_normalized = file.replace(os.sep, '/')

        # フォルダが無視パターンに一致するかチェック
        folder_parts = file_normalized.split('/')
        should_skip = False
        for part in folder_parts[:-1]:  # ファイル名以外の部分をチェック
            if should_ignore_folder(part, folder_include_patterns, folder_exclude_patterns):
                should_skip = True
                break
        if should_skip:
            continue

        # ファイルが無視パターンに一致するかチェック
        if should_ignore_file(file_normalized, file_include_patterns, file_exclude_patterns):
            continue

        yield FileInfo(file, file_normalized)


def build_tree_structure(files: list[FileInfo], base_folder: str) -> dict:
    """ファイルリストからディレクトリ構造を構築"""
    base_folder_normalized = base_folder.replace(os.sep, '/')
    tree = {}

    for file_info in files:
        # ベースフォルダからの相対パスを取得
        if file_info.file_normalized.startswith(base_folder_normalized):
            relative_path = file_info.file_normalized[len(base_folder_normalized):].lstrip('/')
        else:
            relative_path = file_info.file_normalized

        parts = relative_path.split('/')
        current = tree

        # ディレクトリ構造を構築
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # ファイル名を追加
        filename = parts[-1]
        if filename not in current:
            current[filename] = None

    return tree


def print_tree_structure(tree: dict, prefix: str = "", is_last: bool = True):
    """ツリー構造を表示"""
    items = sorted(tree.items())

    for i, (name, subtree) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        current_prefix = "└── " if is_last_item else "├── "
        name_normalized = name.replace(os.sep, '/')
        print(f"{prefix}{current_prefix}{name_normalized}")

        if subtree is not None:  # ディレクトリの場合
            extension = "    " if is_last_item else "│   "
            print_tree_structure(subtree, prefix + extension, is_last_item)


def print_tree(base_folder: str, file_include_patterns: list[str], file_exclude_patterns: list[str],
               folder_include_patterns: list[str], folder_exclude_patterns: list[str],
               hide_empty: bool = False):
    """ディレクトリ構造をツリー形式で表示"""
    files = list(walk_files(base_folder, file_include_patterns, file_exclude_patterns,
                            folder_include_patterns, folder_exclude_patterns))
    
    # 空ファイルを除外するオプション
    if hide_empty:
        files = [f for f in files if not f.is_empty]
    
    tree = build_tree_structure(files, base_folder)
    print_tree_structure(tree)


def compress_python_code(content: str) -> str:
    """Pythonコードから行末の#コメントを削除"""
    lines = content.splitlines()
    compressed_lines = []

    for line in lines:
        # 文字列リテラル内の#を考慮して行末コメントを削除
        in_string = False
        string_char = None
        escape_next = False
        comment_pos = -1

        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if not in_string:
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                elif char == '#':
                    comment_pos = i
                    break
            else:
                if char == string_char:
                    in_string = False
                    string_char = None

        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        compressed_lines.append(line)

    return '\n'.join(compressed_lines)


def print_code(base_folder: str, file_include_patterns: list[str], file_exclude_patterns: list[str],
               folder_include_patterns: list[str], folder_exclude_patterns: list[str],
               compress: bool = False, hide_empty: bool = False):
    """Pythonファイルのコードを表示"""
    files = list(walk_files(base_folder, file_include_patterns, file_exclude_patterns,
                            folder_include_patterns, folder_exclude_patterns))

    for file_info in sorted(files, key=lambda x: x.file_normalized):
        # 空ファイルを非表示にするオプション
        if hide_empty and file_info.is_empty:
            continue

        content = file_info.content
        if compress:
            content = compress_python_code(content)

        print(
            f"[{file_info.file_normalized}] ({len(content.splitlines())} lines)")
        print()
        print(content)
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Pythonファイルのコードまたはディレクトリ構造を表示します')
    parser.add_argument(
        '-t',
        '--tree',
        action='store_true',
        help='ディレクトリ構造をツリー形式で表示'
    )
    parser.add_argument(
        '-s',
        '--show',
        action='store_true',
        help='Pythonファイルのコードを表示'
    )
    parser.add_argument(
        'folder',
        nargs='?',
        help='対象フォルダ名'
    )
    parser.add_argument(
        '-f',
        '--file-include',
        action='append',
        dest='file_includes',
        default=[],
        metavar='PATTERN',
        help='含めるファイル名パターン（ワイルドカード * を使用可能）'
    )
    parser.add_argument(
        '-F',
        '--file-exclude',
        action='append',
        dest='file_excludes',
        default=[],
        metavar='PATTERN',
        help='除外するファイル名パターン（ワイルドカード * を使用可能）'
    )
    parser.add_argument(
        '-d',
        '--folder-include',
        action='append',
        dest='folder_includes',
        default=[],
        metavar='PATTERN',
        help='含めるフォルダ名パターン（正規表現）'
    )
    parser.add_argument(
        '-D',
        '--folder-exclude',
        action='append',
        dest='folder_excludes',
        default=[],
        metavar='PATTERN',
        help='除外するフォルダ名パターン（正規表現）'
    )
    parser.add_argument(
        '-e',
        '--hide-empty',
        action='store_true',
        help='内容が空（空白文字のみ）のファイルを非表示にする'
    )
    parser.add_argument(
        '-c',
        '--compress',
        action='store_true',
        help='行末の#コメントを削除してコードを圧縮'
    )

    args = parser.parse_args()

    # -tと-sのどちらも指定されていない場合はヘルプを表示
    if not args.tree and not args.show:
        parser.print_help()
        sys.exit(1)

    # folderが指定されていない場合
    if not args.folder:
        parser.error('フォルダ名を指定してください')

    # フォルダが存在しない場合
    if not os.path.isdir(args.folder):
        parser.error(f'フォルダが見つかりません: {args.folder}')

    if args.tree:
        print(f"[folder structure]")
        print_tree(args.folder, args.file_includes, args.file_excludes,
                   args.folder_includes, args.folder_excludes, args.hide_empty)
        print()

    if args.show:
        print_code(args.folder, args.file_includes, args.file_excludes,
                   args.folder_includes, args.folder_excludes, args.compress, args.hide_empty)


if __name__ == "__main__":
    main()
