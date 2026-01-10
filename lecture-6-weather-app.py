import flet as ft
import requests
import sqlite3
from datetime import datetime, timedelta
import os

# データベースファイルのパス
DB_PATH = "weather.db"


def init_database():
    """データベースの初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # エリア情報テーブル（オプション機能）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            area_code TEXT PRIMARY KEY,
            area_name TEXT NOT NULL,
            parent_code TEXT,
            area_type TEXT NOT NULL
        )
    """)
    
    # 天気予報テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT NOT NULL,
            area_name TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            weather TEXT,
            temp_min TEXT,
            temp_max TEXT,
            fetched_at TEXT NOT NULL,
            UNIQUE(area_code, forecast_date, fetched_at)
        )
    """)
    
    # インデックス作成
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecasts_area_date 
        ON forecasts(area_code, forecast_date)
    """)
    
    conn.commit()
    conn.close()
    print("データベース初期化完了")


def save_areas_to_db(centers, offices):
    """エリア情報をDBに保存"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # センター（地方）を保存
    for code, info in centers.items():
        cursor.execute("""
            INSERT OR REPLACE INTO areas (area_code, area_name, parent_code, area_type)
            VALUES (?, ?, ?, ?)
        """, (code, info.get("name", ""), None, "center"))
    
    # オフィス（都道府県）を保存
    for code, info in offices.items():
        cursor.execute("""
            INSERT OR REPLACE INTO areas (area_code, area_name, parent_code, area_type)
            VALUES (?, ?, ?, ?)
        """, (code, info.get("name", ""), info.get("parent", ""), "office"))
    
    conn.commit()
    conn.close()
    print(f"エリア情報を保存: センター{len(centers)}件, オフィス{len(offices)}件")


def save_forecast_to_db(area_code, area_name, weather_data, fetched_at):
    """天気予報データをDBに保存"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for date_str, data in weather_data.items():
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO forecasts 
                (area_code, area_name, forecast_date, weather, temp_min, temp_max, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                area_code,
                area_name,
                date_str,
                data.get("weather"),
                data.get("temp_min"),
                data.get("temp_max"),
                fetched_at
            ))
        except sqlite3.Error as e:
            print(f"DB保存エラー: {e}")
    
    conn.commit()
    conn.close()
    print(f"{area_name}の予報を{len(weather_data)}件保存")


