import shutil
import time

# Customize these
MAX_CHARS = 1000  # your "token" or character budget

def draw_usage_bar(current_chars):
    cols = shutil.get_terminal_size().columns
    bar_width = cols - 10  # leave space for label
    usage_ratio = min(current_chars / MAX_CHARS, 1.0)
    filled_len = int(bar_width * usage_ratio)
    empty_len = bar_width - filled_len

    filled = "█" * filled_len
    empty = " " * empty_len
    percent = int(usage_ratio * 100)
    bar = f"[{filled}{empty}] {percent}%"

    # ANSI to move cursor to top and overwrite
    print(f"\033[H{bar}")

def run_chatbot():
    total_chars = 0
    print("\n" * 2)  # Leave space at top for bar
    while True:
        draw_usage_bar(total_chars)
        user_input = input("> ")
        total_chars += len(user_input)
        response = f"Echo: {user_input}"
        total_chars += len(response)
        print(response)
        time.sleep(0.1)  # Just so the print happens after the bar update

if __name__ == "__main__":
    run_chatbot()
