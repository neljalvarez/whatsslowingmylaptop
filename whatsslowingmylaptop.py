import tkinter as tk
from tkinter import ttk
from collections import defaultdict

try:
    import psutil
except ImportError:
    raise SystemExit("Missing dependency. Install it with:  pip install psutil")

REFRESH_MS = 2000  # how often to refresh the list, in milliseconds


def bytes_to_mb(b):
    return b / (1024 * 1024)


class WhatsSlowingMyLaptop:
    def __init__(self, root):
        self.root = root
        self.root.title("What's Slowing My Laptop?")
        self.root.geometry("560x420")

        self.first_seen = {}          # pid -> first rss seen
        self.name_for_pid = {}

        # --- UI ---
        header = tk.Label(
            root,
            text="Live memory usage",
            font=("Segoe UI", 10, "bold"),
            pady=6,
        )
        header.pack(fill="x")

        # Big banner: whatever is using the most RAM right now
        self.top_ram_label = tk.Label(
            root, text="Top RAM user: —", font=("Segoe UI", 12, "bold"),
            fg="#b30000", pady=4,
        )
        self.top_ram_label.pack(fill="x")

        # Sort toggle
        sort_frame = tk.Frame(root)
        sort_frame.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(sort_frame, text="Sort table by:").pack(side="left")
        self.sort_mode = tk.StringVar(value="current")
        ttk.Radiobutton(sort_frame, text="Most RAM right now", value="current",
                        variable=self.sort_mode).pack(side="left", padx=6)
        ttk.Radiobutton(sort_frame, text="Biggest growth (spike)", value="spike",
                        variable=self.sort_mode).pack(side="left", padx=6)

        columns = ("name", "current", "spike")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        self.tree.heading("name", text="App / Process")
        self.tree.heading("current", text="Current MB")
        self.tree.heading("spike", text="Growth (MB)")
        self.tree.column("name", width=260)
        self.tree.column("current", width=110, anchor="e")
        self.tree.column("spike", width=140, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.status = tk.Label(root, text="Starting...", fg="gray", pady=4)
        self.status.pack(fill="x")

        self.refresh()

    def refresh(self):
        rows = []
        for p in psutil.process_iter(attrs=["pid", "name"]):
            try:
                rss = p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            pid = p.pid
            name = p.info["name"] or f"pid-{pid}"
            self.name_for_pid[pid] = name
            if pid not in self.first_seen:
                self.first_seen[pid] = rss
            growth = rss - self.first_seen[pid]
            rows.append((name, rss, growth, pid))

        # Update the "top RAM user right now" banner regardless of sort mode
        if rows:
            top_name, top_rss, _, _ = max(rows, key=lambda r: r[1])
            self.top_ram_label.config(text=f"Top RAM user: {top_name}  ({bytes_to_mb(top_rss):.0f} MB)")

        # Sort by whichever mode is selected
        if self.sort_mode.get() == "spike":
            rows.sort(key=lambda r: r[2], reverse=True)
        else:
            rows.sort(key=lambda r: r[1], reverse=True)

        self.tree.delete(*self.tree.get_children())
        for name, rss, growth, pid in rows[:30]:
            growth_str = f"+{bytes_to_mb(growth):.1f}" if growth > 0 else f"{bytes_to_mb(growth):.1f}"
            self.tree.insert("", "end", values=(name, f"{bytes_to_mb(rss):.1f}", growth_str))

        import time
        self.status.config(text=f"Last updated: {time.strftime('%H:%M:%S')}  |  {len(rows)} processes tracked")

        self.root.after(REFRESH_MS, self.refresh)


def main():
    root = tk.Tk()
    WhatsSlowingMyLaptop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
