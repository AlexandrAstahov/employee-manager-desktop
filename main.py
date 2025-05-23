import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector


# === Улучшенный ToolTip с кнопкой КОПИРОВАТЬ ===
class SQLTooltip:
    def __init__(self, widget, sql_text):
        self.widget = widget
        self.sql_text = sql_text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.sql_text:
            return
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 10

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes('-topmost', True)

        frame = tk.Frame(tw, background="#ffffe0", borderwidth=1, relief='solid')
        frame.pack()

        label = tk.Label(frame, text="SQL-запрос:", font=("Courier", 9), bg="#ffffe0")
        label.pack(anchor='w', padx=5, pady=2)

        self.sql_label = tk.Text(frame, wrap=tk.WORD, height=4, width=40, font=("Courier", 9))
        self.sql_label.insert(tk.END, self.sql_text)
        self.sql_label.config(state=tk.DISABLED)  # Только для чтения
        self.sql_label.pack(padx=5, pady=2)

        copy_btn = tk.Button(frame, text="Копировать", command=self.copy_sql, width=10)
        copy_btn.pack(pady=5)

        # Добавляем обработчики событий для окна подсказки
        tw.bind("<Enter>", lambda e: self.cancel_hide())
        tw.bind("<Leave>", self.hide_tooltip)
        frame.bind("<Enter>", lambda e: self.cancel_hide())
        frame.bind("<Leave>", self.hide_tooltip)
        self.sql_label.bind("<Enter>", lambda e: self.cancel_hide())
        self.sql_label.bind("<Leave>", self.hide_tooltip)
        copy_btn.bind("<Enter>", lambda e: self.cancel_hide())
        copy_btn.bind("<Leave>", self.hide_tooltip)

        # Добавляем таймер для автоматического скрытия
        self.hide_timer = None

    def cancel_hide(self):
        if self.hide_timer:
            self.widget.after_cancel(self.hide_timer)
            self.hide_timer = None

    def hide_tooltip(self, event=None):
        if self.hide_timer:
            self.widget.after_cancel(self.hide_timer)
        self.hide_timer = self.widget.after(100, self._hide_tooltip)

    def _hide_tooltip(self):
        tw = self.tooltip_window
        if tw:
            tw.destroy()
        self.tooltip_window = None
        self.hide_timer = None

    def copy_sql(self):
        self.tooltip_window.clipboard_clear()
        self.tooltip_window.clipboard_append(self.sql_text)
        self.tooltip_window.update()
        messagebox.showinfo("Скопировано", "Запрос скопирован в буфер обмена")


# === Переменные для хранения настроек подключения ===
db_settings = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # Пароль прописан напрямую
    'database': 'my_db'
}


# === Окно настроек подключения ===
def show_connection_settings():
    win = tk.Toplevel()
    win.title("Настройки подключения")
    win.geometry("400x300")
    win.resizable(False, False)

    # Поля для ввода
    tk.Label(win, text="Хост:").pack(pady=5)
    host_entry = tk.Entry(win, width=30)
    host_entry.insert(0, db_settings['host'])
    host_entry.pack(pady=5)

    tk.Label(win, text="Пользователь:").pack(pady=5)
    user_entry = tk.Entry(win, width=30)
    user_entry.insert(0, db_settings['user'])
    user_entry.pack(pady=5)

    tk.Label(win, text="Пароль:").pack(pady=5)
    password_entry = tk.Entry(win, width=30, show="*")
    if db_settings['password']:
        password_entry.insert(0, db_settings['password'])
    password_entry.pack(pady=5)

    tk.Label(win, text="База данных:").pack(pady=5)
    database_entry = tk.Entry(win, width=30)
    database_entry.insert(0, db_settings['database'])
    database_entry.pack(pady=5)

    def save_settings():
        db_settings['host'] = host_entry.get().strip()
        db_settings['user'] = user_entry.get().strip()
        db_settings['password'] = password_entry.get()
        db_settings['database'] = database_entry.get().strip()

        # Проверяем подключение
        try:
            db = connect_db()
            db.close()
            messagebox.showinfo("Успех", "Подключение успешно установлено!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")

    def test_connection():
        # Сохраняем текущие настройки
        old_settings = db_settings.copy()
        
        # Устанавливаем новые настройки
        db_settings['host'] = host_entry.get().strip()
        db_settings['user'] = user_entry.get().strip()
        db_settings['password'] = password_entry.get()
        db_settings['database'] = database_entry.get().strip()

        try:
            db = connect_db()
            db.close()
            messagebox.showinfo("Успех", "Подключение успешно установлено!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")
            # Восстанавливаем старые настройки
            db_settings.update(old_settings)

    # Кнопки
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=20)

    btn_test = tk.Button(btn_frame, text="Проверить подключение", command=test_connection)
    btn_test.pack(side=tk.LEFT, padx=5)
    btn_test.tooltip = SQLTooltip(btn_test, "Проверяет подключение к базе данных с текущими настройками")

    btn_save = tk.Button(btn_frame, text="Сохранить", command=save_settings)
    btn_save.pack(side=tk.LEFT, padx=5)
    btn_save.tooltip = SQLTooltip(btn_save, "Сохраняет настройки подключения")


