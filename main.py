import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector


# Переменная для хранения пароля
db_password = None


# Окно ввода пароля
def ask_password():
    def on_submit():
        global db_password
        db_password = entry_pass.get()
        if db_password:
            root.destroy()  # Закрываем окно ввода
        else:
            messagebox.showwarning("Ошибка", "Введите пароль!")

    # Создаем окно ввода пароля
    root = tk.Tk()
    root.title("Вход в систему")
    root.geometry("300x120")
    root.resizable(False, False)

    tk.Label(root, text="Пароль от БД:").pack(pady=5)
    global entry_pass
    entry_pass = tk.Entry(root, show="*", width=30)
    entry_pass.pack(pady=5)

    tk.Button(root, text="Войти", command=on_submit).pack(pady=5)

    root.mainloop()


# Подключение к БД
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=db_password,
        database="my_db"
    )


# === СОЗДАНИЕ ПРОИЗВОЛЬНОЙ ТАБЛИЦЫ С ОГРАНИЧЕНИЯМИ И ВНЕШНИМИ КЛЮЧАМИ ===

# Получение списка таблиц из базы
def get_tables():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    db.close()
    return tables


# Получение структуры таблицы
def get_table_columns(table_name):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [col['Field'] for col in cursor.fetchall()]
    db.close()
    return columns


