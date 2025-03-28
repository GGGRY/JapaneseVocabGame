import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import random
from gtts import gTTS
from playsound import playsound
import os
import threading

class JapaneseVocabGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("日语单词记忆游戏")
        self.geometry("1000x600")
        
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
        self.incorrect_words = []
        
        # 创建界面
        self.create_widgets()
        
    def load_vocabulary(self):
        """从选择的文件加载单词数据"""
        filename = self.file_var.get() if hasattr(self, 'file_var') else ""
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename, header=None)
            else:  # Excel文件
                df = pd.read_excel(filename, header=0)
                
            self.word_dict = {}
            for _, row in df.iterrows():
                japanese = row[0]
                kana = row[1]
                meaning = row[3]
                self.word_dict[japanese] = [kana, meaning]
                
            # 更新单词列表显示
            if hasattr(self, 'word_tree'):
                self.word_tree.delete(*self.word_tree.get_children())
                for word, (kana, meaning) in self.word_dict.items():
                    self.word_tree.insert("", "end", values=(word, kana, meaning))
                    
        except Exception as e:
            messagebox.showerror("错误", f"无法加载单词文件: {e}")
            if not hasattr(self, 'word_dict'):
                self.word_dict = {}  # 保持为空
            
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 单词列表区域
        wordlist_frame = tk.LabelFrame(main_frame, text="单词列表", padx=5, pady=5)
        wordlist_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.word_tree = ttk.Treeview(wordlist_frame, columns=("word", "kana", "meaning"), show="headings")
        self.word_tree.heading("word", text="单词")
        self.word_tree.heading("kana", text="假名")
        self.word_tree.heading("meaning", text="中文")
        self.word_tree.column("word", width=100)
        self.word_tree.column("kana", width=100)
        self.word_tree.column("meaning", width=100)
        
        scrollbar = ttk.Scrollbar(wordlist_frame, orient="vertical", command=self.word_tree.yview)
        self.word_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_tree.pack(fill=tk.BOTH, expand=True)
        
        # 初始时不填充单词列表
        
        # 右侧区域
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 设置区域
        settings_frame = tk.LabelFrame(right_frame, text="设置", padx=5, pady=5)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 文件选择
        tk.Label(settings_frame, text="单词文件:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar(value="")
        # Get all .xlsx files in current directory
        # excel_files = [f for f in os.listdir() if f.endswith('.xlsx')]
        # self.file_combobox = ttk.Combobox(
        #     settings_frame, 
        #     textvariable=self.file_var,
        #     values=excel_files,
        #     state="readonly",
        #     width=15
        # )
        # Get all .csv files in current directory
        csv_files = [f for f in os.listdir() if f.endswith('.csv')]
        self.file_combobox = ttk.Combobox(
            settings_frame, 
            textvariable=self.file_var,
            values=csv_files,
            state="readonly",
            width=15
        )
        self.file_combobox.pack(side=tk.LEFT, padx=5)
        self.file_combobox.bind("<<ComboboxSelected>>", lambda e: self.load_vocabulary())
        
        tk.Label(settings_frame, text="题目数量:").pack(side=tk.LEFT)
        self.question_count = tk.Spinbox(settings_frame, from_=5, to=50, width=5)
        self.question_count.pack(side=tk.LEFT, padx=5)
        self.question_count.delete(0, "end")
        self.question_count.insert(0, str(self.total_questions))
        
        self.start_button = tk.Button(settings_frame, text="开始游戏", command=self.start_game)
        self.start_button.pack(side=tk.RIGHT)
        
        # 游戏区域
        self.game_frame = tk.LabelFrame(right_frame, text="游戏", padx=5, pady=5)
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        # 游戏状态
        self.status_frame = tk.Frame(self.game_frame)
        self.status_frame.pack(pady=10)
        
        self.progress_label = tk.Label(
            self.status_frame, 
            text="进度: 0/0",
            font=("Arial", 12)
        )
        self.progress_label.pack(side=tk.LEFT, padx=20)
        
        self.score_label = tk.Label(
            self.status_frame,
            text="正确率: 0%",
            font=("Arial", 12)
        )
        self.score_label.pack(side=tk.RIGHT, padx=20)
        
        # 问题显示区域
        self.question_label = tk.Label(
            self.game_frame, 
            text="点击开始游戏", 
            font=("Microsoft YaHei", 28),
            pady=20
        )
        self.question_label.pack()
        
        # 发音按钮
        self.speak_button = tk.Button(
            self.game_frame,
            text="🔊 播放发音",
            command=self.play_sound,
            font=("Arial", 12),
            state=tk.DISABLED
        )
        self.speak_button.pack()
        
        # 选项按钮
        self.option_buttons = []
        options_frame = tk.Frame(self.game_frame)
        options_frame.pack(pady=20)
        for i in range(4):
            btn = tk.Button(
                options_frame,
                text="",
                width=20,
                height=2,
                font=("Arial", 12),
                command=lambda idx=i: self.check_answer(idx),
                state=tk.DISABLED
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=5)
            self.option_buttons.append(btn)
            
        # 反馈标签
        self.feedback_label = tk.Label(
            self.game_frame,
            text="",
            font=("Arial", 12)
        )
        self.feedback_label.pack()
        
    def start_game(self):
        """开始新游戏"""
        try:
            self.total_questions = int(self.question_count.get())
            if self.total_questions < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的题目数量")
            return
            
        self.current_question = 0
        self.correct_count = 0
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
        self.question_label.config(text=self.current_kana)
        for i in range(4):
            self.option_buttons[i].config(
                text=options[i],
                state=tk.NORMAL,
                bg="SystemButtonFace"
            )
        self.speak_button.config(state=tk.NORMAL)
        self.feedback_label.config(text="")
        
        # 自动播放发音
        # threading.Thread(target=self.generate_and_play_sound).start()
        self.update_status()
        
    def generate_and_play_sound(self):
        """生成并播放发音"""
        file_path = os.path.join(self.cache_dir, f"{self.current_word}.mp3")
        
        if not os.path.exists(file_path):
            try:
                tts = gTTS(text=self.current_word, lang='ja')
                tts.save(file_path)
            except Exception as e:
                print(f"生成发音失败: {e}")
                return
                
        playsound(file_path)
        
    def play_sound(self):
        """按钮点击播放发音"""
        threading.Thread(target=self.generate_and_play_sound).start()
        
    def update_status(self):
        """更新状态显示"""
        self.progress_label.config(text=f"进度: {self.current_question}/{self.total_questions}")
        if self.current_question > 0:
            accuracy = int((self.correct_count / (self.current_question - 1)) * 100) if self.current_question > 1 else 0
            self.score_label.config(text=f"正确率: {accuracy}%")
        
    def check_answer(self, selected_idx):
        """检查答案"""
        # 禁用按钮防止重复点击
        for btn in self.option_buttons:
            btn.config(state=tk.DISABLED)
        self.speak_button.config(state=tk.DISABLED)
            
        selected_text = self.option_buttons[selected_idx].cget("text")
        if selected_text == self.correct_answer:
            self.handle_correct()
        else:
            self.handle_incorrect()
            
    def handle_correct(self):
        """处理正确答案"""
        self.correct_count += 1
        self.feedback_label.config(
            text="✓ 回答正确！",
            fg="green"
        )
        self.update_status()
        self.after(1000, self.new_question)
        
    def handle_incorrect(self):
        """处理错误答案"""
        self.incorrect_words.append((self.current_word, self.current_kana, self.correct_answer))
        self.feedback_label.config(
            text=f"✗ 错误！正确答案：{self.current_word}({self.correct_answer})",
            fg="red"
        )
        self.update_status()
        self.after(2000, self.new_question)
        
    def game_over(self):
        """游戏结束"""
        for btn in self.option_buttons:
            btn.config(state=tk.DISABLED)
        self.speak_button.config(state=tk.DISABLED)
        
        result_message = f"游戏结束！\n正确率: {int((self.correct_count / self.total_questions) * 100)}%\n"
        
        if self.incorrect_words:
            result_message += "\n错误的单词:\n"
            for word, kana, meaning in self.incorrect_words:
                result_message += f"{word}({kana}) - {meaning}\n"
        
        messagebox.showinfo("游戏结果", result_message)
        
        # 重置游戏
        self.question_label.config(text="点击开始游戏")
        self.feedback_label.config(text="")
        
if __name__ == "__main__":
    app = JapaneseVocabGame()
    app.mainloop()
