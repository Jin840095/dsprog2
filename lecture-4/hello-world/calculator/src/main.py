import flet as ft

class CalcButton(ft.ElevatedButton):
        def __init__(self, text, expand=1):
            super().__init__()
            self.text = text
            self.expand = expand

class DigitButton(CalcButton):
        def __init__(self, text, expand=1):
            CalcButton.__init__(self, text, expand)
            self.bgcolor = ft.Colors.WHITE24
            self.color = ft.Colors.WHITE

class ActionButton(CalcButton):
        def __init__(self, text):
            CalcButton.__init__(self, text)
            self.bgcolor = ft.Colors.ORANGE
            self.color = ft.Colors.WHITE

class ExtraActionButton(CalcButton):
        def __init__(self, text):
            CalcButton.__init__(self, text)
            self.bgcolor = ft.Colors.BLUE_GREY_100
            self.color = ft.Colors.BLACK

# カウンター表示用のテキスト
def main(page: ft.Page):
    counter = ft.Text("0", size=50, data=0)

    # +ボタンクリック時にカウンターを増加させる関数
    def increment_click(e):
        counter.data += 1
        counter.value = str(counter.data)
        counter.update()
    
    # -ボタンクリック時にカウンターを減少させる関数
    def decrement_click(e):
        counter.data -= 1
        counter.value = str(counter.data)
        counter.update()

    #カウンターを増やすボタン
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, on_click=increment_click
    )
    page.add(
        ft.SafeArea(
            ft.Container(
                counter,
                alignment=ft.alignment.center,
            ),
            expand=True,
        ),
        ft.FloatingActionButton(icon=ft.Icons.REMOVE, on_click=decrement_click)
    )


ft.app(main)
