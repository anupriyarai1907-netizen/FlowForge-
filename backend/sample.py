
def get_user():
    name = input("Enter name: ")
    return name

def save_user(name):
    print("Saving user:", name)

def main():
    user = get_user()
    save_user(user)

main()
