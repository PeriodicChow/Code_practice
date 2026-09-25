# 猜数字小游戏
import random
def guess_number(guesslist, answerlist):
    bnumber = 0
    wnumber = 0
    for idx, n in enumerate(guesslist):
        if n == answerlist[idx]:
            bnumber += 1
        elif n in answerlist:
            wnumber += 1
    return bnumber,wnumber

# 游戏主函数
def main():
    answerlist = [1,2,3,3]#[random.randint(0, 9) for _ in range(4)]  # 生成4个0-9之间的随机数字
    
    bnumber = 0  # 猜对数字的个数
    wnumber = 0  # 猜对数字但位置不对的个数

    print("欢迎来到猜数字小游戏！")
    print("请猜测4个1-9之间的数字(可能有重复)")
    for times in range(1,11):
        try:
            guess = input(f"第 {times} 次猜测，请输入你的猜测（4个数字）：")
            if len(guess) != 4 or not guess.isdigit() :
                print("输入无效，请确保输入4个不同的数字。")
                continue
            guesslist = [int(digit) for digit in guess]
        except Exception as e:
            print("发生错误：", e)
            continue
        bnumber, wnumber = guess_number(guesslist,answerlist)
        if bnumber == 4:
            print("恭喜你，猜对了！答案是：", ''.join(map(str, answerlist)))
            break
        else:
            print(f"猜对了 {bnumber} 个数字，位置正确；{wnumber} 个数字位置不正确。")
        
    print("游戏结束！")
    print("答案是：", ''.join(map(str, answerlist)))
    


if __name__ == "__main__":
    while True:
        main()