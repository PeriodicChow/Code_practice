import os
import csv

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

def input_student():
    students = load_students()
    while True:
        sid = input("请输入学号（输入0结束）：")
        if sid == "0":
            break
        name = input("请输入姓名：")
        gender = input("请输入性别：")
        score = input("请输入成绩：")
        students.append({"id": sid, "name": name, "gender": gender, "score": float(score)})
    save_students(students)
    print("信息录入完成！")

def output_students():
    students = load_students()
    students.sort(key=lambda x: x["score"], reverse=True)
    print("学号\t姓名\t性别\t成绩")
    for stu in students:
        print(f"{stu['id']}\t{stu['name']}\t{stu['gender']}\t{stu['score']}")

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

def query_students():
    students = load_students()
    print("1. 按姓名查询  2. 按学号查询  3. 按成绩区间查询")
    choice = input("请选择查询方式：")
    result = []
    if choice == "1":
        name = input("请输入姓名：")
        result = [stu for stu in students if stu["name"] == name]
    elif choice == "2":
        sid = input("请输入学号：")
        result = [stu for stu in students if stu["id"] == sid]
    elif choice == "3":
        print("1.<60  2.60~69  3.70~79  4.80~89  5.90~100")
        sec = input("请选择成绩区间：")
        if sec == "1":
            result = [stu for stu in students if stu["score"] < 60]
        elif sec == "2":
            result = [stu for stu in students if 60 <= stu["score"] <= 69]
        elif sec == "3":
            result = [stu for stu in students if 70 <= stu["score"] <= 79]
        elif sec == "4":
            result = [stu for stu in students if 80 <= stu["score"] <= 89]
        elif sec == "5":
            result = [stu for stu in students if 90 <= stu["score"] <= 100]
    else:
        print("无效选择")
        return

    if not result:
        print("未找到符合条件的学生。")
        return

    print("学号\t姓名\t性别\t成绩\t等级")
    for stu in result:
        print(f"{stu['id']}\t{stu['name']}\t{stu['gender']}\t{stu['score']}\t{grade(stu['score'])}")

    # 允许用户删除或修改
    print("1. 删除学生  2. 修改学生  0. 返回")
    op = input("请选择操作：")
    if op == "1":
        sid = input("请输入要删除的学号：")
        students = [stu for stu in students if stu["id"] != sid]
        save_students(students)
        print("删除成功！")
    elif op == "2":
        sid = input("请输入要修改的学号：")
        for stu in students:
            if stu["id"] == sid:
                stu["name"] = input("新姓名：")
                stu["gender"] = input("新性别：")
                stu["score"] = float(input("新成绩："))
                break
        save_students(students)
        print("修改成功！")

def main():
    while True:
        print("\n学生信息管理系统")
        print("1. 信息录入")
        print("2. 信息输出")
        print("3. 信息处理")
        print("0. 退出系统")
        choice = input("请选择菜单：")
        if choice == "1":
            input_student()
        elif choice == "2":
            output_students()
        elif choice == "3":
            query_students()
        elif choice == "0":
            print("退出系统。")
            break
        else:
            print("无效选择，请重新输入。")

if __name__ == "__main__":
    main()