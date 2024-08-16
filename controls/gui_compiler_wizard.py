import os

from PyQt5.QtCore import QObject, pyqtSlot, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel, QRadioButton, QPushButton, QLineEdit, \
    QTextEdit, QWizard

from controls.gui_filepath import FilePathWidget
from domain.errors import CompileServiceError
from services.compile import CompileService


class CompilerConfigurationWizardWelcomePage(QWizardPage):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setTitle("開発者用コンソールの紐づけ")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            QLabel(
                "Visual Studioの開発者用コンソールを起動するバッチファイルへのパスを設定します。\n"
                "これはVisual Studioを開かずにコンパイラを動作させるために必要な設定です。\n"
                "戻るボタンを押すとおかしくなるので押さないでください。",
                None)
        )


class CompilerConfigurationWizardSelectMethodPage(QWizardPage):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setTitle("検索方法")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._rb_search_automatically = QRadioButton("自動で検索する", self)
        self._rb_search_automatically.setChecked(True)
        layout.addWidget(self._rb_search_automatically)

        self._rb_search_manually = QRadioButton("手動でパスを設定する", self)
        self._rb_search_manually.setChecked(False)
        layout.addWidget(self._rb_search_manually)

        self.registerField("rb_search_automatically", self._rb_search_automatically)
        self.registerField("rb_search_manually", self._rb_search_manually)


class CompilerConfigurationWizardManuallySelectPage(QWizardPage):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setTitle("手動で指定する")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("VsDevCmd.batのパスを指定してください", None))

        self._w_filepath = FilePathWidget("パス", True, self)
        self._w_filepath.selection_changed.connect(self._selection_changed)
        layout.addWidget(self._w_filepath)

        self._l_warning = QLabel("", self)
        self._l_warning.setStyleSheet("color: \"red\";")
        layout.addWidget(self._l_warning)

        # noinspection PyProtectedMember
        self.registerField("manual.filepath*", self._w_filepath._le_path)

    @pyqtSlot(str)
    def _selection_changed(self, path):
        if not os.path.exists(path):
            self._l_warning.setText("警告：ファイルが見つかりません")
        elif os.path.split(path)[1] != "VsDevCmd.bat":
            self._l_warning.setText("警告：通常、開発者ツールのファイル名は\"VsDevCmd.bat\"です")
        else:
            self._l_warning.setText("")


class CompilerFinderWorker(QThread):
    result_ready = pyqtSignal(str)
    result_not_found = pyqtSignal()
    update_current_path = pyqtSignal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._current_path = None
        self._stop = False

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self.__on_timeout)  # type: ignore
        self._timer.start()

    def run(self):
        search_root_lst = [
            r"C:\Program Files\Microsoft Visual Studio",
        ]
        for search_root in search_root_lst:
            for root, dirnames, filenames in os.walk(search_root):
                self._current_path = root
                if self._stop:
                    break
                if "VsDevCmd.bat" in filenames:
                    self.stop()
                    self.result_ready.emit(os.path.join(root, "VsDevCmd.bat"))  # type: ignore
                    return
        if not self._stop:
            self.result_not_found.emit()  # type: ignore

    def stop(self):
        self._stop = True
        self._timer.stop()

    @pyqtSlot()
    def __on_timeout(self):
        self.update_current_path.emit(self._current_path)  # type: ignore


class CompilerConfigurationWizardAutomaticallySelectPage(QWizardPage):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__worker: CompilerFinderWorker | None = None

        self._init_ui()

    def _init_ui(self):
        self.setTitle("自動検索")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("開発者ツールを検索して自動的に発見します。", self))

        self._b_start = QPushButton("検索を開始", self)
        self._b_start.clicked.connect(self.__on_start_clicked)  # type: ignore
        layout.addWidget(self._b_start)

        self._l_main = QLabel("", self)
        layout.addWidget(self._l_main)

        self._l_current_path = QLabel("", self)
        layout.addWidget(self._l_current_path)

        self._le_path = QLineEdit("", self)
        self._le_path.hide()
        layout.addWidget(self._le_path)

        self.registerField("auto.filepath*", self._le_path)

    @pyqtSlot()
    def __on_start_clicked(self):
        self._b_start.setEnabled(False)
        self._l_main.setText("検索中です・・・")
        self._l_current_path.setText("")
        self._le_path.setText("")

        if self.__worker is None:
            self.__worker = CompilerFinderWorker(self)
            self.__worker.result_ready.connect(self.__on_result_ready)  # type: ignore
            self.__worker.result_not_found.connect(self.__on_result_not_found)  # type: ignore
            self.__worker.update_current_path.connect(self.__on_update_current_path)  # type: ignore
            self.__worker.start()

    def hideEvent(self, evt):
        if self.__worker is not None:
            self.__worker.stop()
            self.__worker.wait()
            self.__worker = None

    @pyqtSlot(str)
    def __on_result_ready(self, path):
        self.__worker = None
        self.setField("path", path)
        self._l_main.setText("開発者ツールを発見しました！次へ進んでください。")
        self._l_current_path.setText(path)
        self._le_path.setText(path)

    @pyqtSlot()
    def __on_result_not_found(self):
        self.__worker = None
        self._l_main.setText("開発者ツールが見つかりません。手動で指定してください。")

    @pyqtSlot(str)
    def __on_update_current_path(self, path):
        self._l_current_path.setText(path)


