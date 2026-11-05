list_num = [8, 8, 7, 6, 4, 5, 4, 53, 32]
for i in range(len(list_num)):
    if i == list_num[i] == 4:
        index = i
        break
del list_num[:index]
print(list_num)
