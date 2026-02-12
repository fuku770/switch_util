from Commands.PythonCommandBase import ImageProcPythonCommand
from Commands.Keys import KeyPress, Button, Hat, Direction, Stick
from typing import List, Optional, Union
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


class Switch_util(object):

    def __init__(self, commands: ImageProcPythonCommand):
        self.commands = commands
        if hasattr(self.commands, 'debug'):
            self.debug = self.commands.debug
        else:
            self.debug = False
    

    def get_switch_info(self):
        """
        switch1,2およびテーマカラーの判定
        """
        if hasattr(self, "switch_version") and hasattr(self, "switch_theme"):
            return
        elif hasattr(self, "switch_version"):
            while not self.is_home():
                self.press(Button.HOME, 0.06, 1.0)
        else:
            while True:
                src = self.commands.camera.readFrame()
                if self.is_match_template(src, 'switch/home.png') or self.is_match_template(src, 'switch2/home.png'):
                    break
                self.press(Button.HOME, 0.06, 1.0)
            if self.is_match_template(src, 'switch/home.png'):
                self.switch_version = 'switch'
            elif self.is_match_template(src, 'switch2/home.png'):
                self.switch_version = 'switch2'
            if self.debug:
                print(self.switch_version)
        
        if not hasattr(self, 'switch_theme'):
            for _ in range(6) : self.press(Button.B, 0.05, 0.05)
            src = self.commands.camera.readFrame()[510:520, 100:110]
            img_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
            if np.average(img_gray) > 128:
                self.switch_theme = 'white'
            else:
                self.switch_theme = 'black'
            if self.debug:
                print(self.switch_theme)

    def start_soft(self, soft: Optional[str] = None, user_num: Optional[int] = None):
        """ 
        ソフト起動
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        self.get_switch_info()

        if self.switch_version == 'switch':
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

        if self.switch_version == 'switch':
            self.reset_soft_for_switch(user_num=user_num)
        else:
            self.reset_soft_for_switch2(user_num=user_num)

    def reboot_switch(self):
        """
        スイッチ再起動
        """
        self.get_switch_info()

        if self.switch_version == 'switch':
            self.reboot_switch_for_switch()
        else:
            self.reboot_switch_for_switch2()


    

    def start_soft_for_switch(self, soft: Optional[str] = None, user_num: Optional[int] = None):
        """ 
        ソフト起動(switch用)
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, 'play_still.png'):
            self.press(Button.X, 0.1, 0.5)
            self.press(Button.A, 0.1, 2.5)
        if not soft == None:
            i = 0
            while not self.is_match_template(None, f'{self.switch_theme}/soft/{soft}.png'):
                self.press(Hat.RIGHT, 0.1, 0.5)
                i += 1
                if i > 30:
                    print('ソフトのタイトルが見つからないため中断します')
                    self.finish()
                    break
        self.press(Button.A, 0.1, 0.5)
        
        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(src, f'{self.switch_theme}/user_select.png', 0.85, True, [50, 320, 260, 380]):
                break
            if self.is_match_template(src, f'{self.switch_theme}/update_notice.png'):
                self.press(Hat.TOP, 0.1, 0.5)
                self.press(Button.A, 0.1, 0.5)
                if not hasattr(self, 'notice_update'):
                    self.notice_update = True
                    self.commands.discord_text('アップデート通知')
            elif i % 30 == 0:
                self.press(Button.A, 0.1, 1.5)
            else:
                self.wait(0.3)

        if user_num == None:
            pass
        else:
            while True:
                src = self.commands.camera.readFrame()
                for i in range(8):
                    if self.is_match_template(src, f'{self.switch_theme}/user_icon_cursor.png',
                                            0.85, True, [30+150*i, 590, 200+150*i, 640]):
                        cursor_position = i
                        break
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.press(Hat.RIGHT, 0.1, 0.2)
        self.press(Button.A, 0.1, 1.0)
        return

    def start_soft_for_switch2(self, soft: Optional[str] = None, user_num: Optional[int] = None):
        """ 
        ソフト起動(switch2用)
        soft : ソフト選択機能あり, ex. "sword", "shield", "home", "violet", "scarlet"
        soft=Noneのとき選択機能は無効化
        user_num : ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        pass

    def reset_soft_for_switch(self, user_num: Optional[int] = None):
        """ 
        ソフトリセット(switch用)
        ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        while not self.is_home():
            self.press(Button.HOME, 0.06, 1.0)

        if self.is_match_template(None, 'play_still.png'):
            self.press(Button.Y, 0.1, 0.5)
            self.press(Button.A, 0.1, 0.5)
        else:
            self.press(Button.A, 0.1, 0.5)

        i = 0
        while True:
            i += 1
            src = self.commands.camera.readFrame()
            if self.is_match_template(src, f'{self.switch_theme}/user_select.png', 0.85, True, [50, 320, 260, 380]):
                break
            if self.is_match_template(src, f'{self.switch_theme}/update_notice.png'):
                self.press(Hat.TOP, 0.1, 0.5)
                self.press(Button.A, 0.1, 0.5)
                if not hasattr(self, 'notice_update'):
                    self.notice_update = True
                    self.commands.discord_text('アップデート通知')
            elif i % 30 == 0:
                self.press(Button.A, 0.1, 1.5)
            else:
                self.wait(0.3)
        
        if user_num == None:
            pass
        else:
            while True:
                src = self.commands.camera.readFrame()
                for i in range(8):
                    if self.is_match_template(src, f'{self.switch_theme}/user_icon_cursor.png',
                                            0.85, True, [30+150*i, 590, 200+150*i, 640]):
                        cursor_position = i
                        break
                n = cursor_position - user_num
                if n == 0:
                    break
                elif n > 0:
                    for _ in range(n):
                        self.press(Hat.LEFT, 0.1, 0.2)
                else:
                    for _ in range(abs(n)):
                        self.press(Hat.RIGHT, 0.1, 0.2)
        self.press(Button.A, 0.1, 1.0)
        return

    def reset_soft_for_switch2(self, user_num: Optional[int] = None):
        """ 
        ソフトリセット(switch2用)
        ユーザー選択機能あり
        user_num=Noneのとき選択機能は無効化
        """
        pass

    def reboot_switch_for_switch(self):
        """
        スイッチ再起動(switch用)
        """
        while not self.is_home():
            self.press(Button.HOME, 0.06, 1.0)

        while True:
            self.move_to_setting_menu()
            # 言語を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Neutral, wait=0.3)
            self.press(Direction.DOWN, 0.20, 0.1)
            for _ in range(3):
                if self.is_match_template(None, f'{self.switch_theme}/select_langage_change.png', 0.9):
                    break
                else:
                    self.press(Direction.DOWN, 0.04, 0.1)
            else:
                self.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50) 
            # 正常に言語を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(None, f'{self.switch_theme}/check_langage_change.png', 0.9, True, [44, 132, 148, 198]):
                break
            else:
                self.press(Button.HOME, 0.1, 1.0)
        # 再起動処理（中国語に変更）
        self.press(Hat.BTM, 0.1, 1.0)
        for _ in range(2):
            self.press(Button.A, 0.1, 1.0)
        while not self.is_home():
            for _ in range(10):
                self.press(Button.B, 0.05, 0.05)

        while True:
            self.move_to_setting_menu()
            # 言語を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)
            self.send_command(Neutral, wait=0.3)
            self.press(Direction.DOWN, 0.20, 0.1)
            for _ in range(3):
                if self.is_match_template(None, f'{self.switch_theme}/select_langage_change_cn.png', 0.9):
                    break
                else:
                    self.press(Direction.DOWN, 0.04, 0.1)
            else:
                self.press(Button.HOME, 0.1, 1.0)
                continue
            self.send_command(Button_A, wait=0.04)
            self.send_command(Neutral, wait=0.50) 
            # 正常に言語を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
            if self.is_match_template(None, f'{self.switch_theme}/check_langage_change_cn.png', 0.9, True, [44, 132, 148, 198]):
                break
            else:
                self.press(Button.HOME, 0.1, 1.0)
        # 再起動処理（日本語に戻す）
        self.press(Hat.TOP, 0.1, 1.0)
        for _ in range(2):
            self.press(Button.A, 0.1, 1.0)
        while not self.is_home():
            for _ in range(10):
                self.press(Button.B, 0.05, 0.05)

    
    def reboot_switch_for_switch2(self):
        """
        スイッチ再起動(switch2用)
        """
        pass
        

    def is_home(self):
        if hasattr(self, "switch_version"):
            return self.is_match_template(None, 'home.png')
        else:
            src = self.commands.camera.readFrame()
            return self.is_match_template(src, 'switch/home.png') or self.is_match_template(src, 'switch2/home.png')

    def is_match_template(
        self, 
        base_image=None,          # (Optional) 基本となる画像。型: np.array または None
        template=None,            # テンプレート画像またはテンプレート画像のファイル名。型: np.array, str または None
        threshold=0.85,            # 類似度の閾値。型: float
        trim=False,               # 画像をトリムするかどうかのフラグ。型: bool
        trim_area=[0,0,1280,720], # トリムする領域 [x, y, width, height]。型: List[int]
        show_debug_image=False,   # デバッグ画像を表示するかどうかのフラグ。型: bool
        use_gray=True,            # グレースケール画像を使用するかのフラグ。型: bool
        ZNCC_string="",           # ZNCCの表示用文字列。型: str
        other_trim_offset=np.array([0,0]),               # srcを事前にトリムしていた場合のオフセット量。型: np.array
        ) -> bool:
        """
        画像判定関数
        """
        if hasattr(self, 'switch_version'):
            TEMPLATE_PATH = f"./Commands/PythonCommands/switch_util/image/{self.switch_version}/"
        else:
            TEMPLATE_PATH = "./Commands/PythonCommands/switch_util/image/"

        if not hasattr(self.commands, 'gui'):
            self.commands.gui = None

        # 画像が提供されていない場合、キャプチャする
        if base_image is None:
            base_image = self.commands.camera.readFrame()

        # トリムが指定されている場合、画像をトリムする
        if trim:
            base_image = base_image[trim_area[1]:trim_area[3], trim_area[0]:trim_area[2]]

        # グレースケールに変換する場合
        processed_image = cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY) if use_gray else base_image

        # デバッグ画像を表示する場合
        if show_debug_image:
            cv2.imshow("image", processed_image)
            cv2.waitKey()

        path = TEMPLATE_PATH + template
        if isinstance(template, str):
            if not os.path.exists(path):
                print(f"Error：テンプレートファイル{template}がディレクトリに存在していません")
                return False
        template_image = cv2.imread(path, cv2.IMREAD_GRAYSCALE if use_gray else cv2.IMREAD_COLOR)

        method = cv2.TM_CCOEFF_NORMED
        w, h = template_image.shape[1], template_image.shape[0]
        res = cv2.matchTemplate(processed_image, template_image, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if self.debug:
            if ZNCC_string == "" and isinstance(template, str):
                ZNCC_string = template
            print(ZNCC_string + ' ZNCCの値: ' + str(max_val))

        tag2 = str(time.perf_counter())+"2"
        if trim:
            self.commands.gui.delete("ImageRecRect")
            self.commands.gui.ImgRect(*(np.array([trim_area[0],trim_area[1]])),
                            *(np.array([trim_area[2],trim_area[3]])),
                            outline='orange',
                            tag=tag2,
                            ms=1500)

        if max_val > threshold:
            top_left = np.array(max_loc) + np.array([trim_area[0],trim_area[1]])+other_trim_offset
            bottom_right = (top_left[0] + w, top_left[1] + h)

            tag = str(time.perf_counter())
            self.commands.gui.delete("ImageRecRect")
            self.commands.gui.ImgRect(*top_left,
                            *bottom_right,
                            outline='blue',
                            tag=tag,
                            ms=1500)
            return True
        return False

    def is_pos_match_template(
        self, 
        base_image=None,          # (Optional) 基本となる画像。型: np.array または None
        template=None,            # テンプレート画像またはテンプレート画像のファイル名。型: np.array, str または None
        threshold=0.85,            # 類似度の閾値。型: float
        trim=False,               # 画像をトリムするかどうかのフラグ。型: bool
        trim_area=[0,0,1280,720], # トリムする領域 [x, y, width, height]。型: List[int]
        show_debug_image=False,   # デバッグ画像を表示するかどうかのフラグ。型: bool
        use_gray=True,            # グレースケール画像を使用するかのフラグ。型: bool
        ZNCC_string="",           # ZNCCの表示用文字列。型: str
        other_trim_offset=np.array([0,0]),               # srcを事前にトリムしていた場合のオフセット量。型: np.array
        ) -> tuple[bool, np.ndarray]:
        """
        画像判定関数
        """
        if hasattr(self, 'switch_version'):
            TEMPLATE_PATH = f"./Commands/PythonCommands/switch_util/image/{self.switch_version}/"
        else:
            TEMPLATE_PATH = "./Commands/PythonCommands/switch_util/image/"

        if not hasattr(self.commands, 'gui'):
            self.commands.gui = None

        # 画像が提供されていない場合、キャプチャする
        if base_image is None:
            base_image = self.commands.camera.readFrame()

        # トリムが指定されている場合、画像をトリムする
        if trim:
            base_image = base_image[trim_area[1]:trim_area[3], trim_area[0]:trim_area[2]]

        # グレースケールに変換する場合
        processed_image = cv2.cvtColor(base_image, cv2.COLOR_BGR2GRAY) if use_gray else base_image

        # デバッグ画像を表示する場合
        if show_debug_image:
            cv2.imshow("image", processed_image)
            cv2.waitKey()

        path = TEMPLATE_PATH + template
        if isinstance(template, str):
            if not os.path.exists(path):
                print(f"Error：テンプレートファイル{template}がディレクトリに存在していません")
                return False, np.array([0, 0])
        template_image = cv2.imread(path, cv2.IMREAD_GRAYSCALE if use_gray else cv2.IMREAD_COLOR)

        method = cv2.TM_CCOEFF_NORMED
        w, h = template_image.shape[1], template_image.shape[0]
        res = cv2.matchTemplate(processed_image, template_image, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if self.debug:
            if ZNCC_string == "" and isinstance(template, str):
                ZNCC_string = template
            print(ZNCC_string + ' ZNCCの値: ' + str(max_val))

        tag2 = str(time.perf_counter())+"2"
        if trim:
            self.commands.gui.delete("ImageRecRect")
            self.commands.gui.ImgRect(*(np.array([trim_area[0],trim_area[1]])),
                            *(np.array([trim_area[2],trim_area[3]])),
                            outline='orange',
                            tag=tag2,
                            ms=1500)

        if max_val > threshold:
            top_left = np.array(max_loc) + np.array([trim_area[0],trim_area[1]])+other_trim_offset
            bottom_right = (top_left[0] + w, top_left[1] + h)

            tag = str(time.perf_counter())
            self.commands.gui.delete("ImageRecRect")
            self.commands.gui.ImgRect(*top_left,
                            *bottom_right,
                            outline='blue',
                            tag=tag,
                            ms=1500)
            return True, top_left + np.array([w/2, h/2]).astype(int)
        return False, np.array([0, 0])


    def return_from_date_and_time_setting(self):
        """
        HOMEからゲーム画面に戻る
        """
        while not self.is_home():
            self.press(Button.HOME, 0.06, 1.0)
        while self.is_home():
            self.press(Button.HOME, 0.06, 1.0)

    
    def move_to_date_and_time_setting(self, reset_time=False):
        """
        日時変更画面まで移動する
        reset_time 現在時刻に戻す
        """

        print("日時を変更します") 

        self.get_switch_info()
        while not self.is_home():
            self.press(Button.HOME, 0.06, 1.0)
        
        if self.switch_version == 'switch':
            """
            switch用
            """
            while True:
                self.move_to_setting_menu()
                # 日付と時刻を選択
                self.send_command(Lstick_down, wait=0.04)
                self.send_command(Rstick_down, wait=0.04)
                self.send_command(Neutral, wait=0.3)
                self.press(Direction.DOWN, duration=0.56, wait=0.1)
                for _ in range(5):
                    if self.is_match_template(None, f'{self.switch_theme}/select_date_change.png', 0.9):
                        break
                    else:
                        self.press(Direction.DOWN, 0.04, 0.1)
                else:
                    self.press(Button.HOME, 0.1, 1.0)
                    continue
                self.send_command(Button_A, wait=0.04)
                self.send_command(Neutral, wait=0.50) 

                # 正常に日付と時刻を選択できたかを検知する。入れなかったらHOMEを押して最初からやり直す。
                if self.is_match_template(None, f'{self.switch_theme}/check_change.png', 0.9, True, [65, 31, 168, 101]):
                    break
                else:
                    self.press(Button.HOME, 0.1, 1.0)

            if reset_time : 
                for _ in range(2) : self.press(Button.A, 0.1, 0.5)
                print("現在時刻に戻しました")
                return

            #インターネットに同期するにチェックがあったらoffに切り替える
            if self.is_match_template(None, f'{self.switch_theme}/on.png', 0.9):
                self.press(Button.A, wait=1.0)

            # 現在の日付と時刻を選択
            self.send_command(Lstick_down, wait=0.04)
            self.send_command(Rstick_down, wait=0.04)

        else:
            """
            switch2用
            """
            self.finish()

    def change_date_and_time(self, target_year, target_month, target_day, target_hour, target_minute, init=False):
        """
        指定した日時に変更
        th | 日時検出閾値
        """

        if self.switch_version == 'switch':
            """
            switch用
            """
            th = 0.9
            self.send_command(Button_A, wait=0.04)  # 時刻変更でminを変更しない場合はwaitを大きくすること。
            self.send_command(Neutral, wait=0.20)

            if init:
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
                    self.finish()

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

            self.wait(0.4)

            while True:
                date_lower2 = self.check_date(2, th=th)
                if len(date_lower2) == 6:
                    break
                else:
                    th = th - 0.01
                if th < 0.8:
                    print("日時認識に失敗しました\nプログラムを終了します")
                    self.finish()

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

        else:
            """
            switch2用
            """
            self.finish()



    def move_to_setting_menu(self):
        """
        設定メニューまで移動する
        """
        if self.switch_version == 'switch':
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
        pass



    def check_date(self, num, th=0.9):
        """
        日時検出(OCR不使用)
        """
        TEMPLATE_PATH = f"./Commands/PythonCommands/switch_util/image/{self.switch_version}/"

        src = self.commands.camera.readFrame()
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

        img_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

        box = []
        for test in charlist:
            char_file_name = (TEMPLATE_PATH + f"{self.switch_theme}/character/{test}_{sel_color}.png")
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
        if cnt == 0:
            pass
        elif cnt > 0:
            for i in range(cnt):
                if i % 2 == 0:
                    self.send_command(Lstick_up, wait=0.04)
                else:
                    self.send_command(Rstick_up, wait=0.04)
        else:
            for i in range(-cnt):
                if i % 2 == 0:
                    self.send_command(Lstick_down, wait=0.04)
                else:
                    self.send_command(Rstick_down, wait=0.04)
        return

    def add_1year(self):
        """
        年を1年増やす
        """
        wtime = 0.04
        self.press(Button.A, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_left, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_left, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_up, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Neutral, wait=wtime * 2)
        self.press(Button.A, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Neutral, wait=wtime * 2)

    def add_1year_once(self):
        """
        年を1年増やす(初回)
        """
        wtime = 0.04
        self.press(Button.A, wait=wtime)
        self.send_command(Lstick_up, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Neutral, wait=wtime * 2)
        self.press(Button.A, wait=wtime * 3)

    def init_year(self):
        """
        2000年に戻す
        """
        wtime = 0.04
        self.send_command(Button_A, wait=wtime)
        self.send_command(Neutral, wait=0.16)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_left, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_left, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        for _ in range(30):
            self.send_command(Lstick_down, wait=wtime)
            self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Button_A, wait=wtime)
        self.send_command(Neutral, wait=0.16)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)

    def add_1day(self):
        """
        日を1日増やす
        """
        wtime = 0.04
        self.press(Button.A, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_left, wait=wtime)
        self.send_command(Rstick_left, wait=wtime)
        self.send_command(Lstick_up, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Neutral, wait=wtime)
        self.press(Button.A, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Neutral, wait=wtime)

    def add_1day_once(self):
        """
        日を1日増やす
        """
        wtime = 0.04
        self.press(Button.A, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_up, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Neutral, wait=wtime * 2)
        self.press(Button.A, wait=wtime)
        self.send_command(Rstick_down, wait=wtime)
        self.send_command(Lstick_down, wait=wtime)
        self.send_command(Neutral, wait=wtime)

    def add_1day_once_end(self):
        """
        日を1日増やす
        """
        wtime = 0.04
        self.press(Button.A, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_up, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Lstick_right, wait=wtime)
        self.send_command(Rstick_right, wait=wtime)
        self.send_command(Neutral, wait=wtime * 2)
        self.press(Button.A, wait=0.1)

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


    

    def press(self, buttons: Union[Button, Hat, Stick, Direction], duration: float = 0.1, wait: float = 0.1):
        """
        press関数のラッパー
        """
        self.commands.press(buttons, duration=duration, wait=wait)

    def wait(self, wait: float):
        """
        wait関数のラッパー
        """
        self.commands.wait(wait)

    def hold(self, buttons: Union[Button, Hat, Stick, Direction]):
        """
        hold関数のラッパー
        """
        self.commands.hold(buttons)

    def holdEnd(self, buttons: Union[Button, Hat, Stick, Direction]):
        """
        holdEnd関数のラッパー
        """
        self.commands.holdEnd(buttons)

    def finish(self):
        """
        finish関数のラッパー
        """
        self.commands.finish()

    def checkIfAlive(self):
        """
        checkIFAlive関数のラッパー
        """
        self.commands.checkIfAlive()

    def send_command(self, row: str, wait: float = 0.04):
        """
        黒魔術関数
        """
        self.commands.keys.ser.ser.write((row + "\r\n").encode("utf-8"))
        time.sleep(wait)
        self.checkIfAlive()

    