# Окно создания таблицы
def create_custom_table_window():
    win = tk.Toplevel()
    win.title("Создать новую таблицу")

    tk.Label(win, text="Имя новой таблицы:").pack(pady=5)
    entry_table_name = tk.Entry(win, width=30)
    entry_table_name.pack(padx=10, pady=5)

    fields_frame = tk.Frame(win)
    fields_frame.pack(padx=10, pady=10)

    field_rows = []

    types = ['INT', 'VARCHAR(255)', 'TEXT', 'DATE', 'DATETIME', 'BOOLEAN']
    constraints = ['NOT NULL', 'UNIQUE', 'DEFAULT']

    def add_field_row():
        row = {}

        frame = tk.Frame(fields_frame)
        frame.pack(anchor='w', pady=5)

        # Имя столбца
        tk.Label(frame, text="Имя поля:").pack(side=tk.LEFT)
        entry_name = tk.Entry(frame, width=10)
        entry_name.pack(side=tk.LEFT, padx=5)

        # Тип данных
        tk.Label(frame, text="Тип:").pack(side=tk.LEFT)
        type_var = tk.StringVar()
        combo_type = ttk.Combobox(frame, textvariable=type_var, values=types, state="readonly", width=10)
        combo_type.set('VARCHAR(255)')
        combo_type.pack(side=tk.LEFT, padx=5)

        # NOT NULL
        not_null_var = tk.BooleanVar()
        tk.Checkbutton(frame, text="NOT NULL", variable=not_null_var).pack(side=tk.LEFT, padx=5)

        # UNIQUE
        unique_var = tk.BooleanVar()
        tk.Checkbutton(frame, text="UNIQUE", variable=unique_var).pack(side=tk.LEFT, padx=5)

        # DEFAULT
        default_var = tk.StringVar()
        entry_default = tk.Entry(frame, textvariable=default_var, width=8)
        entry_default.insert(0, "DEFAULT")
        entry_default.pack(side=tk.LEFT, padx=5)

        row['frame'] = frame
        row['entry_name'] = entry_name
        row['combo_type'] = combo_type
        row['not_null_var'] = not_null_var
        row['unique_var'] = unique_var
        row['default_var'] = default_var

        field_rows.append(row)

    def create_table():
        table_name = entry_table_name.get().strip()
        if not table_name:
            messagebox.showwarning("Ошибка", "Имя таблицы не может быть пустым!")
            return

        fields = []
        primary_key = selected_primary_key.get()

        for idx, row in enumerate(field_rows):
            name = row['entry_name'].get().strip()
            data_type = row['combo_type'].get()
            not_null = row['not_null_var'].get()
            unique = row['unique_var'].get()
            default_value = row['default_var'].get().strip()

            if not name:
                continue  # Пропускаем пустые строки

            field_sql = f"`{name}` {data_type}"

            if not_null:
                field_sql += " NOT NULL"

            if unique:
                field_sql += " UNIQUE"

            if default_value and default_value != "DEFAULT":
                if data_type.startswith("VARCHAR") or data_type == "TEXT":
                    field_sql += f" DEFAULT '{default_value}'"
                else:
                    field_sql += f" DEFAULT {default_value}"

            fields.append(field_sql)

        if not fields:
            messagebox.showwarning("Ошибка", "Добавьте хотя бы одно поле!")
            return

        # Добавляем первичный ключ
        if primary_key:
            fields.append(f"PRIMARY KEY ({primary_key})")

        # Собираем запрос
        query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(fields)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(query)
            db.commit()
            db.close()
            messagebox.showinfo("Успех", f"Таблица '{table_name}' создана!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании таблицы:\n{e}")

    def add_foreign_key():
        fk_win = tk.Toplevel()
        fk_win.title("Добавить внешний ключ")

        tk.Label(fk_win, text="Название внешнего ключа:").pack(pady=5)
        entry_fk_name = tk.Entry(fk_win, width=30)
        entry_fk_name.pack(padx=10, pady=5)

        tk.Label(fk_win, text="Столбец текущей таблицы:").pack(pady=5)
        entry_column = tk.Entry(fk_win, width=30)
        entry_column.pack(padx=10, pady=5)

        tables = get_tables()
        tk.Label(fk_win, text="Таблица-ссылка:").pack(pady=5)
        fk_table_var = tk.StringVar()
        fk_table_combo = ttk.Combobox(fk_win, textvariable=fk_table_var, values=tables, state="readonly")
        fk_table_combo.pack(padx=10, pady=5)

        def set_reference_column(event=None):
            table = fk_table_combo.get()
            if table:
                columns = get_table_columns(table)
                fk_col_combo['values'] = columns
                if columns:
                    fk_col_combo.current(0)

        tk.Label(fk_win, text="Поле ссылки:").pack(pady=5)
        fk_col_var = tk.StringVar()
        fk_col_combo = ttk.Combobox(fk_win, textvariable=fk_col_var, state="readonly")
        fk_col_combo.pack(padx=10, pady=5)

        fk_table_combo.bind("<<ComboboxSelected>>", lambda e: set_reference_column())

        def save_foreign_key():
            fk_name = entry_fk_name.get().strip()
            column = entry_column.get().strip()
            ref_table = fk_table_combo.get().strip()
            ref_column = fk_col_combo.get().strip()

            if not all([fk_name, column, ref_table, ref_column]):
                messagebox.showwarning("Ошибка", "Заполните все поля внешнего ключа!")
                return

            try:
                db = connect_db()
                cursor = db.cursor()
                cursor.execute(f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{fk_name}` FOREIGN KEY (`{column}`) REFERENCES `{ref_table}`(``{ref_column}`);")
                db.commit()
                db.close()
                messagebox.showinfo("Успех", f"Внешний ключ `{fk_name}` добавлен!")
                fk_win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить внешний ключ:\n{e}")

        tk.Button(fk_win, text="Добавить внешний ключ", command=save_foreign_key).pack(pady=10)

    # Форма для добавления полей
    tk.Label(win, text="Добавьте поля таблицы:", font=("Arial", 10, "bold")).pack(pady=5)

    field_controls = tk.Frame(win)
    field_controls.pack()

    add_button = tk.Button(field_controls, text="Добавить поле", command=add_field_row)
    add_button.pack(side=tk.LEFT, padx=5)

    # Выбор первичного ключа
    tk.Label(win, text="Первичный ключ (оставь пустым, чтобы использовать id):").pack(pady=5)
    selected_primary_key = tk.StringVar()
    entry_pk = tk.Entry(win, textvariable=selected_primary_key, width=30)
    entry_pk.pack(padx=10, pady=5)

    # Кнопка создания таблицы
    tk.Button(win, text="Создать таблицу", command=create_table).pack(pady=10)

    # Кнопка добавления внешнего ключа
    tk.Button(win, text="Добавить внешний ключ", command=add_foreign_key).pack(pady=5)

    # По умолчанию одно поле
    add_field_row()


# === ГЛАВНОЕ МЕНЮ ===
def create_main_menu():
    root = tk.Tk()
    root.title("Главная")
    root.geometry("300x200")
    root.resizable(False, False)

    tk.Label(root, text="Выберите действие:", font=("Arial", 14)).pack(pady=20)

    tk.Button(root, text="Создать новую таблицу", width=25, command=create_custom_table_window).pack(pady=5)

    root.mainloop()


# Точка входа
if __name__ == "__main__":
    ask_password()
    if db_password:
        create_main_menu()