from PyQt5.QtWidgets import QApplication

class SpeechLocator:
    @staticmethod
    def calculate_position(pet_widget, speech_width, speech_height) -> tuple:
        pet_rect = pet_widget.geometry()
        screen = QApplication.primaryScreen()
        if not screen:
            return pet_rect.right(), pet_rect.top()
        screen_rect = screen.availableGeometry()

        ideal_x = pet_rect.right()
        ideal_y = pet_rect.top() - speech_height

        # 边缘碰撞边界处理
        if ideal_y < screen_rect.top():
            ideal_y = pet_rect.top()
        if ideal_x + speech_width > screen_rect.right():
            ideal_x = pet_rect.left() - speech_width
        if ideal_x < screen_rect.left():
            ideal_x = screen_rect.left() + 5

        return ideal_x, ideal_y