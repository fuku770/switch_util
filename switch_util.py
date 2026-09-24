from Commands.PythonCommandBase import ImageProcPythonCommand
from Commands.Keys import KeyPress, Button, Hat, Direction
from typing import Optional
from dataclasses import dataclass
import time
import cv2
import numpy as np
import os

Neutral = "0x0003 8 80 80 80 80"  # NEUTRAL
Neutral2 = "0x0000 8 80 80 80 80"  # NEUTRAL
Button_A = "0x0013 8 80 80 80 80"  # A
Lstick_up = "0x0003 8 80 00 80 80"  # LSTICK-UP
Lstick_down = "0x0003 8 80 ff 80 80"  # LSTICK-DOWN
Lstick_left = "0x0003 8 00 80 80 80"  # LSTICK-LEFT
Lstick_right = "0x0003 8 ff 80 80 80"  # LSTICK-RIGHT
Rstick_up = "0x0003 8 80 80 80 00"  # RSTICK-UP
Rstick_down = "0x0003 8 80 80 80 ff"  # RSTICK-DOWN
Rstick_left = "0x0003 8 80 80 00 80"  # RSTICK-LEFT
Rstick_right = "0x0003 8 80 80 ff 80"  # RSTICK-RIGHT

Button_L_click = "0x1000 8"  # L-CLICK
Button_R_click = "0x2000 8"  # R-CLICK
Neutral3 = "0x0000 8"  # NEUTRAL

charlist = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


@dataclass
class _SwitchState:
    """
    Switch_util のメソッド間で受け渡す内部状態
    """

    version: Optional[str] = None  # "switch" / "switch2"。未判定なら None
    theme: Optional[str] = None  # "white" / "black"。未判定なら None
    notice_update: bool = False  # アップデート通知を Discord に送信済みか
    debug: bool = False


