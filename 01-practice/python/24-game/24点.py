import random
import itertools

def calc24(nums):
    ops = ['+', '-', '*', '/']
    # 所有排列和运算符组合
    for num_perm in itertools.permutations(nums):
        for ops_perm in itertools.product(ops, repeat=3):
            exp_patterns = [
                f"(({num_perm[0]}{ops_perm[0]}{num_perm[1]}){ops_perm[1]}{num_perm[2]}){ops_perm[2]}{num_perm[3]}",
                f"({num_perm[0]}{ops_perm[0]}({num_perm[1]}{ops_perm[1]}{num_perm[2]})){ops_perm[2]}{num_perm[3]}",
                f"{num_perm[0]}{ops_perm[0]}(({num_perm[1]}{ops_perm[1]}{num_perm[2]}){ops_perm[2]}{num_perm[3]})",
                f"{num_perm[0]}{ops_perm[0]}({num_perm[1]}{ops_perm[1]}({num_perm[2]}{ops_perm[2]}{num_perm[3]}))",
                f"({num_perm[0]}{ops_perm[0]}{num_perm[1]}){ops_perm[1]}({num_perm[2]}{ops_perm[2]}{num_perm[3]})"
            ]
            for exp in exp_patterns:
                try:
                    if abs(eval(exp) - 24) < 1e-6:
                        return exp
                except ZeroDivisionError:
                    continue
    return None

def main():
    print("欢迎来到24点游戏！输入4个1~13之间的数字，用加减乘除得到24。")
    while True:
        nums = [random.randint(1, 13) for _ in range(4)]
        #nums = [2,4,10,10]
        print(f"本轮数字：{nums}")
        user_input = input("请输入你的表达式（或输入'solve'查看答案，输入'q'退出）：")
        if user_input.lower() == 'q':
            print("游戏结束！")
            break
        elif user_input.lower() == 'solve':
            solution = calc24(nums)
            if solution:
                print(f"一种可能的解法：{solution} = 24")
            else:
                print("这组数字无解。")
        else:
            try:
                # 检查用户表达式是否只用了这4个数字
                used_nums = [int(s) for s in user_input if s.isdigit()]
                if sorted(used_nums) != sorted(nums):
                    print("请只使用本轮给出的4个数字！")
                    continue
                if abs(eval(user_input) - 24) < 1e-6:
                    print("恭喜你，答案正确！")
                else:
                    print("答案不正确，再试试吧！")
            except Exception as e:
                print("表达式有误，请重新输入。")

if __name__ == "__main__":
    main()