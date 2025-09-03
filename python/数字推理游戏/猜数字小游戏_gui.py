import tkinter as tk
from tkinter import messagebox
import random

def guess_number(guesslist, answerlist):
    answerlistcopy = answerlist.copy()
    bnumber = 0
    wnumber = 0
    for idx, n in enumerate(guesslist):
        if n == answerlistcopy[idx]:
            bnumber += 1
            guesslist[idx] = -1  # 移除已猜对的数字
            answerlistcopy[idx] = -1 # 移除已猜对的数字
    for  n in guesslist :
        if n in answerlistcopy and n != -1:
            wnumber += 1
    return bnumber, wnumber

class GuessNumberGame:
    def __init__(self, master):
        self.master = master
        master.title("猜数字小游戏")
        master.geometry("400x350")
        self.reset_game()

        self.label = tk.Label(master, text="请输入4个0-9之间的数字（可重复）：")
        self.label.pack(pady=10)

        self.entry = tk.Entry(master, font=("Arial", 16), width=10)
        self.entry.pack()

        self.button = tk.Button(master, text="提交", command=self.check_guess)
        self.button.pack(pady=5)

        self.result_label = tk.Label(master, text="", fg="blue")
        self.result_label.pack(pady=5)

        self.history_label = tk.Label(master, text="历史记录：")
        self.history_label.pack(pady=2)

        self.history_text = tk.Text(master, height=8, width=40, state='disabled')
        self.history_text.pack(pady=2)

        self.restart_button = tk.Button(master, text="重新开始", command=self.reset_game)
        self.restart_button.pack(pady=5)

        self.times_label = tk.Label(master, text="剩余次数：10")
        self.times_label.pack(pady=5)

    def reset_game(self):
        self.answerlist = [random.randint(1, 9) for _ in range(4)]
        #self.answerlist = [2,3,2,8]
        self.times = 10
        if hasattr(self, 'result_label'):
            self.result_label.config(text="")
        if hasattr(self, 'times_label'):
            self.times_label.config(text="剩余次数：10")
        if hasattr(self, 'entry'):
            self.entry.delete(0, tk.END)
        if hasattr(self, 'history_text'):
            self.history_text.config(state='normal')
            self.history_text.delete(1.0, tk.END)
            self.history_text.config(state='disabled')

    def check_guess(self):
        guess = self.entry.get()
        if len(guess) != 4 or not guess.isdigit():
            messagebox.showwarning("输入无效", "请输入4个数字！")
            return
        guesslist = [int(d) for d in guess]
        bnumber, wnumber = guess_number(guesslist, self.answerlist)
        self.times -= 1
        self.times_label.config(text=f"剩余次数：{self.times}")

        # 记录历史
        self.history_text.config(state='normal')
        self.history_text.insert(tk.END, f"{guess}：{bnumber}黑{wnumber}白\n")
        self.history_text.see(tk.END)
        self.history_text.config(state='disabled')

        if bnumber == 4:
            self.result_label.config(text=f"恭喜你，猜对了！答案是：{''.join(map(str, self.answerlist))}")
            messagebox.showinfo("游戏结束", f"恭喜你，猜对了！答案是：{''.join(map(str, self.answerlist))}")
            self.reset_game()
        elif self.times == 0:
            self.result_label.config(text=f"游戏结束！答案是：{''.join(map(str, self.answerlist))}")
            messagebox.showinfo("游戏结束", f"很遗憾，次数用完了！答案是：{''.join(map(str, self.answerlist))}")
            self.reset_game()
        else:
            self.result_label.config(
                text=f" {bnumber} 个黑数；{wnumber} 个白数。"
            )
        self.entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    game = GuessNumberGame(root)
    root.mainloop()