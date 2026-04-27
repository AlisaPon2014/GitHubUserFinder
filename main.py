import json
import os
import tkinter as tk
from tkinter import messagebox
from urllib import error, parse, request


class GitHubUserFinderApp:
    """GUI-приложение для поиска пользователей GitHub и сохранения избранного."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("900x540")

        self.favorites_file = "favorites.json"
        self.search_results = []
        self.favorites = self.load_favorites()

        self.build_ui()
        self.render_favorites()

    def build_ui(self) -> None:
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        title_label = tk.Label(
            top_frame,
            text="GitHub User Finder",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 8))

        search_frame = tk.Frame(top_frame)
        search_frame.pack(fill=tk.X)

        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _event: self.search_users())

        search_button = tk.Button(
            search_frame,
            text="Поиск",
            width=12,
            command=self.search_users
        )
        search_button.pack(side=tk.LEFT)

        middle_frame = tk.Frame(self.root, padx=10, pady=8)
        middle_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.LabelFrame(middle_frame, text="Результаты поиска", padx=8, pady=8)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        right_frame = tk.LabelFrame(middle_frame, text="Избранное", padx=8, pady=8)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self.results_listbox = tk.Listbox(left_frame, font=("Consolas", 10))
        self.results_listbox.pack(fill=tk.BOTH, expand=True)

        left_buttons = tk.Frame(left_frame, pady=8)
        left_buttons.pack(fill=tk.X)

        add_favorite_button = tk.Button(
            left_buttons,
            text="Добавить в избранное",
            command=self.add_to_favorites
        )
        add_favorite_button.pack(side=tk.LEFT)

        self.favorites_listbox = tk.Listbox(right_frame, font=("Consolas", 10))
        self.favorites_listbox.pack(fill=tk.BOTH, expand=True)

        right_buttons = tk.Frame(right_frame, pady=8)
        right_buttons.pack(fill=tk.X)

        remove_button = tk.Button(
            right_buttons,
            text="Удалить из избранного",
            command=self.remove_from_favorites
        )
        remove_button.pack(side=tk.LEFT)

    def search_users(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не должно быть пустым.")
            return

        encoded_query = parse.quote(query)
        url = f"https://api.github.com/search/users?q={encoded_query}&per_page=30"
        req = request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "GitHub-User-Finder-App"
            }
        )

        try:
            with request.urlopen(req, timeout=15) as response:
                payload = response.read().decode("utf-8")
                data = json.loads(payload)
        except error.HTTPError as exc:
            messagebox.showerror("HTTP ошибка", f"GitHub API вернул ошибку: {exc.code}")
            return
        except error.URLError:
            messagebox.showerror("Сетевая ошибка", "Не удалось подключиться к GitHub API.")
            return
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка данных", "Не удалось разобрать ответ GitHub API.")
            return

        self.search_results = data.get("items", [])
        self.render_results()

    def render_results(self) -> None:
        self.results_listbox.delete(0, tk.END)
        for user in self.search_results:
            login = user.get("login", "")
            html_url = user.get("html_url", "")
            self.results_listbox.insert(tk.END, f"{login:<25} {html_url}")

    def add_to_favorites(self) -> None:
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showinfo("Подсказка", "Сначала выберите пользователя в результатах.")
            return

        user = self.search_results[selection[0]]
        login = user.get("login")
        if not login:
            return

        already_added = any(item.get("login") == login for item in self.favorites)
        if already_added:
            messagebox.showinfo("Информация", "Пользователь уже в избранном.")
            return

        favorite_user = {
            "login": login,
            "html_url": user.get("html_url", "")
        }
        self.favorites.append(favorite_user)
        self.save_favorites()
        self.render_favorites()

    def remove_from_favorites(self) -> None:
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showinfo("Подсказка", "Выберите пользователя в избранном для удаления.")
            return

        del self.favorites[selection[0]]
        self.save_favorites()
        self.render_favorites()

    def render_favorites(self) -> None:
        self.favorites_listbox.delete(0, tk.END)
        for user in self.favorites:
            login = user.get("login", "")
            html_url = user.get("html_url", "")
            self.favorites_listbox.insert(tk.END, f"{login:<25} {html_url}")

    def load_favorites(self) -> list:
        if not os.path.exists(self.favorites_file):
            return []

        try:
            with open(self.favorites_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except (OSError, json.JSONDecodeError):
            return []

    def save_favorites(self) -> None:
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as file:
                json.dump(self.favorites, file, ensure_ascii=False, indent=2)
        except OSError:
            messagebox.showerror("Ошибка записи", "Не удалось сохранить избранное в JSON.")


def main() -> None:
    root = tk.Tk()
    app = GitHubUserFinderApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
