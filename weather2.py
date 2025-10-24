import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock # 用於異步操作，雖然這裡的 requests 是同步的，但用於啟動時調用是好的習慣

# OpenWeatherMap API 配置
API_KEY = "93aea5ae7f71bd9bcbe24bb57b43ad90"
CITY = "Tokyo"
# units=metric 獲取攝氏度, lang=zh_tw 獲取繁體中文天氣描述
URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=zh_tw"

# 背景顏色
Window.clearcolor = (1, 1, 1, 1)

class WeatherApp(App):
    def build(self):
        # 初始化天氣數據為 None
        self.temp = None
        self.temp_min = None
        self.temp_max = None
        self.weather = None
        self.city_name = CITY

        # 規則表 - **現在只基於當前溫度 (self.temp) 和天氣描述**
        self.rules = [
            # 規則 1: 10 度（含）以下 (寒冷)
            {"temp": (-50, 10), "weather_keywords": ["雨", "雪", "霧"], "advice": "天氣寒冷，並有雨雪，建議穿：羽絨/厚外套、毛衣和防水鞋。", "image": "images/coat_rain.png"},
            {"temp": (-50, 10), "weather_keywords": [], "advice": "天氣寒冷乾燥，建議穿：羽絨/厚外套、毛衣。", "image": "images/coat.png"}, 
            
            # 規則 2: 11 度到 20 度（含） (涼爽)
            {"temp": (11, 20), "weather_keywords": ["雨"], "advice": "天氣涼爽有雨，建議穿：薄外套/風衣並帶傘。", "image": "images/long_sleeve_rain.png"}, 
            {"temp": (11, 20), "weather_keywords": [], "advice": "天氣涼爽，建議穿：薄外套、長袖襯衫。", "image": "images/long_sleeve.png"},
            
            # 規則 3: 21 度到 25 度（含） (舒適/微暖)
            {"temp": (21, 25), "weather_keywords": [], "advice": "天氣舒適微暖，建議穿：長袖/七分袖T恤，可配輕薄外套。", "image": "images/long_sleeve_tshirt.png"}, # 假設有 long_sleeve_tshirt.png

            # 規則 4: 26 度到 40 度 (炎熱)
            {"temp": (26, 40), "weather_keywords": ["雨", "雷"], "advice": "天氣炎熱有雨，建議穿：短袖、短褲，並帶傘。", "image": "images/tshirt_rain.png"}, 
            {"temp": (26, 40), "weather_keywords": [], "advice": "天氣炎熱，建議穿：短袖T恤、短褲或裙子。", "image": "images/tshirt.png"},
        ]

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 城市和溫度顯示 (將顯示所有溫度)
        self.temp_label = Label(
            text=f'{self.city_name} 天氣載入中...',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='28sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.2
        )
        
        # 建議文字顯示
        self.label = Label(
            text='點擊按鈕或載入完成後顯示建議',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='24sp',
            color=(0, 0, 0, 1),
            size_hint_y=0.3 # 讓建議文本佔用更多空間
        )

        # 圖片顯示
        self.image = Image(source="images/default.png", size_hint_y=0.4)

        # 按鈕
        button = Button(
            text='重新整理/顯示服裝建議',
            font_name="C:/Windows/Fonts/msgothic.ttc",
            font_size='20sp',
            background_color=(0.2, 0.6, 1, 1),
            size_hint_y=0.1
        )
        button.bind(on_press=self.get_weather_and_show_advice)

        layout.add_widget(self.temp_label)
        layout.add_widget(self.label)
        layout.add_widget(self.image)
        layout.add_widget(button)

        # 應用程式啟動後自動獲取一次天氣並顯示建議
        Clock.schedule_once(lambda dt: self.get_weather_and_show_advice(), 0.1)

        return layout

    # --- 1. 獲取天氣數據的方法 ---
    def get_weather_data(self):
        """從 OpenWeatherMap API 獲取數據並更新 class 屬性。"""
        try:
            response = requests.get(URL)
            response.raise_for_status() 
            data = response.json()
            
            main_data = data.get("main", {})
            weather_data = data.get("weather", [{}])[0]
            
            # 更新 class 屬性
            self.temp = int(round(main_data.get("temp", 0)))
            self.temp_min = int(round(main_data.get("temp_min", 0)))
            self.temp_max = int(round(main_data.get("temp_max", 0)))
            self.weather = weather_data.get("description", "未知天氣")
            
            # 更新溫度顯示 Label
            temp_text = (
                f"城市: {self.city_name}\n"
                f"天氣: {self.weather}\n"
                f"當前溫度: {self.temp}°C\n"
                f"(今日溫度範圍: {self.temp_min}°C ~ {self.temp_max}°C)"
            )
            self.temp_label.text = temp_text
            
            return True # 成功獲取數據
            
        except requests.exceptions.RequestException as e:
            error_text = f"無法取得天氣數據。\n錯誤: {e}"
            self.temp_label.text = error_text
            self.label.text = "請檢查網絡或 API 設置。"
            self.image.source = "images/default.png"
            print(error_text)
            return False # 失敗

    # --- 2. 處理建議邏輯的方法 ---
    def _determine_advice(self):
        """根據當前溫度和天氣決定服裝建議。"""
        if self.temp is None or self.weather is None:
            self.label.text = "無法給建議，天氣數據不完整。"
            self.image.source = "images/default.png"
            return

        suggestion = f"基於 {self.temp}°C 和 {self.weather}，暫無明確建議。"
        image_file = "images/default.png"
        
        current_temp = self.temp
        current_weather = self.weather
        
        # 遍歷規則表，尋找第一個匹配的規則
        for rule in self.rules:
            temp_min_rule, temp_max_rule = rule["temp"]
            
            # 1. 檢查當前溫度是否在規則範圍內 (包含上下限)
            is_temp_match = temp_min_rule <= current_temp <= temp_max_rule
            
            if is_temp_match:
                weather_keywords = rule.get("weather_keywords", [])
                
                # 2. 檢查天氣關鍵字是否匹配
                # any() 檢查 current_weather 中是否包含 weather_keywords 中的任一詞彙
                # (not weather_keywords) 處理沒有天氣限制的情況 (即 [] )
                if not weather_keywords or any(keyword in current_weather for keyword in weather_keywords):
                    suggestion = rule["advice"]
                    image_file = rule["image"]
                    break # 找到匹配規則後立即停止

        # 更新 Kivy 界面
        self.label.text = suggestion
        self.image.source = image_file
        
    # --- 3. 組合方法：獲取數據並顯示建議 ---
    def get_weather_and_show_advice(self, instance=None):
        """處理按鈕點擊或啟動時的事件。"""
        if self.get_weather_data(): # 如果成功獲取數據
            self._determine_advice() # 則決定並顯示建議

if __name__ == '__main__':
    # 執行前請確保 'images/' 目錄中存在對應的圖片文件，例如:
    # default.png, coat_rain.png, coat.png, long_sleeve.png, tshirt.png 等。
    WeatherApp().run()