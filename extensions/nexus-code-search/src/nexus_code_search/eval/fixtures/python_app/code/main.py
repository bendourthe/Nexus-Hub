from service import make_user, greet_user


def run():
    user = make_user("Alice")
    return greet_user(user)


if __name__ == "__main__":
    run()
