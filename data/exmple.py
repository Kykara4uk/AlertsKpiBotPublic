a = int(input('enter first number: '))
b = int(input('enter second number: '))
result = 1
n = int(input("1. Сложение: \n"
           "2. Вычетание: \n"
           "3. Умножение: \n"))

if n == 1:
    result = a + b
elif n == 2:
    result = a - b
elif n == 3:
    result = a * b

print(f'Result = {result}')
