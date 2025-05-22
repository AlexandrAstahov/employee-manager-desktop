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


# === ФУНКЦИИ ДЛЯ СОТРУДНИКОВ ===

# Загрузка сотрудников
def get_employees():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.id, e.full_name, e.mail, e.pass, b.name AS organization 
        FROM employees e
        JOIN branch b ON e.organization_id = b.id
    """)
    employees = cursor.fetchall()
    db.close()
    return employees


# Обновление таблицы сотрудников
def refresh_employee_table(tree):
    for item in tree.get_children():
        tree.delete(item)

    employees = get_employees()
    for emp in employees:
        tree.insert("", tk.END, values=(emp['id'], emp['full_name'], emp['mail'], emp['pass'], emp['organization']))


# Окно просмотра сотрудников
def show_employees_window():
    win = tk.Toplevel()
    win.title("Сотрудники")

    # Таблица
    tree = ttk.Treeview(win, columns=("ID", "Ф.И.О.", "Email", "Пароль", "Организация"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Ф.И.О.", text="Ф.И.О.")
    tree.heading("Email", text="Email")
    tree.heading("Пароль", text="Пароль")
    tree.heading("Организация", text="Организация")

    tree.column("ID", width=50)
    tree.column("Ф.И.О.", width=150)
    tree.column("Email", width=150)
    tree.column("Пароль", width=100)
    tree.column("Организация", width=150)

    employees = get_employees()
    for emp in employees:
        tree.insert("", tk.END, values=(emp['id'], emp['full_name'], emp['mail'], emp['pass'], emp['organization']))

    tree.pack(padx=10, pady=10)

    # Кнопки
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Обновить", command=lambda: refresh_employee_table(tree)).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Добавить", command=lambda: add_employee_window(tree)).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Редактировать", command=lambda: edit_employee(tree)).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Удалить", command=lambda: delete_employee(tree)).grid(row=0, column=3, padx=5)


# Окно добавления сотрудника
def add_employee_window(tree):
    win = tk.Toplevel()
    win.title("Добавить сотрудника")

    orgs = load_organizations()

    tk.Label(win, text="Ф.И.О.:").grid(row=0, column=0, padx=10, pady=5)
    entry_fio = tk.Entry(win, width=30)
    entry_fio.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(win, text="Email:").grid(row=1, column=0, padx=10, pady=5)
    entry_mail = tk.Entry(win, width=30)
    entry_mail.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(win, text="Пароль:").grid(row=2, column=0, padx=10, pady=5)
    entry_pass = tk.Entry(win, show="*", width=30)
    entry_pass.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(win, text="Организация:").grid(row=3, column=0, padx=10, pady=5)
    selected_org = tk.StringVar()
    combo_box = ttk.Combobox(win, textvariable=selected_org, values=[f"{org['id']} - {org['name']}" for org in orgs], state="readonly", width=27)
    combo_box.current(0 if orgs else None)
    combo_box.grid(row=3, column=1, padx=10, pady=5)

    def save_employee():
        full_name = entry_fio.get().strip()
        mail = entry_mail.get().strip()
        password = entry_pass.get().strip()
        organization_id = combo_box.get().split(" - ")[0]

        if not full_name:
            messagebox.showwarning("Ошибка", "Ф.И.О. не может быть пустым!")
            return

        db = connect_db()
        cursor = db.cursor()
        sql = """
            INSERT INTO employees (full_name, mail, pass, organization_id) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (full_name, mail, password, int(organization_id)))
        db.commit()
        db.close()

        messagebox.showinfo("Успех", "Сотрудник добавлен!")
        refresh_employee_table(tree)
        win.destroy()

    tk.Button(win, text="Сохранить", command=save_employee).grid(row=4, column=0, columnspan=2, pady=10)


