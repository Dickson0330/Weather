import requests
# UrlRequest を追加
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

# OpenWeatherMap API 設定
API_KEY = "93aea5ae7f71bd9bcbe24bb57b43ad90"
DEFAULT_CITY = "Kobe" # デフォルト都市は神戸

# OpenWeatherMap アイコン URL
WEATHER_ICON_URL = "https://openweathermap.org/img/wn/{icon_code}@2x.png" 

# ローカルのデフォルトアイコンパス（images/default.png が存在することを確認）
DEFAULT_ICON_PATH = "images/default.png" 

Window.clearcolor = (1, 1, 1, 1)

class WeatherApp(App):
    def build(self):
        # 位置 / 天気データの初期化
        self.city_name = "位置を読み込み中" 
        self.temp = None
        self.weather = None
        self.weather_icon_code = "01d" # デフォルトアイコンコード（晴れ・昼）
        self.icon_temp_path = DEFAULT_ICON_PATH # 一時保存用の画像パス
        
        # --- 服装アドバイスルール ---
        self.rules = [
            {"temp": (-20, 10), "weather_keywords": ["雨", "雪", "霧"], "advice": "寒くて雨や雪です。ダウンコートや厚手の上着、防水靴をおすすめします。", "image": "images/coat_rain.png"},
            {"temp": (-20, 10), "weather_keywords": [], "advice": "寒くて乾燥しています。ダウンや厚手のコートを着ましょう。", "image": "images/coat.png"}, 
            {"temp": (11, 20), "weather_keywords": ["雨"], "advice": "涼しくて雨が降っています。薄手の上着やトレンチコートを着て傘を持ちましょう。", "image": "images/long_sleeve_rain.png"}, 
            {"temp": (11, 20), "weather_keywords": [], "advice": "涼しい天気です。薄手の上着や長袖のシャツをおすすめします。", "image": "images/long_sleeve.png"},
            {"temp": (21, 25), "weather_keywords": [], "advice": "快適で少し暖かいです。長袖または七分袖のTシャツに軽い上着を合わせましょう。", "image": "images/long_sleeve_tshirt_rain.png"}, 
            {"temp": (21, 25), "weather_keywords": [], "advice": "快適で少し暖かいです。長袖または七分袖のTシャツに軽い上着を合わせましょう。", "image": "images/long_sleeve_tshirt.png"}, 
            {"temp": (26, 40), "weather_keywords": ["雨", "雷"], "advice": "暑くて雨です。Tシャツや短パンを着て傘を持ちましょう。", "image": "images/tshirt_rain.png"}, 
            {"temp": (26, 40), "weather_keywords": [], "advice": "暑い天気です。Tシャツや短パン、スカートなどを着ましょう。", "image": "images/tshirt.png"},
        ]
        # -------------------

        # --- レイアウト初期化 ---
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        top_layout = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=10)
        
        # 1. 左側：都市名とアイコン（水平配置）
        city_icon_layout = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=5)

        self.city_label = Label(
            text=self.city_name,
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='40sp',
            color=(0, 0, 0, 1),
            size_hint_x=0.75, 
            halign='center',
            valign='center'
        )
        self.city_label.bind(size=self._update_rect, pos=self._update_rect)
        # 都市ラベルの枠線を描画
        with self.city_label.canvas.before:
            kivy.graphics.Color(0, 0, 0, 1)
            self.city_rect = kivy.graphics.Line(width=1)
            
        # 天気アイコン
        self.weather_icon = Image(
            source=DEFAULT_ICON_PATH, # 初期はローカルのデフォルト画像
            size_hint_x=0.25 
        )
        
        city_icon_layout.add_widget(self.city_label)
        city_icon_layout.add_widget(self.weather_icon)

        # 2. 右側：日付と天気・温度
        date_weather_layout = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=5)
        now = datetime.now().strftime("%Y年%m月%d日")
        
        # 日付ラベル
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

        # 天気・温度ラベル
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

        # 中央：服装アドバイス画像（枠付き）
        self.image = Image(source="images/default.png", size_hint_y=0.55)
        self.image.bind(size=self._update_rect, pos=self._update_rect)
        with self.image.canvas.before:
            kivy.graphics.Color(0, 0, 0, 1)
            self.image_rect = kivy.graphics.Line(width=1)

        # 下部：スピナーとアドバイス表示
        bottom_layout = BoxLayout(orientation='vertical', size_hint_y=0.2)

        # 都市選択スピナー
        spinner_layout = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=5) 
        city_options = ['Kobe', 'Osaka', 'Tokyo'] 
        
        self.city_spinner = Spinner(
            text='Kobe',
            values=city_options, 
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='18sp',
            size_hint_x=1.0 
        )
        self.city_spinner.bind(text=self.manual_search_weather_spinner)
        spinner_layout.add_widget(self.city_spinner)
        
        self.label = Label(
            text='神戸の天気を読み込み中...',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='22sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.5, 
            text_size=(Window.width - 40, None),
            halign='center'
        )
        self.label.bind(size=self.label.setter('text_size'))
        
        # 下部の組み合わせ
        bottom_layout.add_widget(spinner_layout) 
        bottom_layout.add_widget(self.label)     

        main_layout.add_widget(top_layout)
        main_layout.add_widget(self.image)
        main_layout.add_widget(bottom_layout)

        # 起動時に神戸の天気を取得
        threading.Thread(target=lambda: self._manual_weather_thread(DEFAULT_CITY)).start()
        
        return main_layout
    
    def _update_rect(self, instance, value):
        if instance == self.city_label:
            self.city_rect.rectangle = (instance.x, instance.y, instance.width, instance.height)
        elif instance == self.image:
            self.image_rect.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def manual_search_weather_spinner(self, instance, city_name):
        """スピナーで選択された都市の天気を取得"""
        city_to_search = city_name.strip()
        if city_to_search in ('Kobe', 'Osaka', 'Tokyo'):
            Clock.schedule_once(lambda dt: self._update_ui_loading(f"{city_to_search} の天気を取得中..."), 0)
            threading.Thread(
                target=lambda: self._manual_weather_thread(city_to_search)
            ).start()

    def _manual_weather_thread(self, city):
        """スレッド内で天気情報を取得"""
        success = self.get_weather_data(city=city)
        if success:
            Clock.schedule_once(lambda dt: self._determine_advice(), 0)

    def _update_ui_loading(self, message):
        self.label.text = message
        self.city_label.text = '読み込み中...'
        self.temp_weather_label.text = '天気 | 気温\n読み込み中...'
        self.weather_icon.source = DEFAULT_ICON_PATH 
        
    def _update_error_ui(self):
        """取得失敗時の表示"""
        self.temp_weather_label.text = "天気 | 気温\n取得失敗"
        self.label.text = f"{self.city_name} の天気を取得できません。ネットワークまたはAPI設定を確認してください。"
        self.image.source = "images/default.png"
        self.weather_icon.source = DEFAULT_ICON_PATH 

    def get_weather_data(self, city=None, lat=None, lon=None):
        """OpenWeatherMap API からデータ取得"""
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
            self.weather = weather_data.get("description", "不明")
            self.weather_icon_code = weather_data.get("icon", "01d") 
            
            Clock.schedule_once(lambda dt: self._update_weather_ui(), 0)
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"天気データの取得に失敗しました: {e}")
            Clock.schedule_once(lambda dt: self._update_error_ui(), 0)
            return False

    def download_icon(self, icon_code):
        """天気アイコンのダウンロード"""
        icon_url = WEATHER_ICON_URL.format(icon_code=icon_code)
        self.icon_temp_path = f'weather_icon_{icon_code}.png'
        UrlRequest(
            icon_url, 
            on_success=self.icon_download_success, 
            on_failure=self.icon_download_fail, 
            file_path=self.icon_temp_path,
            verify=False 
        )

    def icon_download_success(self, req, results):
        Clock.schedule_once(lambda dt: (setattr(self.weather_icon, 'source', self.icon_temp_path), self.weather_icon.reload()), 0)

    def icon_download_fail(self, req, results):
        print(f"アイコンのダウンロード失敗: {req.url}")
        Clock.schedule_once(lambda dt: (setattr(self.weather_icon, 'source', DEFAULT_ICON_PATH), self.weather_icon.reload()), 0)

    def _update_weather_ui(self):
        """取得した天気データをUIに反映"""
        now = datetime.now().strftime("%Y/%m/%d")
        self.date_label.text = f"日付\n{now}"
        self.city_label.text = self.city_name
        self.download_icon(self.weather_icon_code)
        self.temp_weather_label.text = f"天気 | 気温\n{self.weather} | {self.temp}°C\n({self.temp_min}°C~{self.temp_max}°C)"
        self.label.text = f"{self.city_name} の天気データを更新しました。"

    def _determine_advice(self):
        """服装アドバイスの決定"""
        if self.temp is None or self.weather is None:
            self.label.text = "天気データが不完全のため、アドバイスできません。"
            self.image.source = "images/default.png"
            return
        
        suggestion = f"{self.temp}°C と {self.weather} に基づくアドバイスはありません。"
        image_file = "images/default.png"
        current_temp = self.temp
        current_weather = self.weather
        
        for rule in self.rules:
            temp_min_rule, temp_max_rule = rule["temp"]
            if temp_min_rule <= current_temp <= temp_max_rule:
                weather_keywords = rule.get("weather_keywords", [])
                if not weather_keywords or any(keyword in current_weather for keyword in weather_keywords):
                    suggestion = rule["advice"]
                    image_file = rule["image"]
                    break

        self.label.text = suggestion
        self.image.source = image_file

if __name__ == '__main__':
    WeatherApp().run()
