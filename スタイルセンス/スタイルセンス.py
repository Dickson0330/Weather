import requests
from kivy.network.urlrequest import UrlRequest 
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button 
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock 
from datetime import datetime
import kivy.graphics 
import threading 
from kivy.uix.spinner import Spinner 
import os # 導入 os 模塊用於路徑檢查

API_KEY = "93aea5ae7f71bd9bcbe24bb57b43ad90"
DEFAULT_CITY = "Kobe"
WEATHER_ICON_URL = "https://openweathermap.org/img/wn/{icon_code}@2x.png" 
DEFAULT_ICON_PATH = "images/default.png" 

# -------------------------------------------------------------------
# 獲取應用程式根目錄，用於構建絕對路徑 (解決 Kivy 路徑問題)
app_dir = os.path.dirname(os.path.abspath(__file__))

def get_abs_path(relative_path):
    """將相對路徑轉換為絕對路徑"""
    parts = relative_path.split('/') 
    return os.path.join(app_dir, *parts)
# -------------------------------------------------------------------


class WeatherApp(App):
    def build(self):
        self.city_name = "位置を読み込み中"
        self.temp = None
        self.weather = None
        self.weather_icon_code = "01d"
        self.icon_temp_path = DEFAULT_ICON_PATH
        self.humidity = 0
        self.wind_speed = 0
        self.sunrise = 0
        self.sunset = 0

        # 💥 只有兩種背景圖片，使用絕對路徑
        self.rainy_bg_image = get_abs_path("images/rainy_background.png")  
        self.sunny_bg_image = get_abs_path("images/sunny_background.png")  
        # ⚠️ 移除 cloudy_bg_image 相關定義
        self.current_bg_image = self.sunny_bg_image 

        # 檢查背景圖片是否存在 
        if not os.path.exists(self.rainy_bg_image):
            print(f"警告: 雨天背景圖片 '{self.rainy_bg_image}' 未找到。")
            self.rainy_bg_image = "" 
        if not os.path.exists(self.sunny_bg_image):
            print(f"警告: 晴天背景圖片 '{self.sunny_bg_image}' 未找到。")
            self.sunny_bg_image = "" 
        # ⚠️ 移除 cloudy_bg_image 檢查

        # 確保服裝建議圖也使用絕對路徑
        self.rules = [
            {"temp": (-20, 10), "weather_keywords": ["雨", "雪", "霧"], "advice": "寒くて雨や雪です。ダウンコートや厚手の上着、防水靴をおすすめします。", "image": get_abs_path("images/coat_rain.png")},
            {"temp": (-20, 10), "weather_keywords": [], "advice": "寒く乾燥しています。厚手のコートやダウンをおすすめします。", "image": get_abs_path("images/coat.png")}, 
            {"temp": (11, 20), "weather_keywords": ["雨"], "advice": "涼しく雨です。薄手の上着やウィンドブレーカー、傘を持ちましょう。", "image": get_abs_path("images/long_sleeve_rain.png")}, 
            {"temp": (11, 20), "weather_keywords": [], "advice": "涼しい天気です。薄手の上着や長袖シャツをおすすめします。", "image": get_abs_path("images/long_sleeve.png")},
            {"temp": (21, 25), "weather_keywords": ["雨"], "advice": "暖かく雨が降りそうです。長袖や七分袖に軽めの上着、傘を持ちましょう。", "image": get_abs_path("images/long_sleeve_tshirt_rain.png")}, 
            {"temp": (21, 25), "weather_keywords": [], "advice": "過ごしやすい気温です。長袖や七分袖に軽い上着が良いでしょう。", "image": get_abs_path("images/long_sleeve_tshirt.png")}, 
            {"temp": (26, 40), "weather_keywords": ["雨", "雷"], "advice": "暑くて雨です。半袖、短パンで涼しくし、傘を持ちましょう。", "image": get_abs_path("images/tshirt_rain.png")}, 
            {"temp": (26, 40), "weather_keywords": [], "advice": "暑い日です。半袖やスカートなど涼しい服装をおすすめします。", "image": get_abs_path("images/tshirt.png")},
        ]

        # 💥 移除 padding 和 spacing，讓背景鋪滿整個視窗
        main_layout = BoxLayout(orientation='vertical', padding=0, spacing=0) 
        
        # 設定 main_layout 的背景圖片
        main_layout.bind(size=self._update_bg_rect, pos=self._update_bg_rect)
        with main_layout.canvas.before:
            # 💥 透明度設為 1.0 (100% 不透明)
            kivy.graphics.Color(1, 1, 1, 1) 
            self.bg_rect = kivy.graphics.Rectangle(source=self.current_bg_image, 
                                                   pos=main_layout.pos, 
                                                   size=main_layout.size)

        # 接下來的佈局元件需要自己設定間距，如果需要的話
        top_layout = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=10, padding=15) # 重新加入內邊距
        
        city_icon_layout = BoxLayout(orientation='horizontal', size_hint_x=0.6, spacing=5)
        self.city_selector_layout = BoxLayout(orientation='horizontal', size_hint_x=0.6) 
        # ⚠️ 移除 city_selector_layout 的邊框繪製

        self.city_label = Label(
            text=self.city_name,
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='40sp',
            color=(0, 0, 0, 1),
            size_hint_x=0.85, 
            halign='center', 
            valign='center'
        )
        self.city_label.bind(size=self.city_label.setter('text_size'))
        city_options = ['Kobe', 'Osaka', 'Tokyo', 'Sapporo', 'Sendai', 'Nagoya', 'Fukuoka', 'Naha']
        self.city_spinner = Spinner(
            text='▼',
            values=city_options,
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='25sp', 
            size_hint_x=0.15, 
            background_color=(0, 0, 0, 0), 
            background_normal='', 
            background_down='', 
            color=(0, 0, 0, 1) 
        )
        self.city_spinner.bind(text=self.manual_search_weather_spinner)
        self.city_selector_layout.add_widget(self.city_label)
        self.city_selector_layout.add_widget(self.city_spinner)
        self.weather_icon = Image(source=get_abs_path(DEFAULT_ICON_PATH), size_hint_x=0.4) 
        city_icon_layout.add_widget(self.city_selector_layout) 
        city_icon_layout.add_widget(self.weather_icon)
        date_weather_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=5) 
        now = datetime.now().strftime("%Y年%m月%d日")
        self.date_label = Label(
            text=f"日付\n{now}",
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='20sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.4,
            halign='center',
            valign='center'
        )
        self.date_label.bind(size=self.date_label.setter('text_size')) 
        self.temp_weather_label = Label(
            text='天気 | 気温\n読み込み中...',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='18sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.6,
            halign='center',
            valign='center'
        )
        self.temp_weather_label.bind(size=self.temp_weather_label.setter('text_size'))
        date_weather_layout.add_widget(self.date_label)
        date_weather_layout.add_widget(self.temp_weather_label)
        top_layout.add_widget(city_icon_layout)
        top_layout.add_widget(date_weather_layout)
        
        self.center_layout = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=10, padding=[15, 0, 15, 0]) # 重新加入內邊距
        # ⚠️ 移除 center_layout 的邊框繪製

        left_center_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, padding=[0, 10, 0, 0], spacing=10)
        self.extra_info_label = Label(
            text='湿度: N/A\n風速: N/A\n日の出: N/A\n日の入り: N/A',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='18sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.7, 
            halign='center',
            valign='center'
        )
        self.extra_info_label.bind(size=self.extra_info_label.setter('text_size'))
        self.rain_alert_label = Label(
            text='読み込み中...', 
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='18sp',
            color=(0.3, 0.3, 0.3, 1), 
            size_hint_y=0.3,
            halign='center',
            valign='top'
        )
        self.rain_alert_label.bind(size=self.rain_alert_label.setter('text_size'))
        left_center_layout.add_widget(self.extra_info_label)
        left_center_layout.add_widget(self.rain_alert_label)
        self.image = Image(source=get_abs_path("images/default.png"), size_hint_x=0.6)
        self.center_layout.add_widget(left_center_layout)
        self.center_layout.add_widget(self.image)
        
        bottom_layout = BoxLayout(orientation='vertical', size_hint_y=0.25, padding=15) # 重新加入內邊距
        
        self.label = Label(
            text='神戸の天気を読み込み中...',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='22sp',
            color=(0, 0, 0, 1),
            size_hint_y=1.0, 
            text_size=(Window.width - 40, None),
            halign='center',
            valign='center'
        )
        self.label.bind(size=self.label.setter('text_size'))
        bottom_layout.add_widget(self.label)
        
        main_layout.add_widget(top_layout)
        main_layout.add_widget(self.center_layout) 
        main_layout.add_widget(bottom_layout)
        
        threading.Thread(target=lambda: self._manual_weather_thread(DEFAULT_CITY)).start()
        return main_layout

    # ⚠️ 移除 _update_rect 方法，因為相關的 Line 繪圖已被刪除
    # def _update_rect(self, instance, value):
    #     if instance == self.city_selector_layout:
    #         self.city_rect.rectangle = (instance.x, instance.y, instance.width, instance.height)
    #     elif instance == self.center_layout:
    #         self.center_rect.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def manual_search_weather_spinner(self, instance, city_name):
        city_to_search = city_name.strip()
        all_cities = ['Kobe', 'Osaka', 'Tokyo', 'Sapporo', 'Sendai', 'Nagoya', 'Fukuoka', 'Naha']
        if city_to_search in all_cities: 
            Clock.schedule_once(lambda dt: self._update_ui_loading(f"{city_to_search}の天気を取得中..."), 0)
            threading.Thread(target=lambda: self._manual_weather_thread(city_to_search)).start()
        elif city_to_search == '▼':
            pass

    def _manual_weather_thread(self, city):
        success = self.get_weather_data(city=city)
        if success:
            Clock.schedule_once(lambda dt: self._determine_advice(), 0) 

    def _update_ui_loading(self, message):
        self.label.text = message
        self.city_label.text = '読み込み中...'
        self.temp_weather_label.text = '天気 | 気温\n読み込み中...'
        self.extra_info_label.text = '湿度: N/A\n風速: N/A\n日の出: N/A\n日の入り: N/A'
        self.rain_alert_label.text = '読み込み中...'
        self.rain_alert_label.color = (0.3, 0.3, 0.3, 1)
        self.weather_icon.source = get_abs_path(DEFAULT_ICON_PATH) 
        
        if self.current_bg_image != self.sunny_bg_image:
            self.current_bg_image = self.sunny_bg_image
            Clock.schedule_once(lambda dt: self._update_background_texture(), 0)

    def _update_error_ui(self):
        self.temp_weather_label.text = "天気 | 気温\n読み込み失敗"
        self.label.text = f"{self.city_name}の天気を取得できませんでした。ネットワークまたはAPI設定を確認してください。"
        self.image.source = get_abs_path("images/default.png")
        self.weather_icon.source = get_abs_path(DEFAULT_ICON_PATH) 
        self.extra_info_label.text = '湿度: N/A\n風速: N/A\n日の出: N/A\n日の入り: N/A'
        self.rain_alert_label.text = '読み込みエラー' 
        self.rain_alert_label.color = (1, 0, 0, 1)
        
        if self.current_bg_image != self.sunny_bg_image:
            self.current_bg_image = self.sunny_bg_image
            Clock.schedule_once(lambda dt: self._update_background_texture(), 0)


    def get_weather_data(self, city=None, lat=None, lon=None):
        if city is None:
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "エラー：都市情報がありません。"), 0)
            return False
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ja"
        try:
            response = requests.get(weather_url)
            response.raise_for_status() 
            data = response.json()
            main_data = data.get("main", {})
            weather_data = data.get("weather", [{}])[0]
            self.city_name = data.get("name", self.city_name)
            self.temp = int(round(main_data.get("temp", 0)))
            self.temp_min = int(round(main_data.get("temp_min", 0)))
            self.temp_max = int(round(main_data.get("temp_max", 0)))
            self.weather = weather_data.get("description", "不明な天気")
            self.humidity = main_data.get("humidity", 0) 
            self.wind_speed = data.get("wind", {}).get("speed", 0) 
            self.sunrise = data.get("sys", {}).get("sunrise", 0) 
            self.sunset = data.get("sys", {}).get("sunset", 0) 
            self.weather_icon_code = weather_data.get("icon", "01d") 
            Clock.schedule_once(lambda dt: self._update_weather_ui(), 0)
            return True
        except requests.exceptions.RequestException as e:
            print(f"天気データを取得できませんでした: {e}")
            Clock.schedule_once(lambda dt: self._update_error_ui(), 0)
            return False

    def download_icon(self, icon_code):
        icon_url = WEATHER_ICON_URL.format(icon_code=icon_code)
        self.icon_temp_path = f'weather_icon_{icon_code}.png'
        req = UrlRequest(icon_url, on_success=self.icon_download_success, on_failure=self.icon_download_fail, file_path=self.icon_temp_path, verify=False)

    def icon_download_success(self, req, results):
        def update_source(dt):
            self.weather_icon.source = self.icon_temp_path
            self.weather_icon.reload()
        Clock.schedule_once(update_source, 0)

    def icon_download_fail(self, req, results):
        print(f"アイコンのダウンロードに失敗: {req.url}")
        def update_source_fail(dt):
            self.weather_icon.source = get_abs_path(DEFAULT_ICON_PATH)
            self.weather_icon.reload()
        Clock.schedule_once(update_source_fail, 0)

    def _update_weather_ui(self):
        now = datetime.now().strftime("%Y/%m/%d")
        self.date_label.text = f"日付\n{now}"
        self.city_label.text = self.city_name
        self.city_spinner.text = '▼' 
        self.download_icon(self.weather_icon_code)
        temp_weather_text = f"天気 | 気温\n{self.weather} | {self.temp}°C\n({self.temp_min}°C~{self.temp_max}°C)"
        self.temp_weather_label.text = temp_weather_text
        self.label.text = f"{self.city_name}の天気情報を更新しました。"
        try:
            sunrise_time = datetime.fromtimestamp(self.sunrise).strftime("%H:%M")
        except ValueError:
            sunrise_time = "N/A"
        try:
            sunset_time = datetime.fromtimestamp(self.sunset).strftime("%H:%M")
        except ValueError:
            sunset_time = "N/A"
        extra_info_text = f"湿度: {self.humidity}%\n風速: {self.wind_speed} m/s\n日の出: {sunrise_time}\n日の入り: {sunset_time}"
        self.extra_info_label.text = extra_info_text
        
        rain_keywords = ["雨", "雷", "にわか雨", "小雨", "大雨", "霧雨", "雪"] 
        is_rain_expected = any(keyword in self.weather for keyword in rain_keywords) 
        if is_rain_expected:
            self.rain_alert_label.text = "☂傘を持って行きましょう！"
            self.rain_alert_label.color = (0, 0.4, 0.8, 1)
        else:
            self.rain_alert_label.text = "雨の予報はありません"
            self.rain_alert_label.color = (0.3, 0.3, 0.3, 1)

    def _update_background_texture(self):
        if os.path.exists(self.current_bg_image):
            self.bg_rect.source = self.current_bg_image
            self.bg_rect.texture = None 
        else:
            print(f"無法載入背景圖片: {self.current_bg_image}")
            self.bg_rect.source = "" 
            self.bg_rect.texture = None
            

    def _determine_advice(self):
        if self.temp is None or self.weather is None:
            self.label.text = "天気情報が不足しているため、アドバイスを表示できません。"
            self.image.source = get_abs_path("images/default.png")
            
            if self.current_bg_image != self.sunny_bg_image:
                self.current_bg_image = self.sunny_bg_image
                Clock.schedule_once(lambda dt: self._update_background_texture(), 0)
            return
        
        # 判斷並切換背景圖片 (只剩雨天和晴天)
        rain_keywords = ["雨", "雷", "にわか雨", "小雨", "大雨", "霧雨", "雪"] 
        
        is_rain_expected = any(keyword in self.weather for keyword in rain_keywords)

        new_bg_image = self.sunny_bg_image # 預設為晴天

        if is_rain_expected:
            new_bg_image = self.rainy_bg_image
        else:
            new_bg_image = self.sunny_bg_image

        if new_bg_image != self.current_bg_image:
            self.current_bg_image = new_bg_image
            Clock.schedule_once(lambda dt: self._update_background_texture(), 0)

        suggestion = f"{self.temp}°C・{self.weather}に基づく服装の提案はありません。"
        image_file = get_abs_path("images/default.png") 
        current_temp = self.temp
        current_weather = self.weather
        for rule in self.rules:
            temp_min_rule, temp_max_rule = rule["temp"]
            is_temp_match = temp_min_rule <= current_temp <= temp_max_rule
            if is_temp_match:
                weather_keywords = rule.get("weather_keywords", [])
                if not weather_keywords or any(keyword in current_weather for keyword in weather_keywords):
                    suggestion = rule["advice"]
                    image_file = rule["image"]
                    break
        self.label.text = suggestion
        self.image.source = image_file

if __name__ == '__main__':
    WeatherApp().run()