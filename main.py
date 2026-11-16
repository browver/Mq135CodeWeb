import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)