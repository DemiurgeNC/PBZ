import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from tkinter import filedialog

class DatabaseApp:
    def __init__(self, master, connection_params):
        self.master = master
        self.connection_params = connection_params
        self.master.title("СМОТРИ БД IT-компании")
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')
        self.conn = sqlite3.connect(**connection_params)
        self.cursor = self.conn.cursor()
        self.table_names = self.get_table_names()
        for table_name in self.table_names:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=table_name)
            self.create_table_view(frame, table_name)

    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]

    def create_table_view(self, frame, table_name):
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.pack(expand=True, fill='both')
        
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(tree, table_name, c, False))
            tree.column(col, width=100, anchor='center')
        
        self.populate_treeview(tree, table_name)
        
        add_button = tk.Button(frame, text="Добавить", command=lambda: self.add_row(tree, table_name))
        add_button.pack(side=tk.LEFT, padx=10)
        
        delete_button = tk.Button(frame, text="Удалить", command=lambda: self.delete_row(tree, table_name))
        delete_button.pack(side=tk.LEFT, padx=10)
        
        edit_button = tk.Button(frame, text="Изменить", command=lambda: self.edit_row(tree, table_name))
        edit_button.pack(side=tk.LEFT, padx=10)
        
        refresh_button = tk.Button(frame, text="Обновить", command=lambda: self.populate_treeview(tree, table_name))
        refresh_button.pack(side=tk.LEFT, padx=10)
        
        search_entry = tk.Entry(frame)
        search_entry.pack(side=tk.LEFT, padx=10)
        
        search_button = tk.Button(frame, text="Поиск", command=lambda: self.search_treeview(tree, search_entry.get()))
        search_button.pack(side=tk.LEFT, padx=10)
        
        report_button = tk.Button(frame, text="Создать отчет", command=lambda table_name=table_name: self.generate_report(table_name))
        report_button.pack(side=tk.LEFT, padx=10)

    def populate_treeview(self, tree, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name};")
        data = self.cursor.fetchall()
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert('', 'end', values=row)

    def add_row(self, tree, table_name):
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]
        
        add_dialog = tk.Toplevel(self.master)
        add_dialog.title("Добавить строку")
        entry_widgets = []
        
        for col in columns:
            label = tk.Label(add_dialog, text=col)
            label.grid(row=columns.index(col), column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(add_dialog)
            entry.grid(row=columns.index(col), column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)
        
        def insert_row():
            values = [entry.get() for entry in entry_widgets]
            placeholders = ', '.join(['?' for _ in values])
            query = f"INSERT INTO {table_name} VALUES ({placeholders});"
            self.cursor.execute(query, values)
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            add_dialog.destroy()

        submit_button = tk.Button(add_dialog, text="Подтвердить", command=insert_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def delete_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления.")
            return
        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту строку?")
        if not confirm:
            return
        values = tree.item(selected_item)['values']
        where_clause = ' AND '.join([f"{column} = ?" for column in tree['columns']])
        query = f"DELETE FROM {table_name} WHERE {where_clause};"
        self.cursor.execute(query, values)
        self.conn.commit()
        self.populate_treeview(tree, table_name)

    def edit_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для изменения.")
            return
        values = tree.item(selected_item)['values']
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]
        
        edit_dialog = tk.Toplevel(self.master)
        edit_dialog.title("Изменить строку")
        entry_widgets = []
        
        for col, value in zip(columns, values):
            label = tk.Label(edit_dialog, text=col)
            label.grid(row=columns.index(col), column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(edit_dialog)
            entry.insert(0, value)
            entry.grid(row=columns.index(col), column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)
        
        def update_row():
            new_values = [entry.get() for entry in entry_widgets]
            set_clause = ', '.join([f"{column} = ?" for column in columns])
            where_clause = ' AND '.join([f"{column} = ?" for column in columns])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"
            self.cursor.execute(query, new_values + values)
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            edit_dialog.destroy()

        submit_button = tk.Button(edit_dialog, text="Подтвердить", command=update_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def sort_treeview(self, tree, table_name, column, reverse):
        query = f"SELECT * FROM {table_name} ORDER BY {column} {'DESC' if reverse else 'ASC'};"
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert('', 'end', values=row)
        tree.heading(column, command=lambda: self.sort_treeview(tree, table_name, column, not reverse))

    def search_treeview(self, tree, search_term):
        for item in tree.get_children():
            values = tree.item(item)['values']
            if any(str(search_term).lower() in str(value).lower() for value in values):
                tree.selection_add(item)
            else:
                tree.selection_remove(item)

    def generate_report(self, table_name):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile=f"{table_name}_report")
        if not file_path:
            return
        with open(file_path, 'w') as report_file:
            report_file.write(f"Отчет по таблице: {table_name}\n")
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in self.cursor.fetchall()]
            report_file.write("Столбцы: " + ", ".join(columns) + "\n")
            self.cursor.execute(f"SELECT * FROM {table_name};")
            data = self.cursor.fetchall()
            report_file.write("Данные:\n")
            for row in data:
                report_file.write("\t" + ", ".join(str(value) for value in row) + "\n")
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = self.cursor.fetchone()[0]
            report_file.write(f"Количество строк: {row_count}\n")
        messagebox.showinfo("Создание отчета", f"Отчет для таблицы {table_name} успешно создан.")

if __name__ == "__main__":
    connection_params = {"database": "it_company.db"}

    conn = sqlite3.connect(**connection_params)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Проект (
        id INTEGER PRIMARY KEY,
        название TEXT,
        дата_старта TEXT,
        дата_окончания TEXT,
        статус TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Разработчик (
        id INTEGER PRIMARY KEY,
        имя TEXT,
        специализация TEXT,
        проект_id INTEGER,
        опыт INTEGER,
        FOREIGN KEY (проект_id) REFERENCES Проект(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Заказчик (
        id INTEGER PRIMARY KEY,
        имя TEXT,
        контакт TEXT,
        проект_id INTEGER,
        бюджет REAL,
        FOREIGN KEY (проект_id) REFERENCES Проект(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Тестировщик (
        id INTEGER PRIMARY KEY,
        имя TEXT,
        специализация TEXT,
        проект_id INTEGER,
        опыт INTEGER,
        FOREIGN KEY (проект_id) REFERENCES Проект(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS База_данных (
        id INTEGER PRIMARY KEY,
        название TEXT,
        тип TEXT,
        проект_id INTEGER,
        размер REAL,
        FOREIGN KEY (проект_id) REFERENCES Проект(id)
    )
    """)

    cursor.execute("DELETE FROM Проект;")
    cursor.execute("DELETE FROM Разработчик;")
    cursor.execute("DELETE FROM Заказчик;")
    cursor.execute("DELETE FROM Тестировщик;")
    cursor.execute("DELETE FROM База_данных;")

    # Заполнение таблиц тестовыми данными
cursor.execute("INSERT INTO Проект VALUES (1, 'Разработка сайта', '2023-01-01', '2023-12-31', 'В процессе')")
cursor.execute("INSERT INTO Проект VALUES (2, 'Мобильное приложение', '2023-02-15', '2024-05-30', 'Завершен')")
cursor.execute("INSERT INTO Проект VALUES (3, 'Система управления', '2023-06-01', '2024-03-01', 'В процессе')")
cursor.execute("INSERT INTO Проект VALUES (4, 'Интернет-магазин', '2023-07-01', '2024-01-01', 'В процессе')")
cursor.execute("INSERT INTO Проект VALUES (5, 'Блокчейн-платформа', '2023-09-01', '2024-06-30', 'Планируется')")

cursor.execute("INSERT INTO Разработчик VALUES (1, 'Иванов Иван', 'Frontend', 1, 3)")
cursor.execute("INSERT INTO Разработчик VALUES (2, 'Петров Петр', 'Backend', 2, 5)")
cursor.execute("INSERT INTO Разработчик VALUES (3, 'Сидоров Сидор', 'Fullstack', 3, 2)")
cursor.execute("INSERT INTO Разработчик VALUES (4, 'Кузнецова Анна', 'Frontend', 4, 4)")
cursor.execute("INSERT INTO Разработчик VALUES (5, 'Михайлов Дмитрий', 'Backend', 5, 6)")

cursor.execute("INSERT INTO Заказчик VALUES (1, 'ООО Рога и Копыта', 'contact1@example.com', 1, 50000)")
cursor.execute("INSERT INTO Заказчик VALUES (2, 'ЗАО Технологии Будущего', 'contact2@example.com', 2, 200000)")
cursor.execute("INSERT INTO Заказчик VALUES (3, 'ООО АвтоМир', 'contact3@example.com', 3, 75000)")
cursor.execute("INSERT INTO Заказчик VALUES (4, 'ПАО Инновации', 'contact4@example.com', 4, 300000)")
cursor.execute("INSERT INTO Заказчик VALUES (5, 'ТехноГрупп', 'contact5@example.com', 5, 45000)")

cursor.execute("INSERT INTO Тестировщик VALUES (1, 'Петров Петр', 'Functional', 1, 5)")
cursor.execute("INSERT INTO Тестировщик VALUES (2, 'Иванова Ирина', 'Performance', 2, 4)")
cursor.execute("INSERT INTO Тестировщик VALUES (3, 'Сергеев Сергей', 'Security', 3, 6)")
cursor.execute("INSERT INTO Тестировщик VALUES (4, 'Кузнецова Анна', 'Functional', 4, 3)")
cursor.execute("INSERT INTO Тестировщик VALUES (5, 'Лебедев Павел', 'Automation', 5, 7)")

cursor.execute("INSERT INTO База_данных VALUES (1, 'PostgreSQL', 'Relational', 1, 100.5)")
cursor.execute("INSERT INTO База_данных VALUES (2, 'MySQL', 'Relational', 2, 150.0)")
cursor.execute("INSERT INTO База_данных VALUES (3, 'MongoDB', 'NoSQL', 3, 200.5)")
cursor.execute("INSERT INTO База_данных VALUES (4, 'Redis', 'NoSQL', 4, 50.0)")
cursor.execute("INSERT INTO База_данных VALUES (5, 'Oracle', 'Relational', 5, 120.0)")

conn.commit()

conn.close()

try:
    root = tk.Tk()
    app = DatabaseApp(root, connection_params)
    root.mainloop()
except sqlite3.Error as err:
    print(f"Error: {err}")
