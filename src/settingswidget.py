import os

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QMessageBox

import style
from Lib.bili_api import user, utils
from dialoglogin import DialogLogin
from ui_settingswidget import Ui_SettingsWidget
from utils import configUtils
from utils.open_folder import open_folder

# codec
video_codec_id = {
    7: "H.264(AVC) 尺寸大，兼容性最佳",
    12: "H.265(HEVC) 尺寸中等，兼容性一般",
    13: "AV1 尺寸小，老机型兼容差",
}

video_codec_match = {}
for _i in video_codec_id:
    video_codec_match[video_codec_id[_i]] = _i

# style
qt_styles = ["default"]
qt_styles += QtWidgets.QStyleFactory.keys()


class SettingsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_SettingsWidget()
        self.ui.setupUi(self)
        self.userdata = configUtils.UserDataHelper()
        self.mw_tab_index = None
        codecs = []
        for i in video_codec_match:
            codecs.append(i)
        self.ui.combo_codec.addItems(codecs)
        self.ui.combo_style.addItems(qt_styles)
        self.connect(
            self.ui.button_path,
            QtCore.SIGNAL("clicked()"),
            self.on_path_button_clicked,
        )

        self.connect(
            self.ui.button_login,
            QtCore.SIGNAL("clicked()"),
            self.on_login_button_clicked,
        )

        self.connect(
            self.ui.button_reset,
            QtCore.SIGNAL("clicked()"),
            self.on_reset_button_clicked,
        )

        self.connect(
            self.ui.line_path,
            QtCore.SIGNAL("textChanged(QString)"),
            self.on_line_path_changed,
        )

        self.connect(
            self.ui.button_config_dir,
            QtCore.SIGNAL("clicked()"),
            self.on_open_config_dir_clicked,
        )

        self.connect(
            self.ui.button_logout,
            QtCore.SIGNAL("clicked()"),
            self.on_logout_button_clicked,
        )

    def load_settings(self):
        self.userdata.reload()
        path = self.userdata.get(
            self.userdata.CFGS.DOWNLOAD_PATH,
            QtCore.QDir("Download").absolutePath()
        )
        audio = self.userdata.get(self.userdata.CFGS.RESERVE_AUDIO, False)
        passport = self.userdata.get(self.userdata.CFGS.PASSPORT)
        danmaku = self.userdata.get(self.userdata.CFGS.SAVE_DANMAKU, False)
        codec = self.userdata.get(self.userdata.CFGS.VIDEO_CODEC, 7)
        max_thread_count = self.userdata.get(self.userdata.CFGS.MAX_THREAD_COUNT, 4)
        ultra_resolution = self.userdata.get(self.userdata.CFGS.ULTRA_RESOLUTION, False)
        qt_style = self.userdata.get(self.userdata.CFGS.QT_STYLE, "default")
        high_dpi = self.userdata.get(self.userdata.CFGS.APPLY_HIGH_DPI, True)
        only_audio = self.userdata.get(self.userdata.CFGS.DOWNLOAD_AUDIO_ONLY, False)
        disable_title_limit = self.userdata.get(self.userdata.CFGS.DISABLE_TITLE_LENGTH_LIMIT, False)
        self.ui.spin_threads.setValue(max_thread_count)
        self.ui.combo_codec.setCurrentText(video_codec_id[codec])
        self.ui.line_path.setText(path)
        self.ui.check_reserve_audio.setChecked(audio)
        self.ui.check_audio.setChecked(only_audio)
        self.ui.check_danmaku.setChecked(danmaku)
        self.ui.check_hiper.setChecked(ultra_resolution)
        self.ui.line_login.setText("未登录" if passport is None else "已登录")
        self.ui.combo_style.setCurrentText(qt_style)
        self.ui.check_highdpi.setChecked(high_dpi)
        self.ui.check_close_text_len_limit.setChecked(disable_title_limit)

    def save_settings(self):
        path = self.ui.line_path.text()
        audio = self.ui.check_reserve_audio.isChecked()
        danmaku = self.ui.check_danmaku.isChecked()
        codec = video_codec_match[self.ui.combo_codec.currentText()]
        max_thread_count = self.ui.spin_threads.value()
        ultra_resolution = self.ui.check_hiper.isChecked()
        qt_style = self.ui.combo_style.currentText()
        only_audio = self.ui.check_audio.isChecked()
        high_dpi = self.ui.check_highdpi.isChecked()
        disable_title_limit = self.ui.check_close_text_len_limit.isChecked()
        self.userdata.set(self.userdata.CFGS.VIDEO_CODEC, codec)
        self.userdata.set(self.userdata.CFGS.DOWNLOAD_PATH, path)
        self.userdata.set(self.userdata.CFGS.RESERVE_AUDIO, audio)
        self.userdata.set(self.userdata.CFGS.SAVE_DANMAKU, danmaku)
        self.userdata.set(self.userdata.CFGS.MAX_THREAD_COUNT, max_thread_count)
        self.userdata.set(self.userdata.CFGS.ULTRA_RESOLUTION, ultra_resolution)
        self.userdata.set(self.userdata.CFGS.QT_STYLE, qt_style)
        self.userdata.set(self.userdata.CFGS.DOWNLOAD_AUDIO_ONLY, only_audio)
        self.userdata.set(self.userdata.CFGS.APPLY_HIGH_DPI, high_dpi)
        self.userdata.set(self.userdata.CFGS.DISABLE_TITLE_LENGTH_LIMIT, disable_title_limit)
        self.userdata.save()

    def update_tab_changes(self, old, now):
        if old == self.mw_tab_index:
            self.save_settings()
        elif now == self.mw_tab_index:
            self.load_settings()

    # Slot
    def on_path_button_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.ui.line_path.text()
        )
        if len(path) == 0:
            return
        self.ui.line_path.setText(path)

    # Slot
    def on_line_path_changed(self, text):
        if not os.path.isdir(text):
            self.ui.line_path.setStyleSheet(style.BASIC_FONT_STYLE + style.RED_TEXT)
        else:
            self.ui.line_path.setStyleSheet(style.BASIC_FONT_STYLE)

    # Slot
    def on_reset_button_clicked(self):
        dialog = QMessageBox.question(self, "提示", "确定要重置所有设置吗？",
                                      buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      defaultButton=QMessageBox.StandardButton.No)
        if dialog == QMessageBox.StandardButton.Yes:
            configUtils.reSetUserData()
            del self.userdata
            self.userdata = configUtils.UserDataHelper()
            self.load_settings()
            QMessageBox.information(self, "信息", "设置已重置")

    # Slot
    def on_login_button_clicked(self):
        dialog = DialogLogin(self, self.userdata)
        dialog.exec()
        self.load_settings()

    # Slot
    def on_open_config_dir_clicked(self):
        open_folder(QtCore.QDir("data").absolutePath(), self)

    # Slot
    def on_logout_button_clicked(self):
        ret = QMessageBox.question(
            self, "确认", "确认退出登录？",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No)
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            return
        passport = self.userdata.get(self.userdata.CFGS.PASSPORT, None)
        if passport is None:
            QMessageBox.information(self, "信息", "未登录")
            return

        try:
            if "data" not in passport:
                key = self.userdata.get(self.userdata.CFGS.PASSPORT_CRYPT_KEY, None)
                if key is None:
                    raise Exception("无法获取密钥")
                decode = utils.passport.decode_cookie(passport["secure_data"], key)
                if decode is None:
                    raise Exception("处理信息失败")
                passport["data"] = decode
            user.exit_login(utils.passport.BiliPassport(passport["data"]))
            QMessageBox.information(self, "成功", "已退出登录")
        except Exception as e:
            QMessageBox.critical(self, "退出登录失败", "登录信息已清除\n" + str(e))
        self.userdata.set(self.userdata.CFGS.PASSPORT, None)
        self.userdata.set(self.userdata.CFGS.PASSPORT_CRYPT_KEY, None)
        self.userdata.save()
        self.load_settings()