def get_forecasts_from_db(area_code, target_date=None):
    """DBから天気予報を取得"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if target_date:
        # 特定の日付の予報を取得（過去の予報閲覧用）
        cursor.execute("""
            SELECT forecast_date, weather, temp_min, temp_max, fetched_at
            FROM forecasts
            WHERE area_code = ? AND DATE(fetched_at) = ?
            ORDER BY forecast_date
        """, (area_code, target_date))
    else:
        # 最新の予報を取得
        cursor.execute("""
            SELECT forecast_date, weather, temp_min, temp_max, fetched_at
            FROM forecasts
            WHERE area_code = ? AND fetched_at = (
                SELECT MAX(fetched_at) FROM forecasts WHERE area_code = ?
            )
            ORDER BY forecast_date
        """, (area_code, area_code))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


def get_available_dates(area_code):
    """過去に取得した予報の日付リストを取得"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT DATE(fetched_at) as fetch_date
        FROM forecasts
        WHERE area_code = ?
        ORDER BY fetch_date DESC
        LIMIT 30
    """, (area_code,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


def main(page: ft.Page):
    page.title = "天気予報アプリ v2"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # データベース初期化
    init_database()

    # 気象庁APIから地域データを取得
    area_url = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        area_data = requests.get(area_url).json()
        centers = area_data.get("centers", {})
        offices = area_data.get("offices", {})
        # エリア情報をDBに保存（オプション機能）
        save_areas_to_db(centers, offices)
    except Exception as e:
        page.add(ft.Text(f"地域データの取得に失敗しました: {e}"))
        return

    # 現在選択中の地域を保持
    current_area = {"code": None, "name": None}

    # 天気予報表示エリア
    weather_content = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    
    # 日付選択ドロップダウン（天気表示エリア内に配置）
    date_dropdown = ft.Dropdown(
        label="取得日",
        hint_text="日付を選択",
        width=180,
        text_size=14,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=5),
        visible=False,
        border_color=ft.Colors.INDIGO,
        focused_border_color=ft.Colors.INDIGO_700,
        bgcolor=ft.Colors.WHITE,
        on_change=lambda e: on_date_selected(e),
    )
    
    # 日付選択コンテナ
    date_selector_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.HISTORY, color=ft.Colors.INDIGO, size=20),
                ft.Text("過去の予報:", size=14, color=ft.Colors.GREY_700),
                date_dropdown,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        visible=False,
        padding=ft.padding.only(left=20, top=15, bottom=5),
    )

    def get_weather_icon(weather_text):
        """天気テキストからアイコンを取得"""
        # ひらがな・漢字の両方に対応
        is_rain = "雨" in weather_text
        is_snow = "雪" in weather_text
        is_cloudy = "曇" in weather_text or "くもり" in weather_text
        is_sunny = "晴" in weather_text
        
        if is_snow:
            return "❄️"
        elif is_rain and is_sunny:
            return "🌤️🌧️"
        elif is_rain and is_cloudy:
            return "☁️🌧️"
        elif is_rain:
            return "🌧️"
        elif is_sunny and is_cloudy:
            return "⛅"
        elif is_cloudy:
            return "☁️"
        elif is_sunny:
            return "☀️"
        else:
            return "☁️"  # デフォルトは曇りアイコン

    def create_weather_card(date, weather, temp_min, temp_max):
        """天気予報カードを作成"""
        icon = get_weather_icon(weather) if weather else "❓"
        
        weather_short = ""
        if weather:
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

    def parse_forecast_data(forecast_data):
        """APIレスポンスから天気データを解析"""
        weather_dict = {}
        
        if not forecast_data or len(forecast_data) == 0:
            return weather_dict
            
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
                    for i, time_def in enumerate(time_defines):
                        if i >= len(temps) or not temps[i]:
                            continue
                        date_str = time_def[:10]
                        if date_str not in weather_dict:
                            weather_dict[date_str] = {"weather": None, "temp_min": None, "temp_max": None}
                        
                        try:
                            temp_val = int(temps[i])
                            current_min = weather_dict[date_str]["temp_min"]
                            current_max = weather_dict[date_str]["temp_max"]
                            
                            if current_min is None or temp_val < int(current_min):
                                weather_dict[date_str]["temp_min"] = temps[i]
                            if current_max is None or temp_val > int(current_max):
                                weather_dict[date_str]["temp_max"] = temps[i]
                        except (ValueError, TypeError):
                            pass
                
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
        
        return weather_dict

    def display_weather_from_db(area_name, db_forecasts, fetch_date=None):
        """DBから取得したデータを画面に表示"""
        weather_cards = []
        
        for forecast in db_forecasts[:7]:
            date_str, weather, temp_min, temp_max, fetched_at = forecast
            
            if weather:
                weather_cards.append(
                    create_weather_card(date_str, weather, temp_min, temp_max)
                )
        
        # タイトルテキスト
        title_text = f"{area_name}の天気予報"
        if fetch_date:
            title_text += f"（{fetch_date} 取得分）"
        
        # DBインジケーター
        db_indicator = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.STORAGE, size=16, color=ft.Colors.GREEN_700),
                    ft.Text("SQLite DBから表示", size=12, color=ft.Colors.GREEN_700, weight=ft.FontWeight.W_500),
                ],
                spacing=5,
            ),
            padding=ft.padding.only(bottom=10),
        )
        
        weather_content.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                title_text,
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=ft.padding.only(bottom=5),
                        ),
                        db_indicator,
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

    def fetch_weather(area_code, area_name):
        """地域の天気予報をAPIから取得→DBに保存→DBから取得して表示"""
        current_area["code"] = area_code
        current_area["name"] = area_name
        
        forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
        fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # 1. APIからJSONを取得
            response = requests.get(forecast_url, timeout=10)
            
            # ステータスコードチェック
            if response.status_code != 200:
                raise Exception(f"APIエラー: ステータスコード {response.status_code}")
            
            # レスポンスが空かチェック
            if not response.text or response.text.strip() == "":
                raise Exception("この地域の天気予報データは提供されていません")
            
            forecast_data = response.json()
            
            # データが空かチェック
            if not forecast_data or len(forecast_data) == 0:
                raise Exception("天気予報データが空です")
            
            weather_dict = parse_forecast_data(forecast_data)
            
            # 天気データがあるかチェック
            if not weather_dict:
                raise Exception("天気データを解析できませんでした")
            
            # 2. DBに保存
            save_forecast_to_db(area_code, area_name, weather_dict, fetched_at)
            
            # 3. DBから取得して表示（JSONからDBに移行）
            db_forecasts = get_forecasts_from_db(area_code)
            display_weather_from_db(area_name, db_forecasts)
            
            # 日付セレクタを更新・表示
            update_date_dropdown(area_code)
            
        except requests.exceptions.JSONDecodeError:
            # JSONパースエラー（データが提供されていない地域）
            print(f"JSONパースエラー: {area_name}")
            show_error_message(area_name, "この地域の天気予報データは現在提供されていません")
            
        except requests.exceptions.Timeout:
            # タイムアウト
            print(f"タイムアウト: {area_name}")
            fallback_to_db(area_code, area_name, "接続がタイムアウトしました")
            
        except Exception as e:
            # その他のエラー
            print(f"API取得エラー: {e}")
            fallback_to_db(area_code, area_name, str(e))
    
    def fallback_to_db(area_code, area_name, error_msg):
        """エラー時にDBからフォールバック"""
        db_forecasts = get_forecasts_from_db(area_code)
        if db_forecasts:
            display_weather_from_db(area_name, db_forecasts)
            update_date_dropdown(area_code)
        else:
            show_error_message(area_name, error_msg)
    
    def show_error_message(area_name, error_msg):
        """エラーメッセージを表示"""
        weather_content.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=ft.Colors.ORANGE_400),
                        ft.Text(f"{area_name}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(error_msg, size=14, color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text("他の地域を選択してください", size=12, color=ft.Colors.GREY_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                alignment=ft.alignment.center,
            )
        ]
        date_selector_container.visible = False
        page.update()

    def update_date_dropdown(area_code):
        """日付選択ドロップダウンを更新"""
        available_dates = get_available_dates(area_code)
        
        if available_dates:
            date_dropdown.options = [
                ft.dropdown.Option(key=date, text=date) for date in available_dates
            ]
            date_dropdown.value = available_dates[0] if available_dates else None
            date_dropdown.visible = True
            date_selector_container.visible = True
        else:
            date_dropdown.visible = False
            date_selector_container.visible = False
        
        page.update()

    def on_date_selected(e):
        """過去の日付が選択された時の処理"""
        if not current_area["code"] or not e.control.value:
            return
        
        selected_date = e.control.value
        db_forecasts = get_forecasts_from_db(current_area["code"], selected_date)
        
        if db_forecasts:
            display_weather_from_db(current_area["name"], db_forecasts, fetch_date=selected_date)

    def on_area_click(e, area_code, area_name):
        """地域が選択された時の処理"""
        fetch_weather(area_code, area_name)

    # APIで天気予報が提供されていない地域コード（404エラーになる）
    EXCLUDED_AREA_CODES = {
        "014030",  # 十勝地方
        "460040",  # 奄美地方
    }

    def create_region_panel():
        """地域選択パネルを作成"""
        expansion_tiles = []
        
        expansion_tiles.append(
            ft.Container(
                content=ft.Text("地域を選択", size=16, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(left=15, top=10, bottom=10),
            )
        )
        
        for center_code, center_info in centers.items():
            center_name = center_info.get("name", "")
            children_codes = center_info.get("children", [])
            
            child_tiles = []
            for child_code in children_codes:
                # APIで対応していない地域はスキップ
                if child_code in EXCLUDED_AREA_CODES:
                    continue
                    
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

    # AppBar（シンプルに）
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.WB_SUNNY),
        leading_width=40,
        title=ft.Text("天気予報 v2 (SQLite対応)"),
        center_title=False,
        bgcolor=ft.Colors.INDIGO,
        color=ft.Colors.WHITE,
        actions=[
            ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color=ft.Colors.WHITE, 
                         tooltip="天気情報はSQLiteに保存されます"),
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
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN),
                                        ft.Text("天気情報はSQLiteデータベースに保存されます", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=5,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN),
                                        ft.Text("表示データはDBから取得されます（JSON→DB移行）", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=5,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN),
                                        ft.Text("過去の予報データも閲覧可能です", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=20,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
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
                content=ft.Column(
                    controls=[
                        date_selector_container,  # 日付選択は天気表示エリアの上部に配置
                        weather_content,
                    ],
                    spacing=0,
                    expand=True,
                ),
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