from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


class MdMergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown 合并器")
        self.root.geometry("720x480")

        self.files = []
        self.allowed_suffixes = {".md", ".markdown", ".txt"}

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="文本合并器：选择多个 .md / .markdown / .txt 文件，按列表顺序合并为一个文件",
            font=("Microsoft YaHei UI", 11, "bold")
        )
        title.pack(pady=(10, 5))

        hint = tk.Label(
            self.root,
            text="提示：列表中的顺序就是合并顺序。可用“上移 / 下移”调整。",
            anchor="w"
        )
        hint.pack(fill="x", padx=10)

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.listbox = tk.Listbox(
            frame,
            selectmode=tk.EXTENDED,
            font=("Consolas", 10)
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(button_frame, text="添加文件", command=self.add_files).pack(side="left", padx=3)
        tk.Button(button_frame, text="上移", command=self.move_up).pack(side="left", padx=3)
        tk.Button(button_frame, text="下移", command=self.move_down).pack(side="left", padx=3)
        tk.Button(button_frame, text="删除选中", command=self.remove_selected).pack(side="left", padx=3)
        tk.Button(button_frame, text="清空列表", command=self.clear_files).pack(side="left", padx=3)

        option_frame = tk.Frame(self.root)
        option_frame.pack(fill="x", padx=10, pady=5)

        self.use_separator = tk.BooleanVar(value=True)
        tk.Checkbutton(
            option_frame,
            text="文件之间加入 Markdown 分割线：---",
            variable=self.use_separator
        ).pack(side="left")

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            bottom_frame,
            text="开始合并并另存为...",
            command=self.merge_and_save,
            height=2,
            font=("Microsoft YaHei UI", 10, "bold")
        ).pack(side="right")

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for path in self.files:
            self.listbox.insert(tk.END, path.name)

    def add_files(self):
        selected = filedialog.askopenfilenames(
            title="选择文本文件",
            filetypes=[
                ("文本文件", "*.md *.markdown *.txt"),
                ("Markdown 文件", "*.md *.markdown"),
                ("TXT 文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        if not selected:
            return

        existing = {str(p.resolve()).lower() for p in self.files}

        added = 0
        skipped = 0

        for file in selected:
            path = Path(file).resolve()

            if path.suffix.lower() not in self.allowed_suffixes:
                skipped += 1
                continue

            key = str(path).lower()

            if key in existing:
                skipped += 1
                continue

            self.files.append(path)
            existing.add(key)
            added += 1

        self.refresh_listbox()

        if added == 0 and skipped > 0:
            messagebox.showinfo("提示", "没有新增支持的文本文件，可能是文件类型不符或已经在列表中。")

    def selected_indices(self):
        return list(self.listbox.curselection())

    def move_up(self):
        indices = self.selected_indices()

        if not indices or indices[0] == 0:
            return

        for i in indices:
            self.files[i - 1], self.files[i] = self.files[i], self.files[i - 1]

        self.refresh_listbox()

        for i in indices:
            self.listbox.selection_set(i - 1)

    def move_down(self):
        indices = self.selected_indices()

        if not indices or indices[-1] == len(self.files) - 1:
            return

        for i in reversed(indices):
            self.files[i + 1], self.files[i] = self.files[i], self.files[i + 1]

        self.refresh_listbox()

        for i in indices:
            self.listbox.selection_set(i + 1)

    def remove_selected(self):
        indices = self.selected_indices()

        if not indices:
            return

        for i in reversed(indices):
            del self.files[i]

        self.refresh_listbox()

    def clear_files(self):
        self.files.clear()
        self.refresh_listbox()

    def read_text_safely(self, path):
        for enc in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(
            "unknown",
            b"",
            0,
            1,
            f"无法识别文件编码：{path}"
        )

    def merge_and_save(self):
        if len(self.files) < 2:
            messagebox.showwarning("文件不足", "至少需要添加 2 个文本文件。")
            return

        output_file = filedialog.asksaveasfilename(
            title="保存合并后的 Markdown 文件",
            defaultextension=".md",
            filetypes=[
                ("Markdown 文件", "*.md"),
                ("TXT 文件", "*.txt"),
                ("所有文件", "*.*")
            ],
            initialfile="合并版.md"
        )

        if not output_file:
            return

        output_path = Path(output_file).resolve()

        input_paths = {str(p.resolve()).lower() for p in self.files}

        if str(output_path).lower() in input_paths:
            messagebox.showerror(
                "输出文件错误",
                "输出文件不能和输入文件相同，否则会覆盖原文。"
            )
            return

        if output_path.exists():
            confirm = messagebox.askyesno(
                "确认覆盖",
                f"输出文件已存在，是否覆盖？\n\n{output_path}"
            )

            if not confirm:
                return

        sep = "\n\n---\n\n" if self.use_separator.get() else "\n\n"

        try:
            parts = []

            for path in self.files:
                if not path.exists():
                    raise FileNotFoundError(f"文件不存在：{path}")

                text = self.read_text_safely(path)
                parts.append(text.rstrip())

            merged = sep.join(parts).rstrip() + "\n"

            output_path.write_text(merged, encoding="utf-8", newline="\n")

        except Exception as e:
            messagebox.showerror("合并失败", str(e))
            return

        order_text = "\n".join(path.name for path in self.files)

        messagebox.showinfo(
            "合并完成",
            f"已合并 {len(self.files)} 个文件。\n\n"
            f"输出文件：\n{output_path}\n\n"
            f"合并顺序：\n{order_text}"
        )


def main():
    root = tk.Tk()
    app = MdMergeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()