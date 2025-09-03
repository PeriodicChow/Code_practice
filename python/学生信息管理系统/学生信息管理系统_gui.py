import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import csv

'''# 用字典存储学生信息，key为学号
students_dict = {}

def load_students():
    # 返回所有学生的列表
    return list(students_dict.values())

def save_students(students):
    # 用于兼容原有接口，实际上不做任何操作
    pass
'''
DATA_FILE = "学生信息管理系统.csv"

def load_students():
    students = []
    if not os.path.exists(DATA_FILE):
        return students
    with open(DATA_FILE, "r", encoding="utf-8", newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 4:
                students.append({
                    "id": row[0],
                    "name": row[1],
                    "gender": row[2],
                    "score": float(row[3])
                })
    return students

def save_students(students):
    with open(DATA_FILE, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        for stu in students:
            writer.writerow([stu['id'], stu['name'], stu['gender'], stu['score']])

def grade(score):
    if score < 60:
        return "F"
    elif 60 <= score <= 67:
        return "D"
    elif 68 <= score <= 74:
        return "C"
    elif 75 <= score <= 84:
        return "B"
    else:
        return "A"

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学生信息管理系统")
        self.tree = None
        self.init_main_menu()
        
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def init_main_menu(self):
        self.clear_window()
        btn1 = tk.Button(self.root, text="成绩录入", width=20, command=self.input_student)
        btn2 = tk.Button(self.root, text="成绩显示", width=20, command=self.output_students)
        btn3 = tk.Button(self.root, text="信息查询", width=20, command=self.query_students)
        btn4 = tk.Button(self.root, text="退出", width=20, command=self.root.quit)
        btn1.pack(pady=10)
        btn2.pack(pady=10)
        btn3.pack(pady=10)
        btn4.pack(pady=10)

    def input_student(self):
        
        win = tk.Toplevel(self.root)
        win.title("信息录入")
        tk.Label(win, text="学号:").grid(row=0, column=0)
        tk.Label(win, text="姓名:").grid(row=1, column=0)
        tk.Label(win, text="性别:").grid(row=2, column=0)
        tk.Label(win, text="成绩:").grid(row=3, column=0)
        entry_id = tk.Entry(win)
        entry_name = tk.Entry(win)
        entry_gender = tk.Entry(win)
        entry_score = tk.Entry(win)
        entry_id.grid(row=0, column=1)
        entry_name.grid(row=1, column=1)
        entry_gender.grid(row=2, column=1)
        entry_score.grid(row=3, column=1)

        def save():
            sid = entry_id.get()
            name = entry_name.get()
            gender = entry_gender.get()
            try:
                score = float(entry_score.get())
            except ValueError:
                messagebox.showerror("错误", "成绩必须为数字")
                return
            if not sid or not name or not gender:
                messagebox.showerror("错误", "所有字段都不能为空")
                return
            students = load_students()
            students.append({"id": sid, "name": name, "gender": gender, "score": score})
            save_students(students)
            
            #重置输入
            entry_id.delete(0, tk.END)
            entry_name.delete(0, tk.END)
            entry_gender.delete(0, tk.END)
            entry_score.delete(0, tk.END)
            entry_id.focus_set()
            
        def esc():
            messagebox.showinfo("提示", "信息录入完成！")
            win.destroy()
            self.output_students()
        
        tk.Button(win, text="保存", command=save).grid(row=4, column=0)
        tk.Button(win, text="退出", command=esc).grid(row=4, column=1)

    def output_students(self):
        self.clear_window()
        students = load_students()
        students.sort(key=lambda x: x["score"], reverse=True)
        self.tree = ttk.Treeview(self.root, columns=("学号", "姓名", "性别", "成绩", "等级"), show="headings")
        for col in ("学号", "姓名", "性别", "成绩", "等级"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)
        for stu in students:
            self.tree.insert("", tk.END, values=(stu["id"], stu["name"], stu["gender"], stu["score"], grade(stu["score"])))
        tk.Button(self.root, text="返回", command=self.init_main_menu).pack(pady=10)
        # 排序选项
        sort_var = tk.StringVar(value="score")
        def sort_and_refresh():
            key = sort_var.get()
            students = load_students()
            if key == "id":
                students.sort(key=lambda x: x["id"])
            else:
                students.sort(key=lambda x: x["score"], reverse=True)
            # 清空并重新插入
            for i in self.tree.get_children():
               self.tree.delete(i)
            for stu in students:
                self.tree.insert("", tk.END, values=(stu["id"], stu["name"], stu["gender"], stu["score"], grade(stu["score"])))
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Label(frame, text="排序方式:").pack(side=tk.LEFT)
        tk.Radiobutton(frame, text="按成绩", variable=sort_var, value="score", command=sort_and_refresh).pack(side=tk.LEFT)
        tk.Radiobutton(frame, text="按学号", variable=sort_var, value="id", command=sort_and_refresh).pack(side=tk.LEFT)
        
    def query_students(self):
        win = tk.Toplevel(self.root)
        win.title("信息处理")
        var = tk.IntVar()
        tk.Radiobutton(win, text="按姓名查询", variable=var, value=1).pack(anchor="w")
        tk.Radiobutton(win, text="按学号查询", variable=var, value=2).pack(anchor="w")
        tk.Radiobutton(win, text="按成绩区间查询", variable=var, value=3).pack(anchor="w")

        def do_query():
            qtype = var.get()
            students = load_students()
            result = []
            if qtype == 1:
                name = simpledialog.askstring("查询", "请输入姓名：", parent=win)
                if name:
                    result = [stu for stu in students if stu["name"] == name]
            elif qtype == 2:
                sid = simpledialog.askstring("查询", "请输入学号：", parent=win)
                if sid:
                    result = [stu for stu in students if stu["id"] == sid]
            elif qtype == 3:
                sec = simpledialog.askinteger("查询", "选择成绩区间：1.<60 2.60~69 3.70~79 4.80~89 5.90~100", parent=win)
                if sec == 1:
                    result = [stu for stu in students if stu["score"] < 60]
                elif sec == 2:
                    result = [stu for stu in students if 60 <= stu["score"] <= 69]
                elif sec == 3:
                    result = [stu for stu in students if 70 <= stu["score"] <= 79]
                elif sec == 4:
                    result = [stu for stu in students if 80 <= stu["score"] <= 89]
                elif sec == 5:
                    result = [stu for stu in students if 90 <= stu["score"] <= 100]
            win.destroy()
            self.show_query_result(result)

        tk.Button(win, text="查询", command=do_query).pack()

    def show_query_result(self, result):
        self.clear_window()
        if not result:
            messagebox.showinfo("提示", "未找到符合条件的学生。")
            self.init_main_menu()
            return
        self.tree = ttk.Treeview(self.root, columns=("学号", "姓名", "性别", "成绩", "等级"), show="headings")
        for col in ("学号", "姓名", "性别", "成绩", "等级"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)
        for stu in result:
            self.tree.insert("", tk.END, values=(stu["id"], stu["name"], stu["gender"], stu["score"], grade(stu["score"])))
        def after_ask(ans):
            if ans:
                self.ask_modify_or_delete(result)
            else:
                self.init_main_menu()
        # 弹窗询问
        if messagebox.askyesno("操作", "是否对结果进行删除或修改？"):
            self.ask_modify_or_delete(result)
        else:
            self.init_main_menu()

    def ask_modify_or_delete(self, result):
        sid = simpledialog.askstring("操作", "请输入要操作的学号：")
        if not sid:
            self.init_main_menu()
            return
        op = simpledialog.askinteger("操作", "1.删除 2.修改")
        students = load_students()
        if op == 1:
            students = [stu for stu in students if stu["id"] != sid]
            save_students(students)
            messagebox.showinfo("提示", "删除成功！")
            self.init_main_menu()
        elif op == 2:
            for stu in students:
                if stu["id"] == sid:
                    stu["name"] = simpledialog.askstring("修改", "新姓名：", initialvalue=stu["name"])
                    stu["gender"] = simpledialog.askstring("修改", "新性别：", initialvalue=stu["gender"])
                    try:
                        stu["score"] = float(simpledialog.askstring("修改", "新成绩：", initialvalue=str(stu["score"])))
                    except:
                        messagebox.showerror("错误", "成绩必须为数字")
                        self.init_main_menu()
                        return
                    break
            save_students(students)
            messagebox.showinfo("提示", "修改成功！")
            self.init_main_menu()
        else:
            self.init_main_menu()


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()