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


# Получение списка таблиц из базы данных
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
    cursor = db.cursor()
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        db.close()
        return columns
    except Exception as e:
        db.close()
        return None


# Загрузка записей из таблицы
def load_table_data(tree, table_name):
    for item in tree.get_children():
        tree.delete(item)

    db = connect_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            values = [row[col] for col in row]
            tree.insert("", tk.END, values=values)
        db.close()
    except Exception as e:
        db.close()
        messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")


# === СОЗДАНИЕ ТАБЛИЦЫ ===

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

        tk.Label(frame, text="Имя поля:").pack(side=tk.LEFT)
        entry_name = tk.Entry(frame, width=10)
        entry_name.pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Тип:").pack(side=tk.LEFT)
        type_var = tk.StringVar()
        combo_type = ttk.Combobox(frame, textvariable=type_var, values=types, state="readonly", width=10)
        combo_type.set('VARCHAR(255)')
        combo_type.pack(side=tk.LEFT, padx=5)

        not_null_var = tk.BooleanVar()
        tk.Checkbutton(frame, text="NOT NULL", variable=not_null_var).pack(side=tk.LEFT, padx=5)

        unique_var = tk.BooleanVar()
        tk.Checkbutton(frame, text="UNIQUE", variable=unique_var).pack(side=tk.LEFT, padx=5)

        default_var = tk.StringVar()
        entry_default = tk.Entry(frame, textvariable=default_var, width=8)
        entry_default.insert(0, "значение")
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
        for row in field_rows:
            name = row['entry_name'].get().strip()
            data_type = row['combo_type'].get()
            not_null = row['not_null_var'].get()
            unique = row['unique_var'].get()
            default_value = row['default_var'].get().strip()

            if not name:
                continue

            field_sql = f"`{name}` {data_type}"

            if not_null:
                field_sql += " NOT NULL"

            if unique:
                field_sql += " UNIQUE"

            if default_value and default_value != "значение":
                if data_type.startswith("VARCHAR") or data_type == "TEXT":
                    field_sql += f" DEFAULT '{default_value}'"
                elif data_type == "BOOLEAN":
                    field_sql += f" DEFAULT {default_value.upper()}"
                else:
                    field_sql += f" DEFAULT {default_value}"

            fields.append(field_sql)

        if not fields:
            messagebox.showwarning("Ошибка", "Добавьте хотя бы одно поле!")
            return

        query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(fields)}, id INT PRIMARY KEY AUTO_INCREMENT) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(query)
            db.commit()
            db.close()
            messagebox.showinfo("Успех", f"Таблица '{table_name}' создана!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать таблицу:\n{e}")

    # Кнопка добавления строки
    tk.Button(win, text="Добавить поле", command=add_field_row).pack(pady=5)

    # Кнопка создания таблицы
    tk.Button(win, text="Создать таблицу", command=create_table).pack(pady=10)

    # По умолчанию одно поле
    add_field_row()


# === ПОКАЗ ВСЕХ ТАБЛИЦ И РАБОТА С НИМИ ===

# Окно: список таблиц
def show_all_tables_window():
    tables = get_tables()
    if not tables:
        messagebox.showinfo("Нет таблиц", "В базе пока нет таблиц")
        return

    win = tk.Toplevel()
    win.title("Все таблицы")

    tk.Label(win, text="Список таблиц:", font=("Arial", 12)).pack(pady=5)

    listbox = tk.Listbox(win, width=40, height=15)
    listbox.pack(padx=10, pady=5)

    for table in tables:
        listbox.insert(tk.END, table)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Открыть таблицу", command=lambda: open_selected_table(listbox)).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Удалить таблицу", command=lambda: delete_selected_table(listbox, win)).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Обновить", command=lambda: [win.destroy(), show_all_tables_window()]).pack(side=tk.LEFT, padx=5)


# Открытие выбранной таблицы
def open_selected_table(listbox):
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите таблицу")
        return

    table_name = listbox.get(selected)
    open_table_window(table_name)


# Удаление выбранной таблицы
def delete_selected_table(listbox, window):
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите таблицу для удаления")
        return

    table_name = listbox.get(selected[0])

    confirm = messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить таблицу '{table_name}'?")
    if not confirm:
        return

    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        db.commit()
        db.close()
        messagebox.showinfo("Успех", f"Таблица '{table_name}' удалена!")
        window.destroy()
        show_all_tables_window()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить таблицу:\n{e}")


