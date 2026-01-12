n = int(input("Entrez un nombre: "))
toto = True
for i in range(2, n):
    toto = True
    for j in range(2, i-1):
        if i % j == 0:
            toto = False
            break
    if toto:
        print(i)