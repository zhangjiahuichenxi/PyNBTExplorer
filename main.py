import ttkbootstrap as ttk
from tkinter import filedialog, messagebox, simpledialog
import nbtlib
from nbtlib.tag import Int, String, Float, Compound, List, Byte, Short, Long, Double, ByteArray, IntArray, LongArray
import platform
import subprocess
import os
import config
import re


class NBTExplorer:
    def __init__(self, filepath=""):
        self.root = ttk.Window(themename=config.theme)
        self.root.title("PyNBTExplorer")
        self.root.geometry("1000x700")

        try:
            icon_img = ttk.PhotoImage(file="./icon.png")
            self.root.iconphoto(False, icon_img)
        except:
            pass

        self.node_paths = {}
        self.node_values = {}

        self.search_results = []
        self.current_search_index = -1

        self.create_menu()

        self.create_toolbar()

        self.status_var = ttk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.search_frame = ttk.Frame(self.root, relief="raised")
        self.search_frame.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Label(self.search_frame, text="查找:").pack(side="left", padx=(5, 2))
        self.search_entry = ttk.Entry(self.search_frame, width=30)
        self.search_entry.pack(side="left", padx=2)
        self.search_entry.bind("<Return>", lambda e: self.find_next())

        self.search_btn = ttk.Button(self.search_frame, text="查找", command=self.find_next)
        self.search_btn.pack(side="left", padx=2)

        self.prev_btn = ttk.Button(self.search_frame, text="上一个", command=self.find_prev)
        self.prev_btn.pack(side="left", padx=2)

        self.next_btn = ttk.Button(self.search_frame, text="下一个", command=self.find_next)
        self.next_btn.pack(side="left", padx=2)

        ttk.Label(self.search_frame, text="|").pack(side="left", padx=5)

        self.case_sensitive_var = ttk.BooleanVar()
        self.case_chk = ttk.Checkbutton(self.search_frame, text="区分大小写", variable=self.case_sensitive_var)
        self.case_chk.pack(side="left", padx=2)

        self.regex_var = ttk.BooleanVar()
        self.regex_chk = ttk.Checkbutton(self.search_frame, text="正则表达式", variable=self.regex_var)
        self.regex_chk.pack(side="left", padx=2)

        self.paned_window = ttk.PanedWindow(self.root, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)

        self.tree_frame = ttk.Frame(self.paned_window)
        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame)
        self.tree_scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(self.tree_frame, columns=("type", "value"),
                                 yscrollcommand=self.tree_scrollbar.set,
                                 selectmode="browse")
        self.tree_scrollbar.config(command=self.tree.yview)
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("#0", text="名称")
        self.tree.heading("type", text="类型")
        self.tree.heading("value", text="值")
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("value", width=150, minwidth=100)

        self.detail_frame = ttk.Frame(self.paned_window)
        self.detail_label = ttk.Label(self.detail_frame, text="详细信息", font=("Arial", 10, "bold"))
        self.detail_label.pack(pady=5)

        self.detail_text = ttk.Text(self.detail_frame, wrap="word", state="disabled")
        self.detail_scrollbar = ttk.Scrollbar(self.detail_frame, command=self.detail_text.yview)
        self.detail_text.config(yscrollcommand=self.detail_scrollbar.set)

        self.detail_scrollbar.pack(side="right", fill="y")
        self.detail_text.pack(fill="both", expand=True)

        self.paned_window.add(self.tree_frame)
        self.paned_window.add(self.detail_frame)

        self.file_path = ""
        self.level = None

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        if filepath and os.path.exists(filepath):
            self.open_file(filepath)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def create_menu(self):
        self.menu = ttk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.menu_file = ttk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="文件(F)", menu=self.menu_file)

        self.menu_file.add_command(label="打开(O)", command=self.open_file_dialog, accelerator="Ctrl+O")
        self.menu_file.add_command(label="保存(S)", command=self.save_file, accelerator="Ctrl+S", state="disabled")
        self.menu_file.add_command(label="另存为(A)", command=self.save_file_as, accelerator="Ctrl+Shift+S",
                                   state="disabled")
        self.menu_file.add_command(label="设置",command=lambda:os.system("python3 setting.py"))
        self.menu_file.add_separator()
        self.menu_file.add_command(label="退出(X)", command=self.on_closing, accelerator="Alt+F4")

        self.menu_edit = ttk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="编辑(E)", menu=self.menu_edit)

        self.menu_edit.add_command(label="编辑节点(E)", command=self.edit_node, accelerator="Enter", state="disabled")
        self.menu_edit.add_command(label="添加节点(A)", command=self.add_node, accelerator="Ctrl+N", state="disabled")
        self.menu_edit.add_command(label="删除节点(D)", command=self.delete_node, accelerator="Delete",
                                   state="disabled")

        self.menu_view = ttk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="视图(V)", menu=self.menu_view)

        self.menu_view.add_command(label="刷新(R)", command=self.refresh_view, accelerator="F5")

        self.menu_tools = ttk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="工具(T)", menu=self.menu_tools)

        self.menu_tools.add_command(label="查找(F)", command=self.focus_search, accelerator="Ctrl+F")

        self.menu_help = ttk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="帮助(H)", menu=self.menu_help)

        self.menu_help.add_command(label="关于 PyNBTExplorer", command=self.show_about)

        self.root.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind("<F5>", lambda e: self.refresh_view())
        self.root.bind("<Return>", lambda e: self.edit_node())
        self.root.bind("<Delete>", lambda e: self.delete_node())
        self.root.bind("<Control-f>", lambda e: self.focus_search())

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.root, relief="ridge")
        self.toolbar.pack(side="top", fill="x")

        self.btn_open = ttk.Button(self.toolbar, text="打开", command=self.open_file_dialog)
        self.btn_open.pack(side="left", padx=2, pady=2)

        self.btn_save = ttk.Button(self.toolbar, text="保存", command=self.save_file, state=ttk.DISABLED)
        self.btn_save.pack(side="left", padx=2, pady=2)

        self.btn_refresh = ttk.Button(self.toolbar, text="刷新", command=self.refresh_view)
        self.btn_refresh.pack(side="left", padx=2, pady=2)

        ttk.Label(self.toolbar, text="|").pack(side="left", padx=5)

        self.btn_edit = ttk.Button(self.toolbar, text="编辑", command=self.edit_node, state=ttk.DISABLED)
        self.btn_edit.pack(side="left", padx=2, pady=2)

        self.btn_add = ttk.Button(self.toolbar, text="添加", command=self.add_node, state=ttk.DISABLED)
        self.btn_add.pack(side="left", padx=2, pady=2)

        self.btn_delete = ttk.Button(self.toolbar, text="删除", command=self.delete_node, state=ttk.DISABLED)
        self.btn_delete.pack(side="left", padx=2, pady=2)

        ttk.Label(self.toolbar, text="|").pack(side="left", padx=5)

        self.btn_find = ttk.Button(self.toolbar, text="查找", command=self.focus_search)
        self.btn_find.pack(side="left", padx=2, pady=2)

    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, ttk.END)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("NBT Files", "*.nbt"), ("DAT Files", "*.dat"), ("All Files", "*.*")]
        )
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path):
        try:
            self.level = nbtlib.load(file_path)
            self.file_path = file_path
            self.update_tree()
            self.update_status(f"已打开: {file_path}")
            self.enable_edit_controls(True)
        except Exception as e:
            messagebox.showerror("打开文件错误", f"无法打开文件: {str(e)}")

    def save_file(self):
        if not self.file_path:
            self.save_file_as()
            return

        try:
            self.level.save(self.file_path)
            self.update_status(f"已保存: {self.file_path}")
            messagebox.showinfo("保存成功", "文件保存成功！")
        except Exception as e:
            messagebox.showerror("保存文件错误", f"无法保存文件: {str(e)}")

    def save_file_as(self):
        if not self.level:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("NBT Files", "*.nbt"), ("DAT Files", "*.dat"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path = file_path
            self.save_file()

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.node_paths = {}
        self.node_values = {}

        if self.level:
            root_tag = self.level.root if hasattr(self.level, 'root') else self.level
            root_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
            root_id = self.tree.insert("", "end", text=root_name, values=("Compound", ""), open=True)
            self.node_paths[root_id] = []
            self.populate_tree(root_id, root_tag)

    def populate_tree(self, parent_id, tag):
        if isinstance(tag, Compound):
            for key, value in tag.items():
                if isinstance(value, Compound):
                    count = len(value)
                    child_id = self.tree.insert(parent_id, "end", text=key, values=("Compound", f"{count} 项"))
                    self.node_paths[child_id] = self.node_paths[parent_id] + [key]
                    self.populate_tree(child_id, value)
                elif isinstance(value, List):
                    list_type = value.subtype.__name__ if value.subtype else "Unknown"
                    child_id = self.tree.insert(parent_id, "end", text=key,
                                                values=(f"List[{list_type}]", f"{len(value)} 项"))
                    self.node_paths[child_id] = self.node_paths[parent_id] + [key]
                    for i, item in enumerate(value):
                        self.populate_list(child_id, i, item)
                else:
                    value_str = self.get_value_string(value)
                    child_id = self.tree.insert(parent_id, "end", text=key,
                                                values=(self.get_type_name(value), value_str))
                    self.node_paths[child_id] = self.node_paths[parent_id] + [key]
                    self.node_values[child_id] = value

        elif isinstance(tag, List):
            for i, item in enumerate(tag):
                self.populate_list(parent_id, i, item)

    def populate_list(self, parent_id, index, item):
        if isinstance(item, Compound):
            count = len(item)
            child_id = self.tree.insert(parent_id, "end", text=f"[{index}]", values=("Compound", f"{count} 项"))
            self.node_paths[child_id] = self.node_paths[parent_id] + [index]
            self.populate_tree(child_id, item)
        elif isinstance(item, List):
            list_type = item.subtype.__name__ if item.subtype else "Unknown"
            child_id = self.tree.insert(parent_id, "end", text=f"[{index}]",
                                        values=(f"List[{list_type}]", f"{len(item)} 项"))
            self.node_paths[child_id] = self.node_paths[parent_id] + [index]
            for j, subitem in enumerate(item):
                self.populate_list(child_id, j, subitem)
        else:
            value_str = self.get_value_string(item)
            child_id = self.tree.insert(parent_id, "end", text=f"[{index}]",
                                        values=(self.get_type_name(item), value_str))
            self.node_paths[child_id] = self.node_paths[parent_id] + [index]
            self.node_values[child_id] = item

    def get_type_name(self, tag):
        if isinstance(tag, Int):
            return "Int"
        elif isinstance(tag, String):
            return "String"
        elif isinstance(tag, Float):
            return "Float"
        elif isinstance(tag, Double):
            return "Double"
        elif isinstance(tag, Byte):
            return "Byte"
        elif isinstance(tag, Short):
            return "Short"
        elif isinstance(tag, Long):
            return "Long"
        elif isinstance(tag, ByteArray):
            return "ByteArray"
        elif isinstance(tag, IntArray):
            return "IntArray"
        elif isinstance(tag, LongArray):
            return "LongArray"
        return type(tag).__name__

    def get_value_string(self, tag):
        if isinstance(tag, (Int, Byte, Short, Long)):
            return str(tag)
        elif isinstance(tag, (Float, Double)):
            return f"{tag:.6f}"
        elif isinstance(tag, String):
            return f'"{tag}"'
        elif isinstance(tag, ByteArray):
            return f"ByteArray[{len(tag)}]"
        elif isinstance(tag, IntArray):
            return f"IntArray[{len(tag)}]"
        elif isinstance(tag, LongArray):
            return f"LongArray[{len(tag)}]"
        return str(tag)

    def on_tree_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_text = self.tree.item(selected_item, "text")
        item_values = self.tree.item(selected_item, "values")

        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, ttk.END)
        self.detail_text.insert(ttk.END, f"名称: {item_text}\n")
        self.detail_text.insert(ttk.END, f"类型: {item_values[0]}\n")

        if len(item_values) > 1 and item_values[1]:
            self.detail_text.insert(ttk.END, f"值: {item_values[1]}\n")

        self.detail_text.insert(ttk.END, "\n路径: " + self.get_item_path(selected_item))

        if selected_item in self.node_values:
            value = self.node_values[selected_item]
            self.detail_text.insert(ttk.END, f"\n原始值: {value!r}")

        self.detail_text.config(state="disabled")

        self.enable_edit_controls(True)

    def get_item_path(self, item):
        path = []
        while item:
            item_text = self.tree.item(item, "text")
            path.insert(0, item_text)
            item = self.tree.parent(item)
        return "/".join(path)

    def on_tree_double_click(self, event):
        self.edit_node()

    def edit_node(self):
        selected_item = self.tree.focus()
        if not selected_item or selected_item not in self.node_values:
            return

        item_text = self.tree.item(selected_item, "text")
        item_values = self.tree.item(selected_item, "values")
        item_type = item_values[0] if item_values else ""

        original_value = self.node_values[selected_item]
        original_value_str = self.get_value_string(original_value)

        edit_win = ttk.Toplevel(self.root)
        edit_win.title("编辑节点")
        edit_win.geometry("400x250")
        edit_win.transient(self.root)
        edit_win.grab_set()

        name_frame = ttk.Frame(edit_win)
        name_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(name_frame, text="名称:").pack(side="left")
        name_var = ttk.StringVar(value=item_text)
        name_entry = ttk.Entry(name_frame, textvariable=name_var, state="readonly")
        name_entry.pack(side="left", fill="x", expand=True, padx=5)

        type_frame = ttk.Frame(edit_win)
        type_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(type_frame, text="类型:").pack(side="left")
        type_var = ttk.StringVar(value=item_type)
        type_entry = ttk.Entry(type_frame, textvariable=type_var, state="readonly")
        type_entry.pack(side="left", fill="x", expand=True, padx=5)

        value_frame = ttk.Frame(edit_win)
        value_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(value_frame, text="值:").pack(side="left")
        value_var = ttk.StringVar(value=original_value_str)
        value_entry = ttk.Entry(value_frame, textvariable=value_var)
        value_entry.pack(side="left", fill="x", expand=True, padx=5)
        value_entry.select_range(0, ttk.END)
        value_entry.focus_set()

        orig_frame = ttk.Frame(edit_win)
        orig_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(orig_frame, text="原始值:").pack(side="left")
        orig_var = ttk.StringVar(value=str(original_value))
        orig_entry = ttk.Entry(orig_frame, textvariable=orig_var, state="readonly")
        orig_entry.pack(side="left", fill="x", expand=True, padx=5)

        button_frame = ttk.Frame(edit_win)
        button_frame.pack(pady=10)

        def save_changes():
            try:
                new_value_str = value_var.get()

                new_value = self.convert_value(item_type, new_value_str)

                self.tree.item(selected_item, values=(item_type, self.get_value_string(new_value)))

                self.node_values[selected_item] = new_value

                self.update_nbt_value(selected_item, new_value)

                edit_win.destroy()
                self.update_status(f"已更新: {item_text} = {new_value_str}")
            except Exception as e:
                messagebox.showerror("编辑错误", f"无法更新值: {str(e)}")

        ttk.Button(button_frame, text="确定", command=save_changes, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=edit_win.destroy, width=10).pack(side="left", padx=10)

    def update_nbt_value(self, item_id, new_value):

        path = self.node_paths[item_id]

        current = self.level
        for key in path[:-1]:
            if isinstance(current, Compound):
                current = current[key]
            elif isinstance(current, List) and isinstance(key, int):
                current = current[key]

        last_key = path[-1]
        if isinstance(current, Compound):
            current[last_key] = new_value
        elif isinstance(current, List) and isinstance(last_key, int):
            current[last_key] = new_value

    def convert_value(self, type_str, value_str):
        if type_str == "Int":
            return Int(int(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "Float":
            return Float(float(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "Double":
            return Double(float(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "Byte":
            return Byte(int(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "Short":
            return Short(int(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "Long":
            return Long(int(value_str.split("(")[-1].split(")")[0]))
        elif type_str == "String":

            if value_str.startswith('"') and value_str.endswith('"'):
                value_str = value_str[1:-1]
            return String(value_str.split("(")[-1].split(")")[0])
        return value_str.split("(")[-1].split(")")[0]

    def add_node(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("添加节点", "请先选择一个父节点")
            return

        item_values = self.tree.item(selected_item, "values")
        if not item_values or "Compound" not in item_values[0]:
            messagebox.showwarning("添加节点", "只能在Compound节点下添加新节点")
            return

        add_win = ttk.Toplevel(self.root)
        add_win.title("添加新节点")
        add_win.geometry("400x250")
        add_win.transient(self.root)
        add_win.grab_set()

        key_frame = ttk.Frame(add_win)
        key_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(key_frame, text="键名:").pack(side="left")
        key_var = ttk.StringVar()
        key_entry = ttk.Entry(key_frame, textvariable=key_var)
        key_entry.pack(side="left", fill="x", expand=True, padx=5)
        key_entry.focus_set()

        type_frame = ttk.Frame(add_win)
        type_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(type_frame, text="类型:").pack(side="left")

        type_var = ttk.StringVar(value="String")
        types = ["String", "Int", "Float", "Double", "Byte", "Short", "Long", "Compound"]
        type_menu = ttk.Combobox(type_frame, textvariable=type_var, values=types, state="readonly")
        type_menu.pack(side="left", fill="x", expand=True, padx=5)

        value_frame = ttk.Frame(add_win)
        value_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(value_frame, text="值:").pack(side="left")
        value_var = ttk.StringVar(value="")
        value_entry = ttk.Entry(value_frame, textvariable=value_var)
        value_entry.pack(side="left", fill="x", expand=True, padx=5)
        hint_label = ttk.Label(add_win, text="对于Compound类型，值将被忽略", fg="gray")
        hint_label.pack(pady=5)

        def update_hint(*args):
            if type_var.get() == "Compound":
                value_entry.config(state="disabled")
                hint_label.config(text="对于Compound类型，值将被忽略")
            else:
                value_entry.config(state="normal")
                hint_label.config(text="")

        type_var.trace("w", update_hint)
        update_hint()
        button_frame = ttk.Frame(add_win)
        button_frame.pack(pady=10)

        def add_new_node():
            try:
                key = key_var.get().strip()
                if not key:
                    messagebox.showwarning("添加节点", "键名不能为空")
                    return

                node_type = type_var.get()
                value_str = value_var.get().strip()

                if node_type == "String":
                    new_value = String(value_str)
                elif node_type == "Int":
                    new_value = Int(int(value_str))
                elif node_type == "Float":
                    new_value = Float(float(value_str))
                elif node_type == "Double":
                    new_value = Double(float(value_str))
                elif node_type == "Byte":
                    new_value = Byte(int(value_str))
                elif node_type == "Short":
                    new_value = Short(int(value_str))
                elif node_type == "Long":
                    new_value = Long(int(value_str))
                elif node_type == "Compound":
                    new_value = Compound()
                else:
                    messagebox.showwarning("添加节点", f"不支持的类型: {node_type}")
                    return
                self.add_to_nbt(selected_item, key, new_value)
                self.update_tree()

                add_win.destroy()
                self.update_status(f"已添加新节点: {key}")
            except Exception as e:
                messagebox.showerror("添加节点错误", f"无法添加节点: {str(e)}")

        ttk.Button(button_frame, text="添加", command=add_new_node, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=add_win.destroy, width=10).pack(side="left", padx=10)

    def add_to_nbt(self, parent_id, key, value):
        parent_path = self.node_paths[parent_id]

        current = self.level
        for key in parent_path:
            if isinstance(current, Compound):
                current = current[key]
            elif isinstance(current, List) and isinstance(key, int):
                current = current[key]

        if isinstance(current, Compound):
            current[key] = value

    def delete_node(self):
        selected_item = self.tree.focus()
        if not selected_item:
            return

        if not messagebox.askyesno("删除节点", "确定要删除选中的节点吗？"):
            return
        self.delete_from_nbt(selected_item)
        self.update_tree()
        self.update_status("节点已删除")

    def delete_from_nbt(self, item_id):
        path = self.node_paths[item_id]
        current = self.level
        parent = None
        last_key = None

        for key in path[:-1]:
            parent = current
            if isinstance(current, Compound):
                current = current[key]
            elif isinstance(current, List) and isinstance(key, int):
                current = current[key]

        last_key = path[-1]

        if parent is not None:
            if isinstance(parent, Compound):
                del parent[last_key]
            elif isinstance(parent, List) and isinstance(last_key, int):
                del parent[last_key]

    def find_next(self):
        self.search_nodes(forward=True)

    def find_prev(self):
        self.search_nodes(forward=False)

    def search_nodes(self, forward=True):
        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showwarning("查找", "请输入查找内容")
            return
        if not self.search_results or search_text != self.last_search_text:
            self.search_results = []
            self.current_search_index = -1
            self.last_search_text = search_text
            for item in self.tree.get_children():
                self.search_tree(item, search_text)

        if not self.search_results:
            self.update_status("未找到匹配项")
            return
        if forward:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        else:
            self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        item = self.search_results[self.current_search_index]
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.tree.see(item)
        self.update_status(f"找到 {len(self.search_results)} 个匹配项，当前显示第 {self.current_search_index + 1} 个")

    def search_tree(self, item, search_text):
        item_text = self.tree.item(item, "text")
        item_values = self.tree.item(item, "values")
        match = False
        case_sensitive = self.case_sensitive_var.get()
        use_regex = self.regex_var.get()
        if use_regex:
            try:
                pattern = re.compile(search_text) if case_sensitive else re.compile(search_text, re.IGNORECASE)
                if pattern.search(item_text):
                    match = True
            except Exception as e:
                print(e)
        else:
            if case_sensitive:
                if search_text in item_text:
                    match = True
            else:
                if search_text.lower() in item_text.lower():
                    match = True
        if not match and len(item_values) > 1 and item_values[1]:
            value_str = item_values[1]
            if use_regex:
                try:
                    pattern = re.compile(search_text) if case_sensitive else re.compile(search_text, re.IGNORECASE)
                    if pattern.search(value_str):
                        match = True
                except:
                    pass
            else:
                if case_sensitive:
                    if search_text in value_str:
                        match = True
                else:
                    if search_text.lower() in value_str.lower():
                        match = True

        if match:
            self.search_results.append(item)

        for child in self.tree.get_children(item):
            self.search_tree(child, search_text)

    def refresh_view(self):
        if self.file_path:
            self.open_file(self.file_path)
            self.update_status("视图已刷新")

    def update_status(self, message):
        self.status_var.set(message)

    def enable_edit_controls(self, enabled):
        state = ttk.NORMAL if enabled else ttk.DISABLED
        self.menu_file.entryconfig("保存(S)", state=state)
        self.menu_file.entryconfig("另存为(A)", state=state)
        self.menu_edit.entryconfig("编辑节点(E)", state=state)
        self.menu_edit.entryconfig("添加节点(A)", state=state)
        self.menu_edit.entryconfig("删除节点(D)", state=state)

        self.btn_save.config(state=state)
        self.btn_edit.config(state=state)
        self.btn_add.config(state=state)
        self.btn_delete.config(state=state)

    def show_about(self):
        about_text = (
            "PyNBTExplorer\n"
            "版本: 1.0 for MacOS\n\n"
            "一个用Python实现的NBT文件浏览器\n"
            "使用tkinter作为UI框架，nbtlib处理NBT文件\n\n"
            "主要功能:\n"
            "- 浏览NBT文件\n"
        )
        messagebox.showinfo("关于 PyNBTExplorer", about_text)

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出 PyNBTExplorer 吗？"):
            self.root.destroy()


if __name__ == "__main__":
    app = NBTExplorer()
