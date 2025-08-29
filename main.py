import logging

from estimates import download_all

def main():
    logging.basicConfig(level="INFO")
    download_all()

if __name__ == "__main__":
    main()
