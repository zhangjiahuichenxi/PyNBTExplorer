import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import config
from tkinter import messagebox
root = ttk.Window(title="设置")
style = ttk.Style()
theme_names = style.theme_names()
theme_selection = ttk.Frame(root, padding=(10, 10, 10, 0))
theme_selection.pack(fill=X, expand=YES)
lbl = ttk.Label(theme_selection, text="选择主题:")
theme_cbo = ttk.Combobox(
        master=theme_selection,
        text=style.theme.name,
        values=theme_names,
)
theme_cbo.pack(padx=10, side=RIGHT)
theme_cbo.current(theme_names.index(style.theme.name))
lbl.pack(side=RIGHT)
def change_theme(event):
    theme_cbo_value = theme_cbo.get()
    style.theme_use(theme_cbo_value)
    theme_cbo.selection_clear()
theme_cbo.bind('<<ComboboxSelected>>', change_theme)
theme_cbo['state'] = 'readonly'
theme_cbo.current(theme_names.index(config.theme))
def save():
    try:
        with open("./config.py","w") as f:
            f.write("theme = \""+theme_cbo.get() + "\"")
        messagebox.showinfo("提示","配置重启应用后启用")
    except Exception as e:
        messagebox.showerror("错误",str(e))
save_btn = ttk.Button(root,text="保存",command=save)
save_btn.pack(side="left")
exit_btn = ttk.Button(root,text="取消",command=root.quit)
exit_btn.pack(side="right")
root.mainloop()
