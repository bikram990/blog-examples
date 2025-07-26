"""main"""

import requests


def main():
    """main"""
    print("Hello from 2025-07-06-dev-containers!")
    response = requests.get(url="https://google.com", timeout=30)
    print(f"Response is {response.text}")


if __name__ == "__main__":
    main()