class Switch_util(object):

    def __init__(self, commands: ImageProcPythonCommand):
        self.commands = commands
        self._state = _SwitchState(debug=getattr(commands, "debug", False))

    def get_switch_info(self):
        """
        switch1,2およびテーマカラーの判定
        """
        if self._state.version is not None and self._state.theme is not None:
            return
        elif self._state.version is not None:
            while not self.is_home():
                self.commands.press(Button.HOME, 0.06, 1.0)
        else:
            while True:
                src = self.commands.camera.readFrame()
                if self.is_match_template(
                    src, "switch/home.png"
                ) or self.is_match_template(src, "switch2/home.png"):
                    break
                self.commands.press(Button.HOME, 0.06, 1.0)
            if self.is_match_template(src, "switch/home.png"):
                self._state.version = "switch"
            elif self.is_match_template(src, "switch2/home.png"):
                self._state.version = "switch2"
            if self._state.debug:
                print(self._state.version)

        if self._state.theme is None:
            for _ in range(6):
                self.commands.press(Button.B, 0.05, 0.05)
            src = self.commands.camera.readFrame()[510:520, 100:110]
            img_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
            if np.average(img_gray) > 128:
                self._state.theme = "white"
            else:
                self._state.theme = "black"
            if self._state.debug:
                print(self._state.theme)

    def start_soft(self, soft: Optional[str] = None, user_num: Optional[int] = None):
        """
        ソフト起動
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        self.get_switch_info()

        if self._state.version == "switch":
            self.start_soft_for_switch(soft=soft, user_num=user_num)

        else:
            self.start_soft_for_switch2(soft=soft, user_num=user_num)

    def reset_soft(self, user_num: Optional[int] = None):
        """
        ソフトリセット
        ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        self.get_switch_info()

        if self._state.version == "switch":
            self.reset_soft_for_switch(user_num=user_num)
        else:
            self.reset_soft_for_switch2(user_num=user_num)

    def reboot_switch(self):
        """
        スイッチ再起動
        """
        self.get_switch_info()

        if self._state.version == "switch":
            self.reboot_switch_for_switch()
        else:
            self.reboot_switch_for_switch2()

    def start_soft_for_switch(
        self, soft: Optional[str] = None, user_num: Optional[int] = None
    ):
        """
        ソフト起動(switch用)
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, "play_still.png"):
            self.commands.press(Button.X, 0.1, 0.5)
            self.commands.press(Button.A, 0.1, 2.5)
        if not soft == None:
            i = 0
            while not self.is_match_template(
                None, f"{self._state.theme}/soft/{soft}.png"
            ):
                self.commands.press(Hat.RIGHT, 0.1, 0.5)
                i += 1
                if i > 30:
                    print("ソフトのタイトルが見つからないため中断します")
                    self.commands.finish()
                    break
        self.commands.press(Button.A, 0.1, 0.5)

        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(
                src,
                f"{self._state.theme}/user_select.png",
                0.85,
                True,
                [50, 320, 260, 380],
            ):
                break
            if self.is_match_template(src, f"{self._state.theme}/update_notice.png"):
                self.commands.press(Hat.TOP, 0.1, 0.5)
                self.commands.press(Button.A, 0.1, 0.5)
                if not self._state.notice_update:
                    self._state.notice_update = True
                    self.commands.discord_text("アップデート通知")
            elif i % 30 == 0:
                self.commands.press(Button.A, 0.1, 1.5)
            else:
                self.commands.wait(0.3)

        if user_num == None:
            pass
        else:
            while True:
                src = self.commands.camera.readFrame()
                for i in range(8):
                    if self.is_match_template(
                        src,
                        f"{self._state.theme}/user_icon_cursor.png",
                        0.85,
                        True,
                        [30 + 150 * i, 590, 200 + 150 * i, 640],
                    ):
                        cursor_position = i
                        break
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.commands.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.commands.press(Hat.RIGHT, 0.1, 0.2)
        self.commands.press(Button.A, 0.1, 1.0)
        return

    def start_soft_for_switch2(
        self, soft: Optional[str] = None, user_num: Optional[int] = None
    ):
        """
        ソフト起動(switch2用)
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, "play_still.png"):
            self.commands.press(Button.X, 0.1, 0.5)
            self.commands.press(Button.A, 0.1, 2.5)
        if not soft == None:
            i = 0
            while not self.is_match_template(
                None, f"{self._state.theme}/soft/{soft}.png"
            ):
                self.commands.press(Hat.RIGHT, 0.1, 0.5)
                i += 1
                if i > 30:
                    print("ソフトのタイトルが見つからないため中断します")
                    self.commands.finish()
                    break
        self.commands.press(Button.A, 0.1, 0.5)

        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(
                src,
                f"{self._state.theme}/user_select.png",
                0.85,
                True,
                [50, 320, 260, 380],
            ):
                break
            if self.is_match_template(
                src,
                f"{self._state.theme}/update_notice.png",
                0.85,
                True,
                [480, 350, 810, 470],
            ):
                self.commands.press(Hat.TOP, 0.1, 0.5)
                self.commands.press(Button.A, 0.1, 0.5)
                if not self._state.notice_update:
                    self._state.notice_update = True
                    self.commands.discord_text("アップデート通知")
            elif i % 30 == 0:
                self.commands.press(Button.A, 0.1, 1.5)
            else:
                self.commands.wait(0.3)

        if user_num == None:
            pass
        else:
            for _ in range(user_num):
                self.commands.press(Hat.RIGHT, 0.1, 0.2)
            while True:
                start_time = time.perf_counter()
                while time.perf_counter() - start_time < 5:
                    src = self.commands.camera.readFrame()
                    detect_flag, pos = self.get_colored_region_pos(
                        src, True, [0, 410, 1280, 420]
                    )
                    if detect_flag:
                        break
                    detect_flag, pos = self.get_colored_region_pos(
                        src, True, [0, 544, 1280, 554]
                    )
                    if detect_flag:
                        break
                    self.commands.wait(0.1)
                else:
                    print("ユーザー選択に失敗しました")
                    self.commands.finish()
                    break
                cursor_position = (pos[0] - 70) // 141
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.commands.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.commands.press(Hat.RIGHT, 0.1, 0.2)
        self.commands.press(Button.A, 0.1, 1.0)
        return

    def reset_soft_for_switch(self, user_num: Optional[int] = None):
        """
        ソフトリセット(switch用)
        ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, "play_still.png"):
            self.commands.press(Button.Y, 0.1, 0.5)
            self.commands.press(Button.A, 0.1, 0.5)
        else:
            self.commands.press(Button.A, 0.1, 0.5)

        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(
                src,
                f"{self._state.theme}/user_select.png",
                0.85,
                True,
                [50, 320, 260, 380],
            ):
                break
            if self.is_match_template(src, f"{self._state.theme}/update_notice.png"):
                self.commands.press(Hat.TOP, 0.1, 0.5)
                self.commands.press(Button.A, 0.1, 0.5)
                if not self._state.notice_update:
                    self._state.notice_update = True
                    self.commands.discord_text("アップデート通知")
            elif i % 30 == 0:
                self.commands.press(Button.A, 0.1, 1.5)
            else:
                self.commands.wait(0.3)

        if user_num == None:
            pass
        else:
            while True:
                src = self.commands.camera.readFrame()
                for i in range(8):
                    if self.is_match_template(
                        src,
                        f"{self._state.theme}/user_icon_cursor.png",
                        0.85,
                        True,
                        [30 + 150 * i, 590, 200 + 150 * i, 640],
                    ):
                        cursor_position = i
                        break
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.commands.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.commands.press(Hat.RIGHT, 0.1, 0.2)
        self.commands.press(Button.A, 0.1, 1.0)
        return

    def reset_soft_for_switch2(self, user_num: Optional[int] = None):
        """
        ソフトリセット(switch2用)
        ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, "play_still.png"):
            self.commands.press(Button.Y, 0.1, 0.5)
            self.commands.press(Button.A, 0.1, 0.5)
        else:
            self.commands.press(Button.A, 0.1, 0.5)

        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(
                src,
                f"{self._state.theme}/user_select.png",
                0.85,
                True,
                [50, 320, 260, 380],
            ):
                break
            if self.is_match_template(
                src,
                f"{self._state.theme}/update_notice.png",
                0.85,
                True,
                [480, 350, 810, 470],
            ):
                self.commands.press(Hat.TOP, 0.1, 0.5)
                self.commands.press(Button.A, 0.1, 0.5)
                if not self._state.notice_update:
                    self._state.notice_update = True
                    self.commands.discord_text("アップデート通知")
            elif i % 30 == 0:
                self.commands.press(Button.A, 0.1, 1.5)
            else:
                self.commands.wait(0.3)

        if user_num == None:
            pass
        else:
            for _ in range(user_num):
                self.commands.press(Hat.RIGHT, 0.1, 0.2)
            while True:
                start_time = time.perf_counter()
                while time.perf_counter() - start_time < 5:
                    src = self.commands.camera.readFrame()
                    detect_flag, pos = self.get_colored_region_pos(
                        src, True, [0, 410, 1280, 420]
                    )
                    if detect_flag:
                        break
                    detect_flag, pos = self.get_colored_region_pos(
                        src, True, [0, 544, 1280, 554]
                    )
                    if detect_flag:
                        break
                    self.commands.wait(0.1)
                else:
                    print("ユーザー選択に失敗しました")
                    self.commands.finish()
                    break
                cursor_position = (pos[0] - 70) // 141
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.commands.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.commands.press(Hat.RIGHT, 0.1, 0.2)
        self.commands.press(Button.A, 0.1, 1.0)
        return

    def reboot_switch_for_switch(self):
        """
        スイッチ再起動(switch用)
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        while True:
            self.move_to_setting_menu()
            # 言語を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Neutral, wait=0.3)
            self.commands.press(Direction.DOWN, 0.20, 0.1)
            for _ in range(3):
                if self.is_match_template(
                    None, f"{self._state.theme}/select_langage_change.png", 0.9
                ):
                    break
                else:
                    self.commands.press(Direction.DOWN, 0.04, 0.1)
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50)
            # 正常に言語を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(
                None,
                f"{self._state.theme}/check_langage_change.png",
                0.9,
                True,
                [44, 132, 148, 198],
            ):
                break
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
        # 再起動処理（中国語に変更）
        self.commands.press(Hat.BTM, 0.1, 1.0)
        for _ in range(2):
            self.commands.press(Button.A, 0.1, 1.0)
        while not self.is_home():
            for _ in range(10):
                self.commands.press(Button.B, 0.05, 0.05)

        while True:
            self.move_to_setting_menu()
            # 言語を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Neutral, wait=0.3)
            self.commands.press(Direction.DOWN, 0.20, 0.1)
            for _ in range(3):
                if self.is_match_template(
                    None, f"{self._state.theme}/select_langage_change_cn.png", 0.9
                ):
                    break
                else:
                    self.commands.press(Direction.DOWN, 0.04, 0.1)
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50)
            # 正常に言語を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(
                None,
                f"{self._state.theme}/check_langage_change_cn.png",
                0.9,
                True,
                [44, 132, 148, 198],
            ):
                break
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
        # 再起動処理（日本語に戻す）
        self.commands.press(Hat.TOP, 0.1, 1.0)
        for _ in range(2):
            self.commands.press(Button.A, 0.1, 1.0)
        while not self.is_home():
            for _ in range(10):
                self.commands.press(Button.B, 0.05, 0.05)

    def reboot_switch_for_switch2(self):
        """
        スイッチ再起動(switch2用)
        国内版に再起動コマンドは存在しない（はず）
        """
        pass

    def is_home(self):
        if self._state.version is not None:
            return self.is_match_template(None, "home.png")
        else:
            src = self.commands.camera.readFrame()
            return self.is_match_template(
                src, "switch/home.png"
            ) or self.is_match_template(src, "switch2/home.png")

    def is_match_template(
        self,
        base_image=None,  # (Optional) 基本となる画像。型: np.array または None
        template=None,  # テンプレート画像またはテンプレート画像のファイル名。型: np.array, str または None
        threshold=0.85,  # 類似度の閾値。型: float
        trim=False,  # 画像をトリムするかどうかのフラグ。型: bool
        trim_area=[
            0,
            0,
            1280,
            720,
        ],  # トリムする領域 [x, y, width, height]。型: List[int]
        show_debug_image=False,  # デバッグ画像を表示するかどうかのフラグ。型: bool
        use_gray=True,  # グレースケール画像を使用するかのフラグ。型: bool
        ZNCC_string="",  # ZNCCの表示用文字列。型: str
        other_trim_offset=np.array(
            [0, 0]
        ),  # srcを事前にトリムしていた場合のオフセット量。型: np.array
    ) -> bool:
        """
        画像判定関数
        """
        if self._state.version is not None:
            TEMPLATE_PATH = (
                f"./Commands/PythonCommands/switch_util/image/{self._state.version}/"
            )
        else:
            TEMPLATE_PATH = "./Commands/PythonCommands/switch_util/image/"

        gui = getattr(self.commands, "gui", None)

        # 画像が提供されていない場合、キャプチャする
        if base_image is None:
            base_image = self.commands.camera.readFrame()

        # トリムが指定されている場合、画像をトリムする
        if trim:
            base_image = base_image[
                trim_area[1] : trim_area[3], trim_area[0] : trim_area[2]
            ]

        # グレースケールに変換する場合
        processed_image = (
            cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY) if use_gray else base_image
        )

        # デバッグ画像を表示する場合
        if show_debug_image:
            cv2.imshow("image", processed_image)
            cv2.waitKey()

        path = TEMPLATE_PATH + template
        if isinstance(template, str):
            if not os.path.exists(path):
                print(
                    f"Error：テンプレートファイル{template}がディレクトリに存在していません"
                )
                return False
        template_image = cv2.imread(
            path, cv2.IMREAD_GRAYSCALE if use_gray else cv2.IMREAD_COLOR
        )

        method = cv2.TM_CCOEFF_NORMED
        w, h = template_image.shape[1], template_image.shape[0]
        res = cv2.matchTemplate(processed_image, template_image, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if self._state.debug:
            if ZNCC_string == "" and isinstance(template, str):
                ZNCC_string = template
            print(ZNCC_string + " ZNCCの値: " + str(max_val))

        tag2 = str(time.perf_counter()) + "2"
        if trim and gui:
            gui.delete("ImageRecRect")
            gui.ImgRect(
                *(np.array([trim_area[0], trim_area[1]])),
                *(np.array([trim_area[2], trim_area[3]])),
                outline="orange",
                tag=tag2,
                ms=1500,
            )

        if max_val > threshold:
            top_left = (
                np.array(max_loc)
                + np.array([trim_area[0], trim_area[1]])
                + other_trim_offset
            )
            bottom_right = (top_left[0] + w, top_left[1] + h)

            if gui:
                tag = str(time.perf_counter())
                gui.delete("ImageRecRect")
                gui.ImgRect(
                    *top_left, *bottom_right, outline="blue", tag=tag, ms=1500
                )
            return True
        return False

    def is_pos_match_template(
        self,
        base_image=None,  # (Optional) 基本となる画像。型: np.array または None
        template=None,  # テンプレート画像またはテンプレート画像のファイル名。型: np.array, str または None
        threshold=0.85,  # 類似度の閾値。型: float
        trim=False,  # 画像をトリムするかどうかのフラグ。型: bool
        trim_area=[
            0,
            0,
            1280,
            720,
        ],  # トリムする領域 [x, y, width, height]。型: List[int]
        show_debug_image=False,  # デバッグ画像を表示するかどうかのフラグ。型: bool
        use_gray=True,  # グレースケール画像を使用するかのフラグ。型: bool
        ZNCC_string="",  # ZNCCの表示用文字列。型: str
        other_trim_offset=np.array(
            [0, 0]
        ),  # srcを事前にトリムしていた場合のオフセット量。型: np.array
    ) -> tuple[bool, np.ndarray]:
        """
        画像判定関数
        """
        if self._state.version is not None:
            TEMPLATE_PATH = (
                f"./Commands/PythonCommands/switch_util/image/{self._state.version}/"
            )
        else:
            TEMPLATE_PATH = "./Commands/PythonCommands/switch_util/image/"

        gui = getattr(self.commands, "gui", None)

        # 画像が提供されていない場合、キャプチャする
        if base_image is None:
            base_image = self.commands.camera.readFrame()

        # トリムが指定されている場合、画像をトリムする
        if trim:
            base_image = base_image[
                trim_area[1] : trim_area[3], trim_area[0] : trim_area[2]
            ]

        # グレースケールに変換する場合
        processed_image = (
            cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY) if use_gray else base_image
        )

        # デバッグ画像を表示する場合
        if show_debug_image:
            cv2.imshow("image", processed_image)
            cv2.waitKey()

        path = TEMPLATE_PATH + template
        if isinstance(template, str):
            if not os.path.exists(path):
                print(
                    f"Error：テンプレートファイル{template}がディレクトリに存在していません"
                )
                return False, np.array([0, 0])
        template_image = cv2.imread(
            path, cv2.IMREAD_GRAYSCALE if use_gray else cv2.IMREAD_COLOR
        )

        method = cv2.TM_CCOEFF_NORMED
        w, h = template_image.shape[1], template_image.shape[0]
        res = cv2.matchTemplate(processed_image, template_image, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if self._state.debug:
            if ZNCC_string == "" and isinstance(template, str):
                ZNCC_string = template
            print(ZNCC_string + " ZNCCの値: " + str(max_val))

        tag2 = str(time.perf_counter()) + "2"
        if trim and gui:
            gui.delete("ImageRecRect")
            gui.ImgRect(
                *(np.array([trim_area[0], trim_area[1]])),
                *(np.array([trim_area[2], trim_area[3]])),
                outline="orange",
                tag=tag2,
                ms=1500,
            )

        if max_val > threshold:
            top_left = (
                np.array(max_loc)
                + np.array([trim_area[0], trim_area[1]])
                + other_trim_offset
            )
            bottom_right = (top_left[0] + w, top_left[1] + h)

            if gui:
                tag = str(time.perf_counter())
                gui.delete("ImageRecRect")
                gui.ImgRect(
                    *top_left, *bottom_right, outline="blue", tag=tag, ms=1500
                )
            return True, top_left + np.array([w / 2, h / 2]).astype(int)
        return False, np.array([0, 0])

    def get_colored_region_pos(
        self,
        base_image=None,
        trim=False,
        trim_area=[0, 0, 1280, 720],
        show_debug_image=False,
        min_area=10,
    ) -> tuple[bool, np.ndarray]:
        """
        白または黒背景から色付き領域の中心座標を取得する
        """

        gui = getattr(self.commands, "gui", None)

        # 画像取得
        if base_image is None:
            base_image = self.commands.camera.readFrame()

        # トリム
        if trim:
            base_image = base_image[
                trim_area[1] : trim_area[3], trim_area[0] : trim_area[2]
            ]

        # グレースケール変換
        gray = cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY)

        # 背景色判定（平均輝度で判断）
        mean_val = np.mean(gray)

        if mean_val > 127:
            # 白背景 → 暗い部分が対象
            _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        else:
            # 黒背景 → 明るい部分が対象
            _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

        # ノイズ除去
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        if show_debug_image:
            cv2.imshow("mask", mask)
            cv2.waitKey()

        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return False, np.array([0, 0])

        # 最大領域を取得
        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) < min_area:
            return False, np.array([0, 0])

        x, y, w, h = cv2.boundingRect(largest)

        center = np.array([x + w // 2, y + h // 2])

        # トリム補正
        if trim:
            center += np.array([trim_area[0], trim_area[1]])
        if trim and gui:
            tag2 = str(time.perf_counter())
            gui.delete("ImageRecRect")
            gui.ImgRect(
                *(np.array([trim_area[0], trim_area[1]])),
                *(np.array([trim_area[2], trim_area[3]])),
                outline="orange",
                tag=tag2,
                ms=1500,
            )

        draw_x = x
        draw_y = y

        if trim:
            draw_x += trim_area[0]
            draw_y += trim_area[1]

        if gui:
            tag = str(time.perf_counter())
            gui.delete("ImageRecRect")
            gui.ImgRect(
                draw_x, draw_y, draw_x + w, draw_y + h, outline="blue", tag=tag, ms=1500
            )

        return True, center

    def return_from_date_and_time_setting(self):
        """
        HOMEからゲーム画面に戻る
        """
        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 2.0)
        while self.is_home():
            self.commands.press(Button.HOME, 0.06, 2.0)

    def move_to_date_and_time_setting(self, reset_time=False):
        """
        日時変更画面まで移動する
        reset_time 現在時刻に戻す
        """

        print("日時を変更します")

        self.get_switch_info()

        if self._state.version == "switch":
            self.move_to_date_and_time_setting_for_switch(reset_time=reset_time)
        else:
            self.move_to_date_and_time_setting_for_switch2(reset_time=reset_time)

    def move_to_date_and_time_setting_for_switch(self, reset_time: bool):
        """
        日時変更画面まで移動する(switch用)
        reset_time 現在時刻に戻す
        """

        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        while True:
            self.move_to_setting_menu()
            # 日付と時刻を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Neutral, wait=0.3)
            self.commands.press(Hat.BTM, duration=0.56, wait=0.1)
            for _ in range(5):
                if self.is_match_template(
                    None, f"{self._state.theme}/select_date_change.png", 0.9
                ):
                    break
                else:
                    self.commands.press(Hat.BTM, 0.036, 0.2)
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50)

            # 正常に日付と時刻を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(
                None,
                f"{self._state.theme}/check_change.png",
                0.9,
                True,
                [65, 31, 168, 101],
            ):
                break
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)

        if reset_time:
            for _ in range(2):
                self.commands.press(Button.A, 0.1, 0.5)
            print("現在時刻に戻しました")
            return

        # インターネットに同期するにチェックがあったらoffに切り替える
        if self.is_match_template(None, f"{self._state.theme}/on.png", 0.9):
            self.commands.press(Button.A, wait=1.0)

        # 現在の日付と時刻を選択
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)

    def move_to_date_and_time_setting_for_switch2(self, reset_time: bool):
        """
        日時変更画面まで移動する(switch2用)
        reset_time 現在時刻に戻す
        """

        while not self.is_home():
            self.commands.press(Button.HOME, 0.06, 1.0)

        while True:
            self.move_to_setting_menu()
            # 日付と時刻を選択
            wait_time = 0.1
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Neutral, wait=0.3)
            for _ in range(5):
                if self.is_match_template(
                    None, f"{self._state.theme}/select_date_change.png", 0.9
                ):
                    break
                else:
                    self.commands.press(Hat.BTM, 0.036, 0.2)
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50)

            # 正常に日付と時刻を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(
                None,
                f"{self._state.theme}/check_change.png",
                0.9,
                True,
                [69, 27, 118, 78],
            ):
                break
            else:
                self.commands.press(Button.HOME, 0.1, 1.0)

        if reset_time:
            for _ in range(2):
                self.commands.press(Button.A, 0.1, 0.5)
            print("現在時刻に戻しました")
            return

        # インターネットに同期するにチェックがあったらoffに切り替える
        if self.is_match_template(
            None, f"{self._state.theme}/on.png", 0.9, True, [949, 107, 1106, 225]
        ):
            self.commands.press(Button.A, wait=1.0)

        # 現在の日付と時刻を選択
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)

    def ensure_date_and_time_changeable(self):
        """
        必ず日時変更可能な状態にする
        """
        self.commands.wait(0.5)
        while True:
            if self.is_match_template(
                None, f"{self._state.theme}/change_date.png", 0.9
            ):
                break
            elif self.is_match_template(
                None,
                f"{self._state.theme}/check_change.png",
                0.9,
                True,
                (
                    [65, 31, 168, 101]
                    if self._state.version == "switch"
                    else [69, 27, 118, 78]
                ),
            ):
                pass
            else:
                print("日時変更画面に入れませんでした\nプログラムを終了します")
                self.commands.finish()
            if self.is_match_template(
                None,
                f"{self._state.theme}/on.png",
                0.9,
                False if self._state.version == "switch" else True,
                [949, 107, 1106, 225],
            ):
                self.send_command(Lstick_up, wait=0.04)
                self.send_command(Rstick_up, wait=0.04)
                self.commands.press(Button.A, duration=0.1, wait=0.5)
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.commands.press(Button.A, duration=0.1, wait=0.5)

    def change_date_and_time(
        self,
        target_year,
        target_month,
        target_day,
        target_hour,
        target_minute,
        init=False,
    ):
        """
        指定した日時に変更
        th | 日時検出閾値
        """
        th = 0.9
        self.send_command(
            Button_A, wait=0.04
        )  # 時刻変更でminを変更しない場合はwaitを大きくすること。
        self.send_command(Neutral, wait=0.20)

        if init and self._state.version == "switch":
            self.send_command(Rstick_left, wait=0.04)
            self.send_command(Lstick_left, wait=0.04)
            self.send_command(Rstick_left, wait=0.04)
            self.send_command(Lstick_left, wait=0.04)
            self.send_command(Rstick_left, wait=0.04)
        self.send_command(Neutral, wait=0.50)

        while True:
            # 選択している部分(年)とその他を別々に検知する。
            date_upper = self.check_date(0, th=th)
            date_lower = self.check_date(1, th=th)
            date = date_upper + date_lower
            if len(date) == 12:
                break
            else:
                th = th - 0.01
            if th < 0.8:
                print("日時認識に失敗しました\nプログラムを終了します")
                self.commands.finish()

        current_year = int(date[0:4])
        current_month = int(date[4:6])
        current_day = int(date[6:8])
        current_hour = int(date[8:10])
        current_minute = int(date[10:12])

        year_offset = target_year - current_year

        month_offset = target_month - current_month
        if month_offset > 6:
            month_offset = month_offset - 12
        elif month_offset < -6:
            month_offset = month_offset + 12

        # 時間変更画面(1)
        self.change_value(year_offset)
        self.send_command(Lstick_right, wait=0.04)
        self.change_value(month_offset)
        self.send_command(Neutral, wait=0.10)

        self.commands.wait(0.4)

        while True:
            date_lower2 = self.check_date(2, th=th)
            if len(date_lower2) == 6:
                break
            else:
                th = th - 0.01
            if th < 0.8:
                print("日時認識に失敗しました\nプログラムを終了します")
                self.commands.finish()

        current_day = int(date_lower2[0:2])
        current_hour = int(date_lower2[2:4])
        current_minute = int(date_lower2[4:6])

        day_offset = target_day - current_day
        if target_month in [1, 3, 5, 7, 8, 10, 12]:
            a = [15, 31]
        elif target_month in [4, 6, 9, 11]:
            a = [15, 30]
        else:
            a = [14, 28] if target_year % 4 != 0 else [14, 29]
        if day_offset > a[0]:
            day_offset = day_offset - a[1]
        elif day_offset < -a[0]:
            day_offset = day_offset + a[1]

        hour_offset = target_hour - current_hour
        if hour_offset > 12:
            hour_offset = hour_offset - 24
        elif hour_offset < -12:
            hour_offset = hour_offset + 24

        min_offset = target_minute - current_minute
        if min_offset > 30:
            min_offset = min_offset - 60
        elif min_offset < -30:
            min_offset = min_offset + 60

        self.send_command(Rstick_right, wait=0.04)
        self.change_value(day_offset)
        self.send_command(Lstick_right, wait=0.04)
        self.change_value(hour_offset)
        self.send_command(Rstick_right, wait=0.04)
        self.change_value(min_offset)
        self.send_command(Lstick_right, wait=0.04)
        self.send_command(Button_A, wait=0.04)
        self.send_command(Neutral, wait=0.25)  # HOME画面に戻らない場合は要調整。

    def move_to_setting_menu(self):
        """
        設定メニューまで移動する
        """
        if self._state.version == "switch":
            self.move_to_setting_menu_for_switch()
        else:
            self.move_to_setting_menu_for_switch2()

    def move_to_setting_menu_for_switch(self):
        """
        設定メニューまで移動する(switch用)
        """
        # ゲーム選択画面⇒設定
        self.send_command(Lstick_left, wait=0.04)
        self.send_command(Neutral, wait=0.16)  # 設定画面に移動できない場合は要調整。
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Lstick_left, wait=0.04)
        self.send_command(Button_A, wait=0.80)

        # 設定の一番下まで移動
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Rstick_down, wait=0.04)
        self.send_command(Button_A, wait=0.20)

    def move_to_setting_menu_for_switch2(self):
        """
        設定メニューまで移動する(switch2用)
        """
        # ゲーム選択画面⇒設定
        self.send_command(Lstick_left, wait=0.04)
        self.send_command(Neutral, wait=0.16)  # 設定画面に移動できない場合は要調整。
        self.send_command(Lstick_down, wait=0.04)
        self.send_command(Lstick_left, wait=0.04)
        self.send_command(Button_A, wait=0.80)

        # 設定の一番下まで移動
        wait_time = 0.1
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Button_A, wait=0.20)

    def check_date(self, num, th=0.9):
        """
        日時検出(OCR不使用)
        """
        TEMPLATE_PATH = (
            f"./Commands/PythonCommands/switch_util/image/{self._state.version}/"
        )

        src = self.commands.camera.readFrame()
        if self._state.version == "switch":
            if num == 0:
                src = src[437:500, 182:336]
                sel_color = 0  # 選択時
            elif num == 1:
                src = src[437:500, 336:887]
                sel_color = 1  # 非選択時
            elif num == 2:
                src = src[437:500, 474:887]
                sel_color = 1  # 非選択時
            else:
                src = src[437:500, 182:887]
                sel_color = 1  # 非選択時
        else:
            if num == 0:
                src = src[320:370, 170:300]
                sel_color = 0  # 選択時
            elif num == 1:
                src = src[320:370, 360:900]
                sel_color = 1  # 非選択時
            elif num == 2:
                src = src[320:370, 480:900]
                sel_color = 1  # 非選択時
            else:
                src = src[320:370, 170:900]
                sel_color = 1  # 非選択時

        img_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

        box = []
        for test in charlist:
            char_file_name = (
                TEMPLATE_PATH + f"{self._state.theme}/character/{test}_{sel_color}.png"
            )
            if os.path.exists(char_file_name):
                template = cv2.imread(char_file_name)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                # 処理対象画像に対して、テンプレート画像との類似度を算出する
                res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                # 類似度の高い部分を検出する
                threshold = th
                loc = np.where(res >= threshold)
                max_val = np.max(res)
                try:
                    loc_sorted = sorted(loc[1])
                    box.append([loc_sorted[0], test, max_val])
                    box_temp = [loc_sorted[0]]
                    for i in loc_sorted[1:]:
                        for j in box_temp:
                            if abs(i - j) > 5:
                                box.append([i, test, max_val])
                                box_temp = [i]
                except Exception:
                    pass
            else:
                pass
        box.sort(key=lambda x: x[0])
        text = ""
        for i in box:
            flag = True
            for j in box:
                if abs(i[0] - j[0]) < 5 and i != j:
                    if i[2] < j[2]:
                        flag = False
            if flag:
                text = text + i[1]
        return text

    def change_value(self, cnt):
        """
        高速日時変更(数値変更部分)
        """
        if self._state.version == "switch":
            wait_time = 0.04
        else:
            wait_time = 0.1
        if cnt == 0:
            pass
        elif cnt > 0:
            for i in range(cnt):
                if i % 2 == 0:
                    self.send_command(Lstick_up, wait=wait_time)
                else:
                    self.send_command(Rstick_up, wait=wait_time)
        else:
            for i in range(-cnt):
                if i % 2 == 0:
                    self.send_command(Lstick_down, wait=wait_time)
                else:
                    self.send_command(Rstick_down, wait=wait_time)
        return

    def add_1year(self, ensure_change=False):
        """
        年を1年増やす
        """
        if self._state.version == "switch":
            wait_time = 0.04
            if ensure_change:
                self.ensure_date_and_time_changeable()
            else:
                self.commands.press(Button.A, wait=wait_time)
                self.send_command(Rstick_down, wait=wait_time)
                self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_up, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Neutral, wait=wait_time * 2)
            self.commands.press(Button.A, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Neutral, wait=wait_time * 2)
        else:
            self.add_1year_once(ensure_change=ensure_change)

    def add_1year_once(self, ensure_change=False):
        """
        年を1年増やす(初回)
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.commands.press(Button.A, wait=0.1)
        self.send_command(Lstick_up, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Neutral, wait=wait_time * 2)
        self.commands.press(Button.A, wait=wait_time * 3)

    def set_year_2000(self, ensure_change=False):
        """
        2000年に戻す
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.16)
        if self._state.version == "switch":
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            for _ in range(31):
                self.send_command(Lstick_down, wait=wait_time)
                self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.20)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
        else:
            for _ in range(31):
                self.send_command(Lstick_down, wait=0.1)
                self.send_command(Rstick_down, wait=0.1)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.20)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)

    def set_year_2060(self, ensure_change=False):
        """
        2060年にする
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.16)
        if self._state.version == "switch":
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            for _ in range(31):
                self.send_command(Lstick_up, wait=wait_time)
                self.send_command(Rstick_up, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.20)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
        else:
            for _ in range(31):
                self.send_command(Lstick_up, wait=0.1)
                self.send_command(Rstick_up, wait=0.1)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Button_A, wait=wait_time)
            self.send_command(Neutral, wait=0.20)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)

    def add_1day(self, ensure_change=False):
        """
        日を1日増やす
        """
        if self._state.version == "switch":
            wait_time = 0.04
            if ensure_change:
                self.ensure_date_and_time_changeable()
            else:
                self.commands.press(Button.A, wait=wait_time)
                self.send_command(Rstick_down, wait=wait_time)
                self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_left, wait=wait_time)
            self.send_command(Rstick_left, wait=wait_time)
            self.send_command(Lstick_up, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Lstick_right, wait=wait_time)
            self.send_command(Rstick_right, wait=wait_time)
            self.send_command(Neutral, wait=wait_time)
            self.commands.press(Button.A, wait=wait_time)
            self.send_command(Rstick_down, wait=wait_time)
            self.send_command(Lstick_down, wait=wait_time)
            self.send_command(Neutral, wait=wait_time)
        else:
            self.add_1day_once(ensure_change=ensure_change)

    def add_1day_once(self, ensure_change=False):
        """
        日を1日増やす
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.commands.press(Button.A, wait=0.1)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_up, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Neutral, wait=wait_time * 2)
        self.commands.press(Button.A, wait=wait_time)
        self.send_command(Rstick_down, wait=wait_time)
        self.send_command(Lstick_down, wait=wait_time)
        self.send_command(Neutral, wait=wait_time)

    def add_1day_once_end(self, ensure_change=False):
        """
        日を1日増やす
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.commands.press(Button.A, wait=0.1)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_up, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Neutral, wait=wait_time * 2)
        self.commands.press(Button.A, wait=0.1)

    def no_change_year_and_date(self, ensure_change=False):
        """
        年と日を変更しない
        """
        wait_time = 0.04
        if ensure_change:
            self.ensure_date_and_time_changeable()
        else:
            self.commands.press(Button.A, wait=0.1)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Lstick_right, wait=wait_time)
        self.send_command(Rstick_right, wait=wait_time)
        self.send_command(Neutral, wait=wait_time * 2)
        self.commands.press(Button.A, wait=0.1)

    def set_neutral(self):
        """
        黒魔術の終了処理
        """
        self.send_command(Neutral, wait=0.2)
        self.send_command(Neutral, wait=0.2)
        self.send_command(Neutral, wait=0.2)

    def l_click(self):
        """
        黒魔術の終了処理
        """
        self.send_command(Button_L_click, wait=0.055)
        self.send_command(Neutral3, wait=0.05)
        self.send_command(Button_R_click, wait=0.055)
        self.send_command(Neutral3, wait=0.05)

    def send_command(self, row: str, wait: float = 0.04):
        """
        黒魔術関数
        """
        self.commands.keys.ser.ser.write((row + "\r\n").encode("utf-8"))
        time.sleep(wait)
        self.commands.checkIfAlive()