# Окно: работа с конкретной таблицей
def open_table_window(table_name):
    win = tk.Toplevel()
    win.title(f"Таблица: {table_name}")

    # Получаем структуру таблицы
    columns = get_table_columns(table_name)
    if not columns:
        messagebox.showerror("Ошибка", f"Не удалось получить структуру таблицы '{table_name}'")
        return

    # Таблица с данными
    tree = ttk.Treeview(win, show="headings", selectmode="browse")
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    tree.pack(padx=10, pady=10)

    load_table_data(tree, table_name)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Обновить", command=lambda: load_table_data(tree, table_name)).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Добавить", command=lambda: add_record_window(table_name, lambda: load_table_data(tree, table_name))).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Редактировать", command=lambda: edit_record_window(table_name, tree, lambda: load_table_data(tree, table_name))).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Удалить", command=lambda: delete_record_window(table_name, tree, lambda: load_table_data(tree, table_name))).pack(side=tk.LEFT, padx=5)


# Добавление записи
def add_record_window(table_name, refresh_callback):
    win = tk.Toplevel()
    win.title(f"Добавить запись в {table_name}")

    entries = {}
    fields = get_table_columns(table_name)

    if not fields:
        return

    form_frame = tk.Frame(win)
    form_frame.pack(padx=10, pady=10)

    for idx, field in enumerate(fields):
        tk.Label(form_frame, text=field).grid(row=idx, column=0, padx=5, pady=5)
        entry = tk.Entry(form_frame, width=30)
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[field] = entry

    def save_record():
        values = []
        columns = []
        for field, entry in entries.items():
            val = entry.get().strip()
            if val:
                columns.append(f"`{field}`")
                if val.isdigit():
                    values.append(val)
                else:
                    values.append(f"'{val}'")

        if not columns:
            messagebox.showwarning("Ошибка", "Заполните хотя бы одно поле")
            return

        sql = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({', '.join(values)})"

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
            db.close()
            messagebox.showinfo("Успех", "Запись добавлена!")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись:\n{e}")

    tk.Button(win, text="Сохранить", command=save_record).pack(pady=10)


# Редактирование записи
def edit_record_window(table_name, tree, refresh_callback):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите строку для редактирования")
        return

    item = tree.item(selected)
    values = item['values']

    win = tk.Toplevel()
    win.title(f"Редактировать запись в {table_name}")

    entries = {}
    fields = get_table_columns(table_name)

    form_frame = tk.Frame(win)
    form_frame.pack(padx=10, pady=10)

    for idx, field in enumerate(fields):
        tk.Label(form_frame, text=field).grid(row=idx, column=0, padx=5, pady=5)
        entry = tk.Entry(form_frame, width=30)
        entry.insert(0, values[idx])
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[field] = entry

    def save_changes():
        updates = []
        where_id = entries['id'].get() if 'id' in entries else ''
        for field, entry in entries.items():
            val = entry.get().strip()
            if field == 'id':
                continue
            if val.isdigit():
                updates.append(f"{field} = {val}")
            else:
                updates.append(f"{field} = '{val}'")

        if not where_id:
            messagebox.showerror("Ошибка", "ID не указан")
            return

        sql = f"UPDATE `{table_name}` SET {', '.join(updates)} WHERE id = {where_id}"

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
            db.close()
            messagebox.showinfo("Успех", "Запись обновлена!")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")

    tk.Button(win, text="Сохранить изменения", command=save_changes).pack(pady=10)


# Удаление записи
def delete_record_window(table_name, tree, refresh_callback):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите строку для удаления")
        return

    item = tree.item(selected)
    values = item['values']
    record_id = values[0]

    confirm = messagebox.askyesno("Подтверждение", f"Удалить запись ID={record_id}?")
    if not confirm:
        return

    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute(f"DELETE FROM `{table_name}` WHERE id = %s", (record_id,))
        db.commit()
        db.close()
        messagebox.showinfo("Успех", "Запись удалена!")
        refresh_callback()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить запись:\n{e}")


# === ГЛАВНОЕ МЕНЮ ===
def create_main_menu():
    root = tk.Tk()
    root.title("Главная")
    root.geometry("300x200")
    root.resizable(False, False)

    tk.Label(root, text="Выберите действие:", font=("Arial", 14)).pack(pady=20)

    tk.Button(root, text="Создать таблицу", width=25, command=create_custom_table_window).pack(pady=5)
    tk.Button(root, text="Показать все таблицы", width=25, command=show_all_tables_window).pack(pady=5)

    root.mainloop()


# Точка входа
if __name__ == "__main__":
    ask_password()
    if db_password:
        create_main_menu()