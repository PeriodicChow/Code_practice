from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for a,b in enumerate(nums):
            for c,d in enumerate(nums):
                if a != c and b + d == target:
                    return [a, c]

if __name__ == "__main__":
    s = Solution()
    print(s.twoSum([2,7,11,15], 9))  # Output: [0, 1]