# === Подключение к БД ===
def connect_db():
    return mysql.connector.connect(
        host=db_settings['host'],
        user=db_settings['user'],
        password=db_settings['password'],
        database=db_settings['database']
    )


# === СЛУЖЕБНАЯ ТАБЛИЦА metadata ===
def check_metadata_table():
    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_metadata (
                table_name VARCHAR(64) PRIMARY KEY,
                display_name VARCHAR(255) NOT NULL
            )
        """)
        db.commit()
        db.close()
    except Exception as e:
        db.close()
        messagebox.showerror("Ошибка подключения", f"Не удалось создать служебную таблицу:\n{e}")
        exit()


def set_table_display_name(table_name, display_name):
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("REPLACE INTO table_metadata (table_name, display_name) VALUES (%s, %s)",
                       (table_name, display_name))
        db.commit()
    finally:
        db.close()


def get_tables_with_names():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT table_name, display_name FROM table_metadata")
        result = cursor.fetchall()
        return {item['table_name']: item['display_name'] for item in result}
    finally:
        db.close()


def get_tables():
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    finally:
        db.close()


# === Главное меню ===
def create_main_menu():
    root = tk.Tk()
    root.title("Главная")
    root.geometry("300x250")
    root.resizable(False, False)
    tk.Label(root, text="Выберите действие:", font=("Arial", 14)).pack(pady=20)

    def on_create_table():
        create_custom_table_window()

    def on_show_tables():
        show_all_tables_window()

    def on_settings():
        show_connection_settings()

    tk.Button(root, text="Создать таблицу", width=25, command=on_create_table).pack(pady=5)
    tk.Button(root, text="Показать все таблицы", width=25, command=on_show_tables).pack(pady=5)
    tk.Button(root, text="Настройки подключения", width=25, command=on_settings).pack(pady=5)
    root.mainloop()


# === Создание новой таблицы ===
def create_custom_table_window():
    win = tk.Toplevel()
    win.title("Создать новую таблицу")
    win.geometry("600x480")  # уменьшенная высота
    win.minsize(600, 350)

    tk.Label(win, text="Имя таблицы (латиницей):").pack(pady=5)
    entry_table_name = tk.Entry(win, width=40)
    entry_table_name.pack(padx=10, pady=5)

    tk.Label(win, text="Название таблицы (на русском):").pack(pady=5)
    entry_display_name = tk.Entry(win, width=40)
    entry_display_name.pack(padx=10, pady=5)

    # === Прокручиваемая область для полей ===
    canvas_frame = tk.Frame(win)
    canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)
    canvas = tk.Canvas(canvas_frame, borderwidth=0, background=win.cget('bg'), height=220)
    vscroll = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    fields_frame = tk.Frame(canvas, background=win.cget('bg'))

    fields_frame_id = canvas.create_window((0, 0), window=fields_frame, anchor='nw')
    canvas.configure(yscrollcommand=vscroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    fields_frame.bind("<Configure>", on_frame_configure)

    def on_canvas_configure(event):
        canvas.itemconfig(fields_frame_id, width=event.width)
    canvas.bind('<Configure>', on_canvas_configure)

    field_rows = []
    types = ['INT', 'VARCHAR(255)', 'TEXT', 'DATE', 'DATETIME', 'BOOLEAN']
    key_types = ['Нет', 'PRIMARY KEY', 'UNIQUE', 'INDEX']

    def add_field_row():
        row = {}
        frame = tk.Frame(fields_frame)
        frame.pack(anchor='w', pady=5, fill='x')
        # Первая строка: имя, тип, по умолчанию
        name_label = tk.Label(frame, text="Имя поля:")
        name_label.grid(row=0, column=0, padx=2)
        entry_name = tk.Entry(frame, width=12)
        entry_name.grid(row=0, column=1, padx=2)
        type_label = tk.Label(frame, text="Тип:")
        type_label.grid(row=0, column=2, padx=2)
        type_var = tk.StringVar()
        combo_type = ttk.Combobox(frame, textvariable=type_var, values=types, state="readonly", width=12)
        combo_type.set('VARCHAR(255)')
        combo_type.grid(row=0, column=3, padx=2)
        default_var = tk.StringVar()
        tk.Label(frame, text="По умолчанию:").grid(row=0, column=4, padx=2)
        entry_default = tk.Entry(frame, textvariable=default_var, width=10)
        entry_default.grid(row=0, column=5, padx=2)
        entry_default.insert(0, "значение")
        # Вторая строка: чекбоксы и ключ
        not_null_var = tk.BooleanVar()
        unique_var = tk.BooleanVar()
        check_frame = tk.Frame(frame)
        check_frame.grid(row=1, column=0, columnspan=6, sticky='w', pady=2)
        tk.Checkbutton(check_frame, text="NOT NULL", variable=not_null_var).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(check_frame, text="UNIQUE", variable=unique_var).pack(side=tk.LEFT, padx=5)
        tk.Label(check_frame, text="Ключ:").pack(side=tk.LEFT, padx=5)
        key_var = tk.StringVar(value=key_types[0])
        combo_key = ttk.Combobox(check_frame, textvariable=key_var, values=key_types, state="readonly", width=10)
        combo_key.pack(side=tk.LEFT, padx=2)
        row['frame'] = frame
        row['entry_name'] = entry_name
        row['combo_type'] = combo_type
        row['not_null_var'] = not_null_var
        row['unique_var'] = unique_var
        row['default_var'] = default_var
        row['key_var'] = key_var
        field_rows.append(row)
        canvas.yview_moveto(1.0)  # прокрутка вниз при добавлении

    def create_table():
        table_name = entry_table_name.get().strip()
        display_name = entry_display_name.get().strip()
        if not table_name:
            messagebox.showwarning("Ошибка", "Имя таблицы не может быть пустым!")
            return
        if not display_name:
            display_name = table_name

        fields = []
        pk_fields = []
        unique_fields = []
        index_fields = []
        for row in field_rows:
            name = row['entry_name'].get().strip()
            data_type = row['combo_type'].get()
            not_null = row['not_null_var'].get()
            unique = row['unique_var'].get()
            default_value = row['default_var'].get().strip()
            key_type = row['key_var'].get()
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
            # Ключи
            if key_type == 'PRIMARY KEY':
                pk_fields.append(name)
            elif key_type == 'UNIQUE':
                unique_fields.append(name)
            elif key_type == 'INDEX':
                index_fields.append(name)

        if not fields:
            messagebox.showwarning("Ошибка", "Добавьте хотя бы одно поле!")
            return

        # Формируем SQL
        sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ("
        sql += ', '.join(fields)
        constraints = []
        if pk_fields:
            constraints.append(f"PRIMARY KEY ({', '.join([f'`{f}`' for f in pk_fields])})")
        if unique_fields:
            for f in unique_fields:
                constraints.append(f"UNIQUE (`{f}`)")
        if index_fields:
            for f in index_fields:
                constraints.append(f"INDEX (`{f}`)")
        if constraints:
            sql += ', ' + ', '.join(constraints)
        sql += ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
            set_table_display_name(table_name, display_name)
            db.close()
            messagebox.showinfo("Успех", f"Таблица '{table_name}' создана!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать таблицу:\n{e}")

    # === Кнопки в отдельном фрейме ===
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    btn_add = tk.Button(btn_frame, text="Добавить поле", command=add_field_row)
    btn_add.pack(side=tk.LEFT, padx=10)
    btn_add.tooltip = SQLTooltip(btn_add, "Добавляет новое поле в структуру таблицы")

    btn_save = tk.Button(btn_frame, text="Создать таблицу", command=create_table)
    btn_save.pack(side=tk.LEFT, padx=10)
    btn_save.tooltip = SQLTooltip(btn_save, f"CREATE TABLE IF NOT EXISTS `table_name` (field1 type1, field2 type2, ..., id INT PRIMARY KEY AUTO_INCREMENT)")

    SQLTooltip(btn_save, """
        CREATE TABLE IF NOT EXISTS `table_name` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            ...
        ) ENGINE=InnoDB;
    """)

    add_field_row()


# === Показ всех таблиц ===
def show_all_tables_window():
    try:
        tables = get_tables()
        display_names = get_tables_with_names()
    except Exception as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось загрузить таблицы:\n{e}")
        return
    if not tables:
        messagebox.showinfo("Нет таблиц", "В базе пока нет таблиц")
        return

    win = tk.Toplevel()
    win.title("Все таблицы")
    win.geometry("500x300")

    tree = ttk.Treeview(win, columns=("Имя таблицы", "Название"), show="headings")
    tree.heading("Имя таблицы", text="Имя таблицы")
    tree.heading("Название", text="Название")
    tree.column("Имя таблицы", width=150)
    tree.column("Название", width=150)
    tree.pack(padx=10, pady=10)

    for table in tables:
        tree.insert("", tk.END, values=(table, display_names.get(table, table)))

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def update_tooltips(event=None):
        selected = tree.selection()
        table_name = tree.item(selected)['values'][0] if selected else 'table_name'
        btn_open.tooltip.sql_text = f"SELECT * FROM `{table_name}`"
        btn_edit.tooltip.sql_text = f"ALTER TABLE `{table_name}` ..."
        btn_delete.tooltip.sql_text = f"DROP TABLE IF EXISTS `{table_name}`"

    def open_selected_table(tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите таблицу")
            return
        table_name = tree.item(selected)['values'][0]
        open_table_window(table_name)

    def edit_table_structure(tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите таблицу для редактирования")
            return
        table_name = tree.item(selected)['values'][0]
        edit_table_structure_window(table_name)

    def delete_selected_table(tree, window):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите таблицу для удаления")
            return
        table_name = tree.item(selected)['values'][0]
        confirm = messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить таблицу '{table_name}'?")
        if not confirm:
            return
        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            cursor.execute(f"DELETE FROM table_metadata WHERE table_name = '{table_name}'")
            db.commit()
            db.close()
            messagebox.showinfo("Успех", f"Таблица '{table_name}' удалена из БД и метаданных")
            window.destroy()
            show_all_tables_window()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить таблицу:\n{e}")

    # === Кнопки с SQL-подсказками ===
    btn_open = tk.Button(btn_frame, text="Открыть таблицу", command=lambda: open_selected_table(tree))
    btn_open.grid(row=0, column=0, padx=5)
    btn_open.tooltip = SQLTooltip(btn_open, "SELECT * FROM `table_name`")

    btn_edit = tk.Button(btn_frame, text="Редактировать структуру", command=lambda: edit_table_structure(tree))
    btn_edit.grid(row=0, column=1, padx=5)
    btn_edit.tooltip = SQLTooltip(btn_edit, "ALTER TABLE `table_name` ...")

    btn_delete = tk.Button(btn_frame, text="Удалить таблицу", command=lambda: delete_selected_table(tree, win))
    btn_delete.grid(row=0, column=2, padx=5)
    btn_delete.tooltip = SQLTooltip(btn_delete, "DROP TABLE IF EXISTS `table_name`")

    btn_refresh = tk.Button(btn_frame, text="Обновить список", command=lambda: [win.destroy(), show_all_tables_window()])
    btn_refresh.grid(row=0, column=3, padx=5)
    btn_refresh.tooltip = SQLTooltip(btn_refresh, "SHOW TABLES")

    # Привязываем обновление подсказок к выбору элемента в дереве
    tree.bind('<<TreeviewSelect>>', update_tooltips)


# === Открытие конкретной таблицы ===
def open_table_window(table_name):
    win = tk.Toplevel()
    win.title(f"Таблица: {table_name}")
    win.geometry("600x400")

    columns = get_table_columns(table_name)
    if not columns:
        messagebox.showerror("Ошибка", f"Не удалось получить структуру таблицы '{table_name}'")
        return

    tree = ttk.Treeview(win, show="headings", selectmode="browse")
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(padx=10, pady=10)

    load_table_data(tree, table_name)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    btn_refresh = tk.Button(btn_frame, text="Обновить", command=lambda: load_table_data(tree, table_name))
    btn_refresh.pack(side=tk.LEFT, padx=5)
    btn_refresh.tooltip = SQLTooltip(btn_refresh, f"SELECT * FROM `{table_name}`")

    btn_add = tk.Button(btn_frame, text="Добавить запись", command=lambda: add_record_window(table_name, lambda: load_table_data(tree, table_name)))
    btn_add.pack(side=tk.LEFT, padx=5)
    btn_add.tooltip = SQLTooltip(btn_add, f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in columns])}) VALUES ({', '.join(['%s' for _ in columns])})")

    btn_edit = tk.Button(btn_frame, text="Редактировать", command=lambda: edit_record_window(table_name, tree, lambda: load_table_data(tree, table_name)))
    btn_edit.pack(side=tk.LEFT, padx=5)
    btn_edit.tooltip = SQLTooltip(btn_edit, f"UPDATE `{table_name}` SET {', '.join([f'`{col}` = %s' for col in columns if col != 'id'])} WHERE id = %s")

    btn_delete = tk.Button(btn_frame, text="Удалить", command=lambda: delete_record_window(table_name, tree, lambda: load_table_data(tree, table_name)))
    btn_delete.pack(side=tk.LEFT, padx=5)
    btn_delete.tooltip = SQLTooltip(btn_delete, f"DELETE FROM `{table_name}` WHERE id = %s")


# === Загрузка данных таблицы ===
def load_table_data(tree, table_name):
    for item in tree.get_children():
        tree.delete(item)
    try:
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        for row in rows:
            tree.insert("", tk.END, values=[row[col] for col in tree["columns"]])
        db.close()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")


# === Получение столбцов таблицы ===
def get_table_columns(table_name):
    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = [col[0] for col in cursor.fetchall()]
        db.close()
        return columns
    except Exception as e:
        return None


# === Добавление записи ===
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
        tk.Label(form_frame, text=field).grid(row=idx, column=0, padx=5, pady=2)
        entry = tk.Entry(form_frame, width=30)
        entry.grid(row=idx, column=1, padx=5, pady=2)
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
            messagebox.showinfo("Успех", "Запрос выполнен успешно")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить запрос:\n{e}")

    btn_save = tk.Button(win, text="Сохранить", command=save_record)
    btn_save.pack(pady=10)
    btn_save.tooltip = SQLTooltip(btn_save, f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in fields])}) VALUES ({', '.join(['%s' for _ in fields])})")


# === Редактирование записи ===
def edit_record_window(table_name, tree, refresh_callback):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите строку для редактирования")
        return
    item = tree.item(selected)
    values = item['values']
    record_id = values[0]

    win = tk.Toplevel()
    win.title(f"Редактировать запись в {table_name}")
    entries = {}
    fields = get_table_columns(table_name)
    if not fields:
        return

    form_frame = tk.Frame(win)
    form_frame.pack(padx=10, pady=10)
    for idx, field in enumerate(fields):
        tk.Label(form_frame, text=field).grid(row=idx, column=0, padx=5, pady=2)
        entry = tk.Entry(form_frame, width=30)
        entry.insert(0, values[idx])
        entry.grid(row=idx, column=1, padx=5, pady=2)
        entries[field] = entry

    def update_record():
        updates = []
        new_values = []
        for field, entry in entries.items():
            val = entry.get().strip()
            if field == 'id':
                continue
            if val.isdigit():
                updates.append(f"{field} = %s")
                new_values.append(val)
            else:
                updates.append(f"{field} = %s")
                new_values.append(val)
        if not updates:
            messagebox.showwarning("Ошибка", "Ничего не изменено")
            return
        sql = f"UPDATE `{table_name}` SET {', '.join(updates)} WHERE id = {record_id}"
        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(sql, new_values)
            db.commit()
            db.close()
            messagebox.showinfo("Успех", "Запись обновлена!")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")

    btn_save = tk.Button(win, text="Сохранить изменения", command=update_record)
    btn_save.pack(pady=10)
    btn_save.tooltip = SQLTooltip(btn_save, f"UPDATE `{table_name}` SET {', '.join([f'`{col}` = %s' for col in fields if col != 'id'])} WHERE id = {record_id}")


# === Удаление записи ===
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


# === Редактирование структуры таблицы ===
def edit_table_structure_window(table_name):
    win = tk.Toplevel()
    win.title(f"Редактирование структуры таблицы: {table_name}")
    win.geometry("800x600")

    # Получаем текущую структуру таблицы
    try:
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        db.close()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось получить структуру таблицы:\n{e}")
        return

    # Создаем фрейм для списка колонок
    columns_frame = tk.Frame(win)
    columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Создаем Treeview для отображения колонок
    tree = ttk.Treeview(columns_frame, columns=("Field", "Type", "Null", "Key", "Default", "Extra"), show="headings")
    tree.heading("Field", text="Имя поля")
    tree.heading("Type", text="Тип данных")
    tree.heading("Null", text="NULL")
    tree.heading("Key", text="Ключ")
    tree.heading("Default", text="По умолчанию")
    tree.heading("Extra", text="Дополнительно")
    
    # Устанавливаем ширину колонок
    for col in tree["columns"]:
        tree.column(col, width=100)

    # Добавляем скроллбар
    scrollbar = ttk.Scrollbar(columns_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Заполняем дерево данными
    for col in columns:
        tree.insert("", tk.END, values=(
            col['Field'],
            col['Type'],
            col['Null'],
            col['Key'],
            col['Default'] if col['Default'] is not None else '',
            col['Extra']
        ))

    # Фрейм для кнопок
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def update_tooltips(event=None):
        selected = tree.selection()
        column_name = tree.item(selected)['values'][0] if selected else 'column_name'
        btn_edit.tooltip.sql_text = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` ..."
        btn_delete.tooltip.sql_text = f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`"

    def add_column():
        add_column_window(table_name, lambda: refresh_columns())

    def edit_column():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите колонку для редактирования")
            return
        column_name = tree.item(selected)['values'][0]
        edit_column_window(table_name, column_name, lambda: refresh_columns())

    def delete_column():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите колонку для удаления")
            return
        column_name = tree.item(selected)['values'][0]
        if column_name == 'id':
            messagebox.showwarning("Ошибка", "Нельзя удалить колонку id")
            return
        confirm = messagebox.askyesno("Подтверждение", f"Удалить колонку '{column_name}'?")
        if not confirm:
            return
        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`")
            db.commit()
            db.close()
            refresh_columns()
            messagebox.showinfo("Успех", f"Колонка '{column_name}' удалена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить колонку:\n{e}")

    def refresh_columns():
        # Очищаем дерево
        for item in tree.get_children():
            tree.delete(item)
        # Получаем обновленную структуру
        try:
            db = connect_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            db.close()
            # Заполняем дерево новыми данными
            for col in columns:
                tree.insert("", tk.END, values=(
                    col['Field'],
                    col['Type'],
                    col['Null'],
                    col['Key'],
                    col['Default'] if col['Default'] is not None else '',
                    col['Extra']
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить структуру:\n{e}")

    # Кнопки управления с подсказками
    btn_add = tk.Button(btn_frame, text="Добавить колонку", command=add_column)
    btn_add.pack(side=tk.LEFT, padx=5)
    btn_add.tooltip = SQLTooltip(btn_add, f"ALTER TABLE `{table_name}` ADD COLUMN `column_name` type [NOT NULL] [UNIQUE] [DEFAULT value]")

    btn_edit = tk.Button(btn_frame, text="Редактировать колонку", command=edit_column)
    btn_edit.pack(side=tk.LEFT, padx=5)
    btn_edit.tooltip = SQLTooltip(btn_edit, f"ALTER TABLE `{table_name}` MODIFY COLUMN `column_name` ...")

    btn_delete = tk.Button(btn_frame, text="Удалить колонку", command=delete_column)
    btn_delete.pack(side=tk.LEFT, padx=5)
    btn_delete.tooltip = SQLTooltip(btn_delete, f"ALTER TABLE `{table_name}` DROP COLUMN `column_name`")

    btn_refresh = tk.Button(btn_frame, text="Обновить", command=refresh_columns)
    btn_refresh.pack(side=tk.LEFT, padx=5)
    btn_refresh.tooltip = SQLTooltip(btn_refresh, f"DESCRIBE `{table_name}`")

    # Привязываем обновление подсказок к выбору элемента в дереве
    tree.bind('<<TreeviewSelect>>', update_tooltips)

def add_column_window(table_name, refresh_callback):
    win = tk.Toplevel()
    win.title(f"Добавить колонку в {table_name}")
    win.geometry("400x300")

    # Поля для ввода
    tk.Label(win, text="Имя колонки:").pack(pady=5)
    name_entry = tk.Entry(win, width=30)
    name_entry.pack(pady=5)

    tk.Label(win, text="Тип данных:").pack(pady=5)
    type_var = tk.StringVar()
    types = ['INT', 'VARCHAR(255)', 'TEXT', 'DATE', 'DATETIME', 'BOOLEAN']
    type_combo = ttk.Combobox(win, textvariable=type_var, values=types, state="readonly")
    type_combo.set('VARCHAR(255)')
    type_combo.pack(pady=5)

    # Чекбоксы
    not_null_var = tk.BooleanVar()
    tk.Checkbutton(win, text="NOT NULL", variable=not_null_var).pack(pady=5)

    unique_var = tk.BooleanVar()
    tk.Checkbutton(win, text="UNIQUE", variable=unique_var).pack(pady=5)

    # Значение по умолчанию
    tk.Label(win, text="Значение по умолчанию:").pack(pady=5)
    default_entry = tk.Entry(win, width=30)
    default_entry.pack(pady=5)

    def save_column():
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите имя колонки")
            return

        data_type = type_var.get()
        not_null = "NOT NULL" if not_null_var.get() else ""
        unique = "UNIQUE" if unique_var.get() else ""
        default = default_entry.get().strip()
        default_clause = f"DEFAULT '{default}'" if default else ""

        # Формируем SQL запрос
        sql_parts = [f"`{name}` {data_type}"]
        if not_null:
            sql_parts.append(not_null)
        if unique:
            sql_parts.append(unique)
        if default_clause:
            sql_parts.append(default_clause)

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {' '.join(sql_parts)}")
            db.commit()
            db.close()
            messagebox.showinfo("Успех", f"Колонка '{name}' добавлена")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить колонку:\n{e}")

    tk.Button(win, text="Сохранить", command=save_column).pack(pady=10)

def edit_column_window(table_name, column_name, refresh_callback):
    win = tk.Toplevel()
    win.title(f"Редактировать колонку {column_name}")
    win.geometry("400x300")

    # Получаем текущие данные колонки
    try:
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE `{table_name}` `{column_name}`")
        column_data = cursor.fetchone()
        db.close()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось получить данные колонки:\n{e}")
        return

    # Поля для ввода
    tk.Label(win, text="Имя колонки:").pack(pady=5)
    name_entry = tk.Entry(win, width=30)
    name_entry.insert(0, column_name)
    name_entry.pack(pady=5)

    tk.Label(win, text="Тип данных:").pack(pady=5)
    type_var = tk.StringVar()
    types = ['INT', 'VARCHAR(255)', 'TEXT', 'DATE', 'DATETIME', 'BOOLEAN']
    type_combo = ttk.Combobox(win, textvariable=type_var, values=types, state="readonly")
    type_combo.set(column_data['Type'].split('(')[0] if '(' in column_data['Type'] else column_data['Type'])
    type_combo.pack(pady=5)

    # Чекбоксы
    not_null_var = tk.BooleanVar(value=column_data['Null'] == 'NO')
    tk.Checkbutton(win, text="NOT NULL", variable=not_null_var).pack(pady=5)

    unique_var = tk.BooleanVar(value='UNI' in column_data['Key'])
    tk.Checkbutton(win, text="UNIQUE", variable=unique_var).pack(pady=5)

    # Значение по умолчанию
    tk.Label(win, text="Значение по умолчанию:").pack(pady=5)
    default_entry = tk.Entry(win, width=30)
    if column_data['Default'] is not None:
        default_entry.insert(0, column_data['Default'])
    default_entry.pack(pady=5)

    def save_changes():
        new_name = name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("Ошибка", "Введите имя колонки")
            return

        data_type = type_var.get()
        not_null = "NOT NULL" if not_null_var.get() else ""
        unique = "UNIQUE" if unique_var.get() else ""
        default = default_entry.get().strip()
        default_clause = f"DEFAULT '{default}'" if default else ""

        # Формируем SQL запрос
        sql_parts = [f"`{new_name}` {data_type}"]
        if not_null:
            sql_parts.append(not_null)
        if unique:
            sql_parts.append(unique)
        if default_clause:
            sql_parts.append(default_clause)

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(f"ALTER TABLE `{table_name}` CHANGE COLUMN `{column_name}` {' '.join(sql_parts)}")
            db.commit()
            db.close()
            messagebox.showinfo("Успех", f"Колонка '{column_name}' изменена")
            win.destroy()
            refresh_callback()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить колонку:\n{e}")

    tk.Button(win, text="Сохранить изменения", command=save_changes).pack(pady=10)


# === Точка входа ===
if __name__ == "__main__":
    check_metadata_table()
    create_main_menu()