# Редактирование сотрудника
def edit_employee(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите сотрудника для редактирования!")
        return

    item_data = tree.item(selected_item)
    employee_id = item_data['values'][0]
    full_name = item_data['values'][1]
    mail = item_data['values'][2]
    password = item_data['values'][3]
    organization = item_data['values'][4]

    orgs = load_organizations()
    try:
        org_index = next(i for i, o in enumerate(orgs) if o['name'] == organization)
    except StopIteration:
        messagebox.showerror("Ошибка", "Не найдена организация")
        return

    edit_win = tk.Toplevel()
    edit_win.title("Редактировать сотрудника")

    tk.Label(edit_win, text="Ф.И.О.:").grid(row=0, column=0, padx=10, pady=5)
    entry_fio = tk.Entry(edit_win, width=30)
    entry_fio.insert(0, full_name)
    entry_fio.grid(row=0, column=1)

    tk.Label(edit_win, text="Email:").grid(row=1, column=0, padx=10, pady=5)
    entry_mail = tk.Entry(edit_win, width=30)
    entry_mail.insert(0, mail)
    entry_mail.grid(row=1, column=1)

    tk.Label(edit_win, text="Пароль:").grid(row=2, column=0, padx=10, pady=5)
    entry_pass = tk.Entry(edit_win, show="*", width=30)
    entry_pass.insert(0, password)
    entry_pass.grid(row=2, column=1)

    selected_org = tk.StringVar()
    org_options = [f"{org['id']} - {org['name']}" for org in orgs]
    combo_box = ttk.Combobox(edit_win, textvariable=selected_org, values=org_options, state="readonly", width=27)
    combo_box.current(org_index)
    combo_box.grid(row=3, column=1, padx=10, pady=5)

    def save_changes():
        updated_full_name = entry_fio.get().strip()
        updated_mail = entry_mail.get().strip()
        updated_password = entry_pass.get().strip()
        updated_org_id = combo_box.get().split(" - ")[0]

        if not updated_full_name:
            messagebox.showwarning("Ошибка", "Ф.И.О. не может быть пустым!")
            return

        db = connect_db()
        cursor = db.cursor()
        sql = """
            UPDATE employees 
            SET full_name = %s, mail = %s, pass = %s, organization_id = %s 
            WHERE id = %s
        """
        cursor.execute(sql, (updated_full_name, updated_mail, updated_password, int(updated_org_id), employee_id))
        db.commit()
        db.close()

        messagebox.showinfo("Успех", "Данные сотрудника обновлены!")
        refresh_employee_table(tree)
        edit_win.destroy()

    tk.Button(edit_win, text="Сохранить изменения", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)


# Удаление сотрудника
def delete_employee(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите сотрудника для удаления!")
        return

    item_data = tree.item(selected_item)
    employee_id = item_data['values'][0]

    confirm = messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить сотрудника ID={employee_id}?")
    if not confirm:
        return

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
    db.commit()
    db.close()

    messagebox.showinfo("Успех", "Сотрудник удален!")
    refresh_employee_table(tree)


# === ФУНКЦИИ ДЛЯ ОРГАНИЗАЦИЙ ===

# Окно просмотра организаций
def show_organizations_window():
    win = tk.Toplevel()
    win.title("Организации")

    tk.Label(win, text="Список организаций:").pack(pady=5)

    listbox = tk.Listbox(win, width=50, height=10)
    listbox.pack(padx=10, pady=5)

    refresh_organization_list(listbox)

    tk.Label(win, text="Добавить новую организацию:").pack(pady=5)
    new_org_entry = tk.Entry(win, width=30)
    new_org_entry.pack(padx=10, pady=5)

    def add_and_refresh():
        name = new_org_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Название организации не может быть пустым!")
            return

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO branch (name) VALUES (%s)", (name,))
        db.commit()
        db.close()

        new_org_entry.delete(0, tk.END)
        refresh_organization_list(listbox)

    tk.Button(win, text="Добавить организацию", command=add_and_refresh).pack(pady=5)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Обновить", command=lambda: refresh_organization_list(listbox)).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Редактировать", command=lambda: edit_organization(listbox)).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Удалить", command=lambda: delete_organization(listbox)).pack(side=tk.LEFT, padx=5)


# Обновление списка организаций
def refresh_organization_list(listbox):
    listbox.delete(0, tk.END)
    orgs = load_organizations()
    for org in orgs:
        listbox.insert(tk.END, f"{org['id']} - {org['name']}")


# Загрузка организаций
def load_organizations():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM branch")
    organizations = cursor.fetchall()
    db.close()
    return organizations


# Редактирование организации
def edit_organization(listbox):
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите организацию для редактирования!")
        return

    org_info = listbox.get(selected[0])
    org_id, name = org_info.split(" - ", 1)

    edit_win = tk.Toplevel()
    edit_win.title("Редактировать организацию")

    tk.Label(edit_win, text="Название организации:").pack(pady=5)
    entry_name = tk.Entry(edit_win, width=30)
    entry_name.insert(0, name)
    entry_name.pack(padx=10, pady=5)

    def save_changes():
        new_name = entry_name.get().strip()
        if not new_name:
            messagebox.showwarning("Ошибка", "Название не может быть пустым!")
            return

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("UPDATE branch SET name = %s WHERE id = %s", (new_name, int(org_id)))
        db.commit()
        db.close()

        messagebox.showinfo("Успех", "Название организации изменено!")
        refresh_organization_list(listbox)
        edit_win.destroy()

    tk.Button(edit_win, text="Сохранить", command=save_changes).pack(pady=10)


# Удаление организации
def delete_organization(listbox):
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите организацию для удаления!")
        return

    org_info = listbox.get(selected[0])
    org_id = org_info.split(" - ", 1)[0]

    confirm = messagebox.askyesno("Подтверждение", f"Удалить организацию ID={org_id}?")
    if not confirm:
        return

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM branch WHERE id = %s", (int(org_id),))
    db.commit()
    db.close()

    messagebox.showinfo("Успех", "Организация удалена!")
    refresh_organization_list(listbox)


# === ГЛАВНОЕ МЕНЮ ===
def create_main_menu():
    root = tk.Tk()
    root.title("Главная")
    root.geometry("300x150")
    root.resizable(False, False)

    tk.Label(root, text="Выберите действие:", font=("Arial", 14)).pack(pady=20)

    tk.Button(root, text="Посмотреть сотрудников", width=25, command=show_employees_window).pack(pady=5)
    tk.Button(root, text="Посмотреть организации", width=25, command=show_organizations_window).pack(pady=5)

    root.mainloop()


# Точка входа
if __name__ == "__main__":
    ask_password()
    if db_password:
        create_main_menu()