class CompilerTestingWorker(QThread):
    test_completed = pyqtSignal(str)
    test_failed = pyqtSignal(CompileServiceError)

    def __init__(self, vs_dev_cmd_bat_path, parent: QObject = None):
        super().__init__(parent)

        self._current_path = None
        self._stop = False
        self._compiler = CompileService(
            vs_dev_cmd_bat_path=vs_dev_cmd_bat_path,
            cwd_path=os.getcwd(),
            target_relative_path_lst=["test.c"],
            timeout=5,
        )

    def run(self):
        try:
            output = self._compiler.run()
            if not os.path.exists(os.path.join(os.getcwd(), "test.exe")):
                raise CompileServiceError(
                    reason="コンパイルは終了しましたが実行ファイルが確認できませんでした",
                    output=output,
                )
        except CompileServiceError as e:
            self.test_failed.emit(e)  # type: ignore
        else:
            self.test_completed.emit(output)  # type: ignore

    def stop(self):
        self.terminate()


class CompilerConfigurationWizardTestPage(QWizardPage):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__worker: CompilerTestingWorker | None = None

        self._init_ui()

    def _init_ui(self):
        self.setTitle("テスト")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("設定された開発者ツールが正しく動作するかをテストします。", self))

        self._b_start = QPushButton("テストを開始", self)
        self._b_start.clicked.connect(self.__on_start_clicked)  # type: ignore
        layout.addWidget(self._b_start)

        self._l_status = QLabel("", self)
        layout.addWidget(self._l_status)

        self._l_path = QLabel()
        layout.addWidget(self._l_path)

        self._te_output = QTextEdit(self)
        self._te_output.setReadOnly(True)
        layout.addWidget(self._te_output)

        self._le_dummy = QLineEdit(self)
        self._le_dummy.hide()
        layout.addWidget(self._le_dummy)

        self.registerField("test.dummy*", self._le_dummy)

    @pyqtSlot()
    def __on_start_clicked(self):
        self._b_start.setEnabled(False)
        self._l_status.setText("テスト中です・・・")
        self._te_output.setText("")
        self._le_dummy.setText("")
        self._l_path.setText("")

        vs_dev_cmd_bat_path = self.field("auto.filepath") or self.field("manual.filepath")
        self._l_path.setText(f"開発者ツールの場所：{vs_dev_cmd_bat_path}")

        if self.__worker is None:
            self.__worker = CompilerTestingWorker(vs_dev_cmd_bat_path, self)
            self.__worker.test_completed.connect(self.__on_test_completed)  # type: ignore
            self.__worker.test_failed.connect(self.__on_test_failed)  # type: ignore
            self.__worker.start()

    def hideEvent(self, evt):
        if self.__worker is not None:
            self.__worker.stop()
            self.__worker.wait()
            self.__worker = None

    @pyqtSlot(str)
    def __on_test_completed(self, output):
        self.__worker = None
        self._l_status.setText("テストに成功しました！終了するとパスを保存します。")
        self._te_output.setText(output)
        self._le_dummy.setText("OK")

    @pyqtSlot(CompileServiceError)
    def __on_test_failed(self, e):
        self.__worker = None
        self._l_status.setText("テストに失敗しました")
        if e.output is not None:
            self._te_output.setText(str(e.output))


class CompilerConfigurationWizard(QWizard):
    PAGE_WELCOME = 0
    PAGE_SELECT_METHOD = 1
    PAGE_SEARCH_MANUALLY = 2
    PAGE_SEARCH_AUTOMATICALLY = 3
    PAGE_TEST = 4

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self.resize(1000, 600)

        self.setPage(
            self.PAGE_WELCOME,
            CompilerConfigurationWizardWelcomePage(self),
        )
        self.setPage(
            self.PAGE_SELECT_METHOD,
            CompilerConfigurationWizardSelectMethodPage(self),
        )
        self.setPage(
            self.PAGE_SEARCH_AUTOMATICALLY,
            CompilerConfigurationWizardAutomaticallySelectPage(self),
        )
        self.setPage(
            self.PAGE_SEARCH_MANUALLY,
            CompilerConfigurationWizardManuallySelectPage(self),
        )
        self.setPage(
            self.PAGE_TEST,
            CompilerConfigurationWizardTestPage(self),
        )

    def nextId(self):
        if self.currentId() == self.PAGE_WELCOME:
            return self.PAGE_SELECT_METHOD
        elif self.currentId() == self.PAGE_SELECT_METHOD:
            if self.field("rb_search_automatically"):
                return self.PAGE_SEARCH_AUTOMATICALLY
            elif self.field("rb_search_manually"):
                return self.PAGE_SEARCH_MANUALLY
            else:
                assert False, (
                    self.field("rb_search_automatically"),
                    self.field("rb_search_manually")
                )
        elif self.currentId() == self.PAGE_SEARCH_AUTOMATICALLY:
            return self.PAGE_TEST
        elif self.currentId() == self.PAGE_SEARCH_MANUALLY:
            return self.PAGE_TEST
        elif self.currentId() == self.PAGE_TEST:
            return -1
        else:
            assert False, self.currentId()

    def _init_ui(self):
        self.setModal(True)
        self.setWindowTitle("コンパイラの設定")  # type: ignore

    def result_path(self):
        return self.field("auto.filepath") or self.field("manual.filepath")
