import textwrap
text = "Hello World!"
result = textwrap.wrap(text, 9)

for word in result:
    for letter in word:
        print(letter)
    print("newline")

# print(result)