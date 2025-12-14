import flet as ft
import math


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK


class ScientificButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_100
        self.color = ft.Colors.BLACK


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()
        self.scientific_mode = True
        self.inverse_mode = False
        self.last_result = 0

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        
        # 標準モードのボタン
        self.standard_buttons = ft.Column(
            visible=False,
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="科学", button_clicked=self.toggle_mode),
                    ]
                ),
            ]
        )
        
        # 科学計算モードのボタン
        self.scientific_buttons = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                ft.Row(
                    controls=[
                        ScientificButton(text="x!", button_clicked=self.button_clicked),
                        ScientificButton(text="Inv", button_clicked=self.button_clicked),
                        ScientificButton(text="sin", button_clicked=self.button_clicked),
                        ScientificButton(text="ln", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScientificButton(text="π", button_clicked=self.button_clicked),
                        ScientificButton(text="cos", button_clicked=self.button_clicked),
                        ScientificButton(text="log", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScientificButton(text="e", button_clicked=self.button_clicked),
                        ScientificButton(text="tan", button_clicked=self.button_clicked),
                        ScientificButton(text="√", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScientificButton(text="Ans", button_clicked=self.button_clicked),
                        ScientificButton(text="EXP", button_clicked=self.button_clicked),
                        ScientificButton(text="x^y", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ExtraActionButton(text="標準", button_clicked=self.toggle_mode),
                    ]
                ),
            ]
        )
        
        # Stackを使って同じ位置に重ねて表示
        self.content = ft.Stack(
            controls=[
                self.standard_buttons,
                self.scientific_buttons,
            ]
        )

    def toggle_mode(self, e):
        self.scientific_mode = not self.scientific_mode
        self.standard_buttons.visible = not self.scientific_mode
        self.scientific_buttons.visible = self.scientific_mode
        self.update()

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = self.result.value + data

        elif data in ("+", "-", "*", "/"):
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data == "=":
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.last_result = float(self.result.value) if self.result.value != "Error" else 0
            self.reset()

        elif data == "%":
            self.result.value = float(self.result.value) / 100
            self.reset()

        elif data == "+/-":
            if float(self.result.value) > 0:
                self.result.value = "-" + str(self.result.value)
            elif float(self.result.value) < 0:
                self.result.value = str(self.format_number(abs(float(self.result.value))))

        # 科学計算機能
        elif data == "Inv":
            self.inverse_mode = not self.inverse_mode
            # Invモードの表示を更新する場合はここに追加

        elif data == "sin":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(math.degrees(math.asin(val)))
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.sin(math.radians(val)))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "cos":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(math.degrees(math.acos(val)))
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.cos(math.radians(val)))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "tan":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(math.degrees(math.atan(val)))
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.tan(math.radians(val)))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "ln":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(math.exp(val))
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.log(val))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "log":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(math.pow(10, val))
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.log10(val))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "√":
            try:
                val = float(self.result.value)
                if self.inverse_mode:
                    self.result.value = self.format_number(val * val)
                    self.inverse_mode = False
                else:
                    self.result.value = self.format_number(math.sqrt(val))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "x!":
            try:
                val = int(float(self.result.value))
                self.result.value = self.format_number(math.factorial(val))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "π":
            self.result.value = self.format_number(math.pi)
            self.new_operand = True

        elif data == "e":
            self.result.value = self.format_number(math.e)
            self.new_operand = True

        elif data == "Ans":
            self.result.value = self.format_number(self.last_result)
            self.new_operand = True

        elif data == "EXP":
            try:
                val = float(self.result.value)
                self.result.value = self.format_number(math.exp(val))
                self.new_operand = True
            except:
                self.result.value = "Error"

        elif data == "x^y":
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = "^"
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        self.update()

    def format_number(self, num):
        if num % 1 == 0:
            return int(num)
        else:
            return num

    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return self.format_number(operand1 + operand2)
        elif operator == "-":
            return self.format_number(operand1 - operand2)
        elif operator == "*":
            return self.format_number(operand1 * operand2)
        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)
        elif operator == "^":
            try:
                return self.format_number(math.pow(operand1, operand2))
            except:
                return "Error"

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator"
    calc = CalculatorApp()
    page.add(calc)


ft.app(main)