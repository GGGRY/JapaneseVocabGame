import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QTreeWidget, 
                            QTreeWidgetItem, QMessageBox, QGroupBox, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QIcon
import pandas as pd
import random
from gtts import gTTS
from playsound import playsound
import os

class SoundThread(QThread):
    """Thread for playing sounds to avoid UI freezing"""
    def __init__(self, word, cache_dir):
        super().__init__()
        self.word = word
        self.cache_dir = cache_dir

    def run(self):
        file_path = os.path.join(self.cache_dir, f"{self.word}.mp3")
        
        if not os.path.exists(file_path):
            try:
                tts = gTTS(text=self.word, lang='ja')
                tts.save(file_path)
            except Exception as e:
                print(f"生成发音失败: {e}")
                QMessageBox.warning(None, "发音错误", 
                                  f"无法生成发音: {e}\n请检查网络连接")
                return
                
        try:
            playsound(file_path)
        except Exception as e:
            print(f"播放发音失败: {e}")

class JapaneseVocabGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日语单词记忆游戏")
        # 设置窗口标志启用自定义标题栏（保留原有窗口标志）
        flags = self.windowFlags()
        self.setWindowFlags(flags | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self.resize(1200,800)
        
        # Set window icon
        if os.path.exists("Icon.png"):
            self.setWindowIcon(QIcon("Icon.png"))
        else:
            print("Icon.png not found in current directory")
        
        # 初始化语音缓存目录
        self.cache_dir = "tts_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # 初始化空单词数据
        self.word_dict = {}
        
        # 游戏状态
        self.total_questions = 20  # 默认题目数量
        self.current_question = 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.incorrect_words = []
        
        # 创建界面
        self.create_widgets()
        
    def load_vocabulary(self):
        """从选择的文件加载单词数据"""
        filename = self.file_combo.currentText()
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename, header=None)
            else:  # Excel文件
                df = pd.read_excel(filename, header=0)
                
            self.word_dict = {}
            for _, row in df.iterrows():
                japanese = row.iloc[0]
                kana = row.iloc[1]
                meaning = row.iloc[3]
                self.word_dict[japanese] = [kana, meaning]
                
            # 更新单词列表显示
            self.word_tree.clear()
            for word, (kana, meaning) in self.word_dict.items():
                item = QTreeWidgetItem([word, kana, meaning])
                self.word_tree.addTopLevelItem(item)
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载单词文件: {e}")
            if not hasattr(self, 'word_dict'):
                self.word_dict = {}  # 保持为空
            
    def create_widgets(self):
        """创建界面组件"""
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 单词列表区域 (reduced width)
        wordlist_group = QGroupBox("单词列表")
        wordlist_group.setStyleSheet("QGroupBox { font-size: 12pt; }")
        wordlist_group.setMaximumWidth(800)
        wordlist_layout = QVBoxLayout(wordlist_group)
        
        self.word_tree = QTreeWidget()
        self.word_tree.setHeaderLabels(["单词", "假名", "中文"])
        self.word_tree.setColumnWidth(0, 120)
        self.word_tree.setColumnWidth(1, 120)
        self.word_tree.setColumnWidth(2, 120)
        self.word_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 12pt;
            }
            QHeaderView::section {
                font-size: 12pt;
                padding: 5px;
            }
        """)
        
        wordlist_layout.addWidget(self.word_tree)
        main_layout.addWidget(wordlist_group, stretch=1)  # Add stretch factor
        
        # 右侧区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 设置区域 (reduced height)
        settings_group = QGroupBox("设置")
        settings_group.setStyleSheet("QGroupBox { font-size: 12pt; }")
        settings_group.setMaximumHeight(150)
        settings_layout = QHBoxLayout(settings_group)
        
        # 文件选择
        file_label = QLabel("单词文件:")
        file_label.setAlignment(Qt.AlignCenter)
        file_label.setStyleSheet("font-size: 12pt;")
        settings_layout.addWidget(file_label)
        
        # 初始化下拉菜单
        self.file_combo = QComboBox()
        self.file_combo.setStyleSheet("font-size: 12pt;")
        excel_files = [f for f in os.listdir() if f.endswith('.xlsx')]
        if excel_files:
            self.file_combo.addItems(excel_files)
            self.file_combo.setCurrentIndex(-1)  # No initial selection
        self.file_combo.currentTextChanged.connect(self.load_vocabulary)
        settings_layout.addWidget(self.file_combo)
        
        # 题目数量
        count_label = QLabel("题目数量:")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("font-size: 12pt;")
        settings_layout.addWidget(count_label)
        self.question_count = QSpinBox()
        self.question_count.setStyleSheet("font-size: 12pt;")
        # self.question_count.setRange(5, 100)
        self.question_count.setValue(self.total_questions)
        settings_layout.addWidget(self.question_count)
        
        # 开始按钮
        self.start_button = QPushButton("开始游戏")
        self.start_button.setStyleSheet("font-size: 12pt;")
        self.start_button.clicked.connect(self.start_game)
        settings_layout.addWidget(self.start_button)
        
        right_layout.addWidget(settings_group)
        right_layout.setStretch(1, 3)  # Give more space to game area
        
        # 游戏区域 (expanded)
        self.game_group = QGroupBox("游戏")
        self.game_group.setStyleSheet("QGroupBox { font-size: 12pt; }")
        game_layout = QVBoxLayout(self.game_group)
        
        # 游戏状态
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        self.correct_label = QLabel("正确\n0")
        self.correct_label.setStyleSheet("font-size: 16pt;")
        self.correct_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.correct_label)

        self.incorrect_label = QLabel("失误\n0")
        self.incorrect_label.setStyleSheet("font-size: 16pt;")
        self.incorrect_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.incorrect_label)
        
        self.score_label = QLabel("正确率\n0%")
        self.score_label.setStyleSheet("font-size: 16pt;")
        self.score_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.score_label)
        
        game_layout.addWidget(status_widget)
        
        # 问题显示区域
        self.question_label = QLabel("点击开始游戏")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet("""
            font-size: 28pt;
            padding: 10px;
            margin: 10px;
        """)
        self.question_label.setMinimumHeight(100)
        self.question_label.setWordWrap(True)
        game_layout.addWidget(self.question_label)
        
        # 发音按钮
        self.speak_button = QPushButton("🔊 播放发音")
        self.speak_button.setStyleSheet("font-size: 12pt;")
        self.speak_button.setEnabled(False)
        self.speak_button.clicked.connect(self.play_sound)
        game_layout.addWidget(self.speak_button)
        
        # 选项按钮
        options_widget = QWidget()
        options_layout = QGridLayout(options_widget)
        options_layout.setSpacing(15)
        options_layout.setContentsMargins(10, 10, 10, 10)
        
        self.option_buttons = []
        for i in range(4):
            btn = QPushButton("")
            btn.setMinimumSize(200, 80)
            # Set base font size first
            btn.setStyleSheet("font-size: 18pt;")
            # Then add other styles
            btn.setStyleSheet(btn.styleSheet() + """
                QPushButton {
                    padding: 15px;
                    background-color: #3a3a3a;
                    border: 2px solid #555;
                    border-radius: 5px;
                    color: #e0e0e0;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
            """)
            btn.setEnabled(False)
            btn.clicked.connect(lambda checked, idx=i: self.check_answer(idx))
            self.option_buttons.append(btn)
            # Place buttons in 2 rows of 2
            options_layout.addWidget(btn, i//2, i%2)
        
        game_layout.addWidget(options_widget)
        
        # 反馈标签
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet("font-size: 12pt;")
        game_layout.addWidget(self.feedback_label)
        
        right_layout.addWidget(self.game_group)
        main_layout.addWidget(right_widget, stretch=2)  # Add stretch factor
        
    def start_game(self):
        """开始新游戏"""
        if not self.word_dict:
            QMessageBox.warning(self, "错误", "单词列表为空，请先加载单词文件")
            return
            
        try:
            self.total_questions = self.question_count.value()
            if self.total_questions < 1:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "错误", "请输入有效的题目数量")
            return
            
        self.current_question = 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.incorrect_words = []
        
        self.update_status()
        self.new_question()
        
    def new_question(self):
        """生成新题目"""
        if self.current_question >= self.total_questions:
            self.game_over()
            return
            
        self.current_question += 1
        self.current_word, (self.current_kana, meaning) = random.choice(list(self.word_dict.items()))
        wrong_answers = random.sample(
            [v[1] for k, v in self.word_dict.items() if k != self.current_word],
            3
        )
        self.correct_answer = meaning
        options = [meaning] + wrong_answers
        random.shuffle(options)
        
        # 更新界面
        self.question_label.setText(self.current_kana)
        for i in range(4):
            self.option_buttons[i].setText(options[i])
            self.option_buttons[i].setEnabled(True)
            # Only reset color styles, keep font size
            self.option_buttons[i].setStyleSheet( self.option_buttons[i].styleSheet() + """
                QPushButton {
                    color: #e0e0e0;
                    background-color: #3a3a3a;
                }
            """)
        self.speak_button.setEnabled(True)
        self.feedback_label.setText("")
        
        # 自动播放发音
        # self.play_sound()
        self.update_status()
        
    def play_sound(self):
        """播放发音"""
        self.sound_thread = SoundThread(self.current_word, self.cache_dir)
        self.sound_thread.start()
        
    def update_status(self):
        """更新状态显示"""
        self.correct_label.setText(f"正确\n{self.correct_count}")
        self.incorrect_label.setText(f"失误\n{self.incorrect_count}")
        accuracy = int((self.correct_count / (self.correct_count + self.incorrect_count)) * 100) if self.current_question > 1 else 0
        self.score_label.setText(f"正确率\n{accuracy}%")
        
    def check_answer(self, selected_idx):
        """检查答案"""
        # 禁用按钮防止重复点击
        for btn in self.option_buttons:
            btn.setEnabled(False)
        self.speak_button.setEnabled(False)
            
        selected_text = self.option_buttons[selected_idx].text()
        if selected_text == self.correct_answer:
            self.handle_correct()
        else:
            self.handle_incorrect()
            
    def handle_correct(self):
        """处理正确答案"""
        self.correct_count += 1
        self.feedback_label.setText("✓ 回答正确！")
        self.feedback_label.setStyleSheet("color: green; font-size: 16pt;")
        self.update_status()
        
        # 延迟显示下一题
        QTimer.singleShot(500, self.new_question)
        
    def handle_incorrect(self):
        """处理错误答案"""
        self.incorrect_count += 1
        self.incorrect_words.append((self.current_word, self.current_kana, self.correct_answer))
        self.feedback_label.setText(f"✗ 错误！正确答案：{self.current_word}({self.correct_answer})")
        self.feedback_label.setStyleSheet("color: red; font-size: 16pt;")
        self.update_status()
        
        # 延迟显示下一题
        QTimer.singleShot(1000, self.new_question)
        
    def game_over(self):
        """游戏结束"""
        for btn in self.option_buttons:
            btn.setEnabled(False)
        self.speak_button.setEnabled(False)
        
        result_message = f"游戏结束！\n正确率: {int((self.correct_count / self.current_question) * 100)}%\n"
        
        if self.incorrect_words:
            result_message += "\n错误的单词:\n"
            for word, kana, meaning in self.incorrect_words:
                result_message += f"{word}({kana}) - {meaning}\n"
        
        QMessageBox.information(self, "游戏结果", result_message)
        
        # 重置游戏
        self.question_label.setText("点击开始游戏")
        self.feedback_label.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Use Fusion style for better dark theme support
    app.setStyle('Fusion')
    
    # 设置全局字体为微软雅黑Light
    font = app.font()
    font.setFamily("Microsoft YaHei Light")
    app.setFont(font)
    
    # 设置全局dark主题样式（包含标题栏细节）
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        QMainWindow::title {
            background-color: #2d2d2d;
            color: #e0e0e0;
            height: 30px;
            padding-left: 10px;
            margin: 2px;
        }
        QWidget {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: none;
        }
        QHeaderView::section {
            background-color: #3a3a3a;
            color: #e0e0e0;
            border: 1px solid #555;
            padding: 5px;
        }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 5px;
            margin-top: 15px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 2px 5px;
            margin-top: 1px;
            background-color: #2d2d2d;
        }
        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QTreeWidget {
            background-color: #252525;
            alternate-background-color: #2d2d2d;
        }
        QSpinBox, QComboBox {
            background-color: #3a3a3a;
            border: 1px solid #555;
            padding: 2px;
        }
        QLabel {
            color: #e0e0e0;
        }
    """)
    
    window = JapaneseVocabGame()
    window.show()
    sys.exit(app.exec_())
