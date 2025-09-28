import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import re
import os
import sys

class PharmacologyTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест по фармакодинамике")
        self.root.geometry("950x700")
        
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.total_questions = 0
        self.random_order = False
        self.user_answers = []
        self.file_path = None
        
        self.pdf_available = self.check_pdf_support()
        self.create_widgets()
        
    def check_pdf_support(self):
        """Проверка доступности PyPDF2"""
        try:
            import PyPDF2
            return True
        except ImportError:
            return False
        
    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм выбора файла
        file_frame = ttk.LabelFrame(main_frame, text="Выбор файла с вопросами", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Путь к файлу
        ttk.Label(file_frame, text="Путь к файлу:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        self.file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Кнопки файла
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Обзор", 
                  command=self.browse_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Загрузить", 
                  command=self.load_questions_from_file).pack(side=tk.LEFT, padx=2)
        
        # Информация о статусе
        info_frame = ttk.Frame(file_frame)
        info_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        pdf_status = "✓ PDF поддерживается" if self.pdf_available else "✗ PDF не поддерживается"
        pdf_color = "green" if self.pdf_available else "red"
        
        ttk.Label(info_frame, text=pdf_status, foreground=pdf_color).pack(side=tk.LEFT, padx=5)
        
        self.file_info_label = ttk.Label(info_frame, text="Файл не выбран")
        self.file_info_label.pack(side=tk.LEFT, padx=20)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Фрейм настроек теста
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки теста", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Режим вопросов
        ttk.Label(settings_frame, text="Порядок вопросов:").grid(row=0, column=0, padx=5, sticky=tk.W)
        
        self.order_var = tk.StringVar(value="sequential")
        ttk.Radiobutton(settings_frame, text="По порядку", 
                       variable=self.order_var, value="sequential",
                       command=self.toggle_order).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Radiobutton(settings_frame, text="Случайный порядок", 
                       variable=self.order_var, value="random",
                       command=self.toggle_order).grid(row=0, column=2, padx=5, sticky=tk.W)
        
        # Кнопки управления
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=0, column=3, padx=10, sticky=tk.E)
        
        self.start_button = ttk.Button(button_frame, text="Начать тест", 
                                      command=self.start_test, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Результаты", 
                  command=self.show_results).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Сбросить", 
                  command=self.reset_test).pack(side=tk.LEFT, padx=2)
        
        settings_frame.columnconfigure(3, weight=1)
        
        # Фрейм вопроса
        self.question_frame = ttk.LabelFrame(main_frame, text="Вопрос", padding="15")
        
        # Текст вопроса
        self.question_label = tk.Text(self.question_frame, wrap=tk.WORD, 
                                    height=5, font=("Arial", 11), bg="#f8f9fa",
                                    relief=tk.FLAT, padx=10, pady=10)
        self.question_label.pack(fill=tk.X, pady=(0, 15))
        self.question_label.config(state=tk.DISABLED)
        
        # Фрейм вариантов ответов
        answers_container = ttk.Frame(self.question_frame)
        answers_container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(answers_container, text="Варианты ответов:", 
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.answers_frame = ttk.Frame(answers_container)
        self.answers_frame.pack(fill=tk.BOTH, expand=True)
        
        self.answer_var = tk.StringVar()
        
        # Фрейм кнопок навигации
        nav_frame = ttk.Frame(self.question_frame)
        nav_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.prev_button = ttk.Button(nav_frame, text="← Назад", 
                                     command=self.previous_question)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.submit_button = ttk.Button(nav_frame, text="✅ Ответить", 
                                       command=self.check_answer)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(nav_frame, text="Вперед →", 
                                     command=self.next_question)
        self.next_button.pack(side=tk.RIGHT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе. Выберите файл с вопросами.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, padding="5")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Изначально скрываем элементы вопросов
        self.hide_question_elements()
    
    def browse_file(self):
        """Выбор файла через диалоговое окно"""
        file_types = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        if self.pdf_available:
            file_types.insert(0, ("PDF files", "*.pdf"))
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл с вопросами",
            filetypes=file_types
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_var.set(file_path)
            filename = os.path.basename(file_path)
            self.file_info_label.config(text=f"Выбран: {filename}")
            self.status_var.set(f"Файл '{filename}' выбран. Нажмите 'Загрузить' для загрузки вопросов.")
    
    def load_questions_from_file(self):
        """Загрузка вопросов из выбранного файла"""
        if not self.file_path:
            messagebox.showwarning("Внимание", "Сначала выберите файл с вопросами")
            return
        
        if not os.path.exists(self.file_path):
            messagebox.showerror("Ошибка", "Файл не существует")
            return
        
        try:
            self.status_var.set("Загрузка файла...")
            self.root.update()
            
            # Определяем тип файла
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            if file_ext == '.pdf':
                if not self.pdf_available:
                    messagebox.showerror("Ошибка", "Поддержка PDF недоступна")
                    return
                content = self.read_pdf_file()
            else:
                content = self.read_text_file()
            
            if content:
                self.parse_questions(content)
                self.start_button.config(state=tk.NORMAL)
                messagebox.showinfo("Успех", f"Загружено {len(self.questions)} вопросов")
                self.status_var.set(f"Загружено {len(self.questions)} вопросов. Нажмите 'Начать тест'.")
            else:
                messagebox.showerror("Ошибка", "Не удалось прочитать файл или файл пуст")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла:\n{str(e)}")
            self.status_var.set("Ошибка при загрузке файла")
    
    def read_text_file(self):
        """Чтение текстового файла"""
        encodings = ['utf-8', 'cp1251', 'latin-1', 'windows-1251']
        
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise Exception(f"Ошибка чтения файла ({encoding}): {str(e)}")
        
        raise Exception("Не удалось определить кодировку файла")
    
    def read_pdf_file(self):
        """Чтение PDF файла"""
        try:
            import PyPDF2
            
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    content += f"\n===== Page {page_num} =====\n"
                    content += page.extract_text() + "\n"
                
                return content
                
        except Exception as e:
            raise Exception(f"Ошибка чтения PDF: {str(e)}")
    
    def parse_questions(self, content):
        """Парсинг вопросов из содержимого файла"""
        self.questions = []
        
        # Разбиваем на страницы
        pages = re.split(r'===== Page \d+ =====', content)
        
        for page_num, page in enumerate(pages, 1):
            if not page.strip():
                continue
            
            # Ищем вопросы
            question_blocks = re.findall(r'#\d+.*?(?=#\d+|$)', page, re.DOTALL)
            
            for block in question_blocks:
                lines = [line.strip() for line in block.split('\n') if line.strip()]
                if len(lines) < 2:
                    continue
                
                # Первая строка - вопрос
                question_match = re.match(r'#\d+\s*(.*)', lines[0])
                if not question_match:
                    continue
                
                question_text = question_match.group(1).strip()
                correct_answers = []
                answer_options = []
                
                # Обрабатываем варианты ответов
                for line in lines[1:]:
                    if any(line.startswith(marker) for marker in ['$', 'S', 's', 'З', 'Э', '8']):
                        answer_text = line[1:].strip()
                        correct_answers.append(answer_text)
                        answer_options.append(answer_text)
                    elif line.startswith('?') or line.startswith('9'):
                        answer_text = line[1:].strip()
                        answer_options.append(answer_text)
                    elif line and len(line) > 1:  # Любая другая непустая строка
                        answer_options.append(line)
                
                if question_text and answer_options and correct_answers:
                    self.questions.append({
                        'question': question_text,
                        'options': answer_options,
                        'correct': correct_answers,
                        'user_answer': None,
                        'is_correct': False,
                        'page': page_num
                    })
        
        self.total_questions = len(self.questions)
    
    def hide_question_elements(self):
        """Скрыть элементы вопросов"""
        self.question_frame.pack_forget()
    
    def show_question_elements(self):
        """Показать элементы вопросов"""
        self.question_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def toggle_order(self):
        """Переключение режима порядка вопросов"""
        self.random_order = (self.order_var.get() == "random")
    
    def start_test(self):
        """Начало теста"""
        if not self.questions:
            messagebox.showerror("Ошибка", "Нет загруженных вопросов")
            return
        
        self.score = 0
        self.current_question_index = 0
        self.user_answers = [None] * len(self.questions)
        
        if self.random_order:
            random.shuffle(self.questions)
        
        self.show_question_elements()
        self.show_question()
        self.update_navigation_buttons()
        self.status_var.set(f"Тест начат. Вопрос 1 из {self.total_questions}")
    
    def show_question(self):
        """Показать текущий вопрос"""
        if self.current_question_index >= len(self.questions):
            return
        
        question_data = self.questions[self.current_question_index]
        
        # Очищаем предыдущие варианты
        for widget in self.answers_frame.winfo_children():
            widget.destroy()
        
        # Показываем вопрос
        self.question_label.config(state=tk.NORMAL)
        self.question_label.delete(1.0, tk.END)
        
        question_number = self.current_question_index + 1
        question_text = f"Вопрос {question_number}/{self.total_questions}"
        if 'page' in question_data:
            question_text += f" (Страница {question_data['page']})"
        question_text += f"\n\n{question_data['question']}"
        
        self.question_label.insert(1.0, question_text)
        self.question_label.config(state=tk.DISABLED)
        
        # Показываем варианты ответов
        for option in question_data['options']:
            rb = ttk.Radiobutton(self.answers_frame, text=option, 
                               variable=self.answer_var, value=option,
                               style='TRadiobutton')
            rb.pack(anchor=tk.W, pady=3, padx=10)
        
        # Восстанавливаем ответ пользователя
        user_answer = self.user_answers[self.current_question_index]
        self.answer_var.set(user_answer if user_answer else '')
        
        self.update_status()
    
    def check_answer(self):
        """Проверка ответа"""
        user_answer = self.answer_var.get()
        if not user_answer:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите вариант ответа")
            return
        
        question_data = self.questions[self.current_question_index]
        self.user_answers[self.current_question_index] = user_answer
        
        # Проверяем правильность
        is_correct = user_answer in question_data['correct']
        question_data['is_correct'] = is_correct
        question_data['user_answer'] = user_answer
        
        if is_correct:
            self.score += 1
            messagebox.showinfo("Результат", "✅ Правильный ответ!")
        else:
            correct_answers = "\n".join(f"• {ans}" for ans in question_data['correct'])
            messagebox.showinfo("Результат", 
                              f"❌ Неправильно!\n\nПравильные ответы:\n{correct_answers}")
        
        self.update_status()
    
    def next_question(self):
        """Следующий вопрос"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.show_question()
            self.update_navigation_buttons()
        else:
            messagebox.showinfo("Тест завершен", "Вы ответили на все вопросы!")
    
    def previous_question(self):
        """Предыдущий вопрос"""
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.show_question()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Обновление состояния кнопок навигации"""
        self.prev_button.config(state=tk.NORMAL if self.current_question_index > 0 else tk.DISABLED)
        has_next = self.current_question_index < len(self.questions) - 1
        self.next_button.config(state=tk.NORMAL if has_next else tk.DISABLED)
    
    def update_status(self):
        """Обновление статусной строки"""
        answered = sum(1 for ans in self.user_answers if ans is not None)
        progress = f"Прогресс: {answered}/{self.total_questions}"
        score = f"Правильных: {self.score}"
        current = f"Текущий: {self.current_question_index + 1}/{self.total_questions}"
        
        self.status_var.set(f"{progress} | {score} | {current}")
    
    def show_results(self):
        """Показать результаты теста"""
        answered = sum(1 for ans in self.user_answers if ans is not None)
        
        if answered == 0:
            messagebox.showinfo("Результаты", "Тест еще не пройден")
            return
        
        correct_count = sum(1 for q in self.questions if q['is_correct'])
        percentage = (correct_count / self.total_questions) * 100
        
        # Определяем оценку
        if percentage >= 90:
            grade = "5 (Отлично) 🎉"
        elif percentage >= 75:
            grade = "4 (Хорошо) 👍"
        elif percentage >= 60:
            grade = "3 (Удовлетворительно) 👌"
        elif percentage >= 40:
            grade = "2 (Неудовлетворительно) 📚"
        else:
            grade = "1 (Плохо) 💪"
        
        result_text = (
            f"Результаты теста:\n\n"
            f"Всего вопросов: {self.total_questions}\n"
            f"Отвечено: {answered}\n"
            f"Правильных ответов: {correct_count}\n"
            f"Процент правильных: {percentage:.1f}%\n\n"
            f"Оценка: {grade}"
        )
        
        messagebox.showinfo("Итоговые результаты", result_text)
    
    def reset_test(self):
        """Сброс теста"""
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.total_questions = 0
        self.user_answers = []
        self.file_path = None
        self.file_path_var.set("")
        self.file_info_label.config(text="Файл не выбран")
        self.start_button.config(state=tk.DISABLED)
        self.hide_question_elements()
        self.status_var.set("Тест сброшен. Выберите новый файл.")

def main():
    root = tk.Tk()
    app = PharmacologyTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()