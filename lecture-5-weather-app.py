import flet as ft
import requests


def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # 気象庁APIから地域データを取得
    area_url = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        area_data = requests.get(area_url).json()
    except Exception as e:
        page.add(ft.Text(f"地域データの取得に失敗しました: {e}"))
        return

    centers = area_data.get("centers", {})
    offices = area_data.get("offices", {})

    # 天気予報表示エリア
    weather_content = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    # 天気アイコンのマッピング（気象庁のtelop codeに対応）
    def get_weather_icon(weather_text):
        if "雨" in weather_text and "晴" in weather_text:
            return "☀️🌧️"
        elif "雨" in weather_text and "曇" in weather_text:
            return "☁️🌧️"
        elif "雪" in weather_text:
            return "❄️"
        elif "雨" in weather_text:
            return "🌧️"
        elif "曇" in weather_text and "晴" in weather_text:
            return "⛅"
        elif "晴" in weather_text and "曇" in weather_text:
            return "🌤️"
        elif "曇" in weather_text:
            return "☁️"
        elif "晴" in weather_text:
            return "☀️"
        else:
            return "🌈"

    def create_weather_card(date, weather, temp_min, temp_max):
        """天気予報カードを作成"""
        icon = get_weather_icon(weather)
        
        # 天気テキストを短縮（改行を削除し、長い場合は省略）
        weather_short = weather.replace("\n", " ").replace("　", " ")
        if len(weather_short) > 20:
            weather_short = weather_short[:18] + "..."
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(date, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(icon, size=40),
                    ft.Container(
                        content=ft.Text(
                            weather_short, 
                            size=11, 
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=120,
                        height=40,
                        alignment=ft.alignment.center,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{temp_min}°C" if temp_min else "-",
                                color=ft.Colors.BLUE,
                                size=12,
                            ),
                            ft.Text("/", size=12),
                            ft.Text(
                                f"{temp_max}°C" if temp_max else "-",
                                color=ft.Colors.RED,
                                size=12,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            width=150,
            height=180,
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            ),
        )

    def fetch_weather(area_code, area_name):
        """地域の天気予報を取得して表示"""
        forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
        
        try:
            forecast_data = requests.get(forecast_url).json()
        except Exception as e:
            weather_content.controls = [
                ft.Container(
                    content=ft.Text(f"天気データの取得に失敗しました: {e}"),
                    padding=20,
                )
            ]
            page.update()
            return

        weather_dict = {}  # 日付をキーにしてデータを集約
        
        # 天気予報データを解析
        if forecast_data and len(forecast_data) > 0:
            for forecast_item in forecast_data:
                time_series = forecast_item.get("timeSeries", [])
                
                for ts in time_series:
                    time_defines = ts.get("timeDefines", [])
                    areas = ts.get("areas", [])
                    
                    if not areas:
                        continue
                    
                    area = areas[0]
                    
                    # 天気情報の取得
                    weathers = area.get("weathers", [])
                    if weathers:
                        for i, time_def in enumerate(time_defines):
                            date_str = time_def[:10]
                            if date_str not in weather_dict:
                                weather_dict[date_str] = {"weather": None, "temp_min": None, "temp_max": None}
                            if i < len(weathers):
                                weather_dict[date_str]["weather"] = weathers[i]
                    
                    # 気温情報の取得（temps配列 - 短期予報用）
                    temps = area.get("temps", [])
                    if temps and len(time_defines) > 0:
                        # 短期予報のtempsは時刻ごとの気温
                        # timeDefinesと対応させて、日付ごとに最低・最高を判定
                        for i, time_def in enumerate(time_defines):
                            if i >= len(temps) or not temps[i]:
                                continue
                            date_str = time_def[:10]
                            if date_str not in weather_dict:
                                weather_dict[date_str] = {"weather": None, "temp_min": None, "temp_max": None}
                            
                            temp_val = int(temps[i]) if temps[i] else None
                            if temp_val is not None:
                                current_min = weather_dict[date_str]["temp_min"]
                                current_max = weather_dict[date_str]["temp_max"]
                                
                                # 最低気温の更新
                                if current_min is None or temp_val < int(current_min):
                                    weather_dict[date_str]["temp_min"] = temps[i]
                                # 最高気温の更新
                                if current_max is None or temp_val > int(current_max):
                                    weather_dict[date_str]["temp_max"] = temps[i]
                    
                    # tempsMin/tempsMax（週間予報用）
                    temps_min = area.get("tempsMin", [])
                    temps_max = area.get("tempsMax", [])
                    
                    if temps_min or temps_max:
                        for i, time_def in enumerate(time_defines):
                            date_str = time_def[:10]
                            if date_str not in weather_dict:
                                weather_dict[date_str] = {"weather": None, "temp_min": None, "temp_max": None}
                            if temps_min and i < len(temps_min) and temps_min[i]:
                                weather_dict[date_str]["temp_min"] = temps_min[i]
                            if temps_max and i < len(temps_max) and temps_max[i]:
                                weather_dict[date_str]["temp_max"] = temps_max[i]

        # カードを作成
        weather_cards = []
        for date_str in sorted(weather_dict.keys())[:7]:
            data = weather_dict[date_str]
            if data["weather"]:
                weather_cards.append(
                    create_weather_card(
                        date_str,
                        data["weather"],
                        data["temp_min"],
                        data["temp_max"]
                    )
                )

        weather_content.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                f"{area_name}の天気予報",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=ft.padding.only(bottom=20),
                        ),
                        ft.Row(
                            controls=weather_cards,
                            wrap=True,
                            spacing=15,
                            run_spacing=15,
                        ),
                    ],
                ),
                padding=20,
            )
        ]
        page.update()

    def on_area_click(e, area_code, area_name):
        """地域が選択された時の処理"""
        fetch_weather(area_code, area_name)

    # 地域選択パネルを作成
    def create_region_panel():
        expansion_tiles = []
        
        # 「地域を選択」タイトル
        expansion_tiles.append(
            ft.Container(
                content=ft.Text("地域を選択", size=16, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=15, top=10, bottom=10),
            )
        )
        
        # centersごとにExpansionTileを作成
        for center_code, center_info in centers.items():
            center_name = center_info.get("name", "")
            children_codes = center_info.get("children", [])
            
            # 子要素（都道府県）のListTileを作成
            child_tiles = []
            for child_code in children_codes:
                if child_code in offices:
                    office_info = offices[child_code]
                    office_name = office_info.get("name", "")
                    
                    child_tiles.append(
                        ft.ListTile(
                            title=ft.Text(office_name, size=14),
                            subtitle=ft.Text(child_code, size=10, color=ft.Colors.GREY),
                            on_click=lambda e, code=child_code, name=office_name: on_area_click(e, code, name),
                            dense=True,
                        )
                    )
            
            # ExpansionTileを作成
            expansion_tiles.append(
                ft.ExpansionTile(
                    title=ft.Text(center_name, size=14),
                    subtitle=ft.Text(center_code, size=10, color=ft.Colors.GREY),
                    controls=child_tiles,
                    initially_expanded=False,
                    collapsed_text_color=ft.Colors.BLACK,
                    text_color=ft.Colors.BLUE,
                )
            )
        
        return ft.Container(
            content=ft.Column(
                controls=expansion_tiles,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
            ),
            width=280,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

    # AppBar
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.WB_SUNNY),
        leading_width=40,
        title=ft.Text("天気予報"),
        center_title=False,
        bgcolor=ft.Colors.INDIGO,
        color=ft.Colors.WHITE,
        actions=[
            ft.IconButton(ft.Icons.MORE_VERT, icon_color=ft.Colors.WHITE),
        ],
    )

    # 初期表示メッセージ
    weather_content.controls = [
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CLOUD, size=100, color=ft.Colors.GREY_400),
                    ft.Text(
                        "左側のリストから地域を選択してください",
                        size=16,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
    ]

    # メインレイアウト
    main_content = ft.Row(
        controls=[
            create_region_panel(),
            ft.Container(
                content=weather_content,
                expand=True,
                bgcolor=ft.Colors.GREY_200,
            ),
        ],
        expand=True,
        spacing=0,
    )

    page.add(app_bar, main_content)


if __name__ == "__main__":
    ft.app(target=main)