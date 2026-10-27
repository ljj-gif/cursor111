"""FizzBuzz：1 到 100，3 的倍数打 Fizz，5 的倍数打 Buzz，15 的倍数打 FizzBuzz。"""


def fizzbuzz(n: int) -> str:
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)


if __name__ == "__main__":
    for i in range(1, 101):
        print(fizzbuzz(i))
