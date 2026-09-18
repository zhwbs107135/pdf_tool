import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import PyPDF2
import os
from pathlib import Path


class PDFDuplicateRemover:
    def __init__(self, root):
        self.root = root
        self.version = "V1.0.6"
        self.root.title("PDF页面处理工具({})".format(self.version))
        self.root.geometry("750x730")
        self.root.resizable(True, True)

        # ========== 变量定义 ==========
        # 主PDF文件路径
        self.pdf_path = tk.StringVar()
        # 要删除的页码字符串
        self.pages_to_delete = tk.StringVar()
        # 要旋转的页码字符串
        self.pages_to_rotate = tk.StringVar()
        # 旋转角度（90, -90, 180）
        self.rotation_angle = tk.StringVar(value="90")
        # 输出文件路径
        self.output_path = tk.StringVar()
        # PDF读取器对象
        self.pdf_reader = None
        # 总页数
        self.total_pages = 0
        # 当前激活的标签页（'delete', 'rotate', 'merge'）
        self.current_tab = "delete"

        # ========== 合并功能相关变量 ==========
        # 合并目录路径
        self.merge_dir = tk.StringVar()
        # PDF文件列表
        self.pdf_files = []
        # 每个文件的复选框变量
        self.file_vars = []

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建所有界面组件"""
        # 主框架 - 使用padding让内容不贴边
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 标题（带点击事件和悬停效果） ==========
        # 创建标题标签
        self.title_label = ttk.Label(main_frame, text="PDF页面处理工具", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=(0, 20))

        # 绑定事件：鼠标悬停时改变光标形状
        self.title_label.bind("<Enter>", self.on_title_hover_enter)
        self.title_label.bind("<Leave>", self.on_title_hover_leave)

        # 绑定事件：点击标题显示版本信息
        self.title_label.bind("<Button-1>", self.show_about_info)

        # 添加下划线提示（表示可点击）
        self.title_label.bind("<Enter>", lambda e: self.title_label.config(foreground="blue"))
        self.title_label.bind("<Leave>", lambda e: self.title_label.config(foreground="black"))

        # ========== 文件选择区域 ==========
        file_frame = ttk.LabelFrame(main_frame, text="选择主PDF文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))

        # 文件路径显示
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X)

        self.file_entry = ttk.Entry(path_frame, textvariable=self.pdf_path, state='readonly')
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_pdf)
        browse_btn.pack(side=tk.RIGHT)

        # 页面信息显示
        self.info_label = ttk.Label(file_frame, text="未选择文件", foreground="gray")
        self.info_label.pack(anchor=tk.W, pady=(5, 0))

        # ========== 标签页（Notebook） ==========
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 绑定标签页切换事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        # ---------- 标签页1: 删除页面 ----------
        self.delete_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.delete_tab, text="🗑️ 删除页面")

        # 帮助文本
        delete_help = "输入要删除的页码（从1开始），多个页码用逗号分隔，范围用'-'连接\n例如：1,3,5-8,10 表示删除第1、3、5、6、7、8、10页"
        help_label = ttk.Label(self.delete_tab, text=delete_help, wraplength=620, foreground="gray")
        help_label.pack(anchor=tk.W, pady=(0, 10))

        # 输入框
        delete_input_frame = ttk.Frame(self.delete_tab)
        delete_input_frame.pack(fill=tk.X)

        self.delete_entry = ttk.Entry(delete_input_frame, textvariable=self.pages_to_delete)
        self.delete_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        preview_delete_btn = ttk.Button(delete_input_frame, text="预览删除", command=self.preview_delete_pages)
        preview_delete_btn.pack(side=tk.RIGHT)

        # 提示信息
        delete_tip = ttk.Label(self.delete_tab, text="💡 提示：删除操作会从PDF中完全移除指定页面", foreground="blue")
        delete_tip.pack(anchor=tk.W, pady=(10, 0))

        # ---------- 标签页2: 旋转页面 ----------
        self.rotate_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.rotate_tab, text="🔄 旋转页面")

        # 帮助文本
        rotate_help = "输入要旋转的页码（从1开始），多个页码用逗号分隔，范围用'-'连接\n例如：1,3,5-8,10"
        help_label2 = ttk.Label(self.rotate_tab, text=rotate_help, wraplength=620, foreground="gray")
        help_label2.pack(anchor=tk.W, pady=(0, 10))

        # 输入框
        rotate_input_frame = ttk.Frame(self.rotate_tab)
        rotate_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.rotate_entry = ttk.Entry(rotate_input_frame, textvariable=self.pages_to_rotate)
        self.rotate_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        preview_rotate_btn = ttk.Button(rotate_input_frame, text="预览旋转", command=self.preview_rotate_pages)
        preview_rotate_btn.pack(side=tk.RIGHT)

        # 旋转角度选择
        angle_frame = ttk.LabelFrame(self.rotate_tab, text="旋转角度", padding="10")
        angle_frame.pack(fill=tk.X, pady=(0, 10))

        angle_inner_frame = ttk.Frame(angle_frame)
        angle_inner_frame.pack()

        ttk.Radiobutton(angle_inner_frame, text="顺时针 +90°", variable=self.rotation_angle,
                        value="90").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(angle_inner_frame, text="逆时针 -90°", variable=self.rotation_angle,
                        value="-90").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(angle_inner_frame, text="旋转 180°", variable=self.rotation_angle,
                        value="180").pack(side=tk.LEFT)

        # 旋转模式选择
        mode_frame = ttk.LabelFrame(self.rotate_tab, text="旋转模式", padding="10")
        mode_frame.pack(fill=tk.X)

        mode_inner_frame = ttk.Frame(mode_frame)
        mode_inner_frame.pack(anchor=tk.W)

        self.rotate_mode = tk.StringVar(value="absolute")
        ttk.Radiobutton(mode_inner_frame, text="绝对旋转（覆盖原有旋转）",
                        variable=self.rotate_mode, value="absolute").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_inner_frame, text="相对旋转（在原有旋转基础上增加）",
                        variable=self.rotate_mode, value="relative").pack(anchor=tk.W, pady=2)

        # 提示信息
        rotate_tip = ttk.Label(self.rotate_tab, text="💡 提示：旋转操作会改变指定页面的显示方向", foreground="blue")
        rotate_tip.pack(anchor=tk.W, pady=(10, 0))

        # ---------- 标签页3: 合并PDF ----------
        self.merge_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.merge_tab, text="📑 合并PDF")

        # 说明文本
        merge_info = ttk.Label(self.merge_tab, text="选择包含要合并PDF文件的目录，勾选要合并的文件", foreground="gray")
        merge_info.pack(anchor=tk.W, pady=(0, 10))

        # 目录选择
        merge_dir_frame = ttk.Frame(self.merge_tab)
        merge_dir_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(merge_dir_frame, text="目录：").pack(side=tk.LEFT, padx=(0, 5))
        self.merge_dir_entry = ttk.Entry(merge_dir_frame, textvariable=self.merge_dir, state='readonly')
        self.merge_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        merge_browse_btn = ttk.Button(merge_dir_frame, text="选择目录", command=self.browse_merge_dir)
        merge_browse_btn.pack(side=tk.RIGHT)

        # 刷新按钮
        refresh_frame = ttk.Frame(self.merge_tab)
        refresh_frame.pack(fill=tk.X, pady=(0, 10))

        refresh_btn = ttk.Button(refresh_frame, text="🔄 刷新文件列表", command=self.refresh_merge_files)
        refresh_btn.pack(side=tk.LEFT)

        # 全选/取消全选按钮
        select_frame = ttk.Frame(self.merge_tab)
        select_frame.pack(fill=tk.X, pady=(0, 10))

        select_all_btn = ttk.Button(select_frame, text="全选", command=self.select_all_files)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 10))

        deselect_all_btn = ttk.Button(select_frame, text="取消全选", command=self.deselect_all_files)
        deselect_all_btn.pack(side=tk.LEFT)

        # 文件列表区域（带滚动条）
        list_frame = ttk.LabelFrame(self.merge_tab, text="PDF文件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建带滚动条的列表容器
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        # Canvas用于实现滚动
        self.merge_canvas = tk.Canvas(list_container, height=100)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.merge_canvas.yview)
        self.merge_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.merge_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 文件列表的实际容器
        self.merge_list_frame = ttk.Frame(self.merge_canvas)
        self.merge_canvas.create_window((0, 0), window=self.merge_list_frame, anchor="nw")

        # 绑定框架大小变化事件，更新滚动区域
        self.merge_list_frame.bind("<Configure>", self.on_merge_frame_configure)

        # 统计信息标签
        self.merge_info_label = ttk.Label(self.merge_tab, text="未选择目录", foreground="gray")
        self.merge_info_label.pack(anchor=tk.W, pady=(10, 0))

        # ========== 输出和操作区域 ==========
        # 输出文件区域
        output_frame = ttk.LabelFrame(main_frame, text="保存为新的PDF文件", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 15))

        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X)

        self.output_entry = ttk.Entry(output_path_frame, textvariable=self.output_path, state='readonly')
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        output_browse_btn = ttk.Button(output_path_frame, text="另存为", command=self.browse_output)
        output_browse_btn.pack(side=tk.RIGHT)

        # ========== 按钮区域 ==========
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        # 进度条
        self.progress = ttk.Progressbar(button_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 操作按钮
        btn_frame = ttk.Frame(button_frame)
        btn_frame.pack(fill=tk.X)

        # 主操作按钮 - 根据当前标签页改变文本
        self.process_btn = ttk.Button(btn_frame, text="删除页面并保存", command=self.process_pdf)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        clear_btn = ttk.Button(btn_frame, text="清空", command=self.clear_all)
        clear_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # ========== 状态栏 ==========
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    # ========== 标题事件处理函数 ==========
    def on_title_hover_enter(self, event):
        """
        鼠标进入标题区域时，将光标变为手形
        """
        self.root.config(cursor="hand2")
        # 可选：改变标题颜色
        self.title_label.config(foreground="#0066cc")

    def on_title_hover_leave(self, event):
        """
        鼠标离开标题区域时，恢复默认光标
        """
        self.root.config(cursor="")
        # 恢复标题颜色
        self.title_label.config(foreground="black")

    def center_window(self, window, width, height):
        """
        将窗口居中显示

        Args:
            window: 要居中的窗口对象
            width: 窗口宽度
            height: 窗口高度
        """
        # 获取主窗口的位置和大小
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # 计算居中位置
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2

        # 设置窗口位置
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_about_info(self, event):
        """
        点击标题时显示版本信息和作者信息
        """
        # 创建关于对话框
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("关于 PDF页面处理工具({})".format(self.version))
        about_dialog.resizable(False, False)

        # 设置对话框背景色
        about_dialog.configure(bg="#f0f0f0")

        # 设置对话框为模态（必须关闭才能操作主窗口）
        about_dialog.transient(self.root)
        about_dialog.grab_set()

        # ========== 创建对话框内容 ==========
        # 主框架
        main_frame = tk.Frame(about_dialog, bg="#f0f0f0", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="📄 PDF页面处理工具",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0",
            fg="#0066cc"
        )
        title_label.pack(pady=(0, 5))

        # 版本信息
        version_label = tk.Label(
            main_frame,
            text="版本 {}".format(self.version),
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#666666"
        )
        version_label.pack(pady=(0, 15))

        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))

        author_text = tk.Label(
            main_frame,
            text="Wangbsh_wbs@hotmail.com,  2026.08",
            font=("Arial", 10),
            bg="#f0f0f0",
            justify=tk.LEFT
        )
        author_text.pack(anchor=tk.W, pady=(0, 20))

        # 关闭按钮
        close_btn = tk.Button(
            main_frame,
            text="确定",
            font=("Arial", 10, "bold"),
            command=about_dialog.destroy,
            bg="#0066cc",
            fg="white",
            padx=30,
            pady=5,
            relief=tk.RAISED,
            cursor="hand2",
            borderwidth=2
        )
        close_btn.pack()

        # 绑定键盘事件
        about_dialog.bind("<Return>", lambda e: about_dialog.destroy())
        about_dialog.bind("<Escape>", lambda e: about_dialog.destroy())

        # 计算对话框大小并居中
        about_dialog.update_idletasks()
        width = 320
        height = 230
        self.center_window(about_dialog, width, height)

        # 让确定按钮获得焦点
        close_btn.focus_set()

    def on_merge_frame_configure(self, event):
        """
        当合并文件列表框架大小变化时调用
        更新Canvas的滚动区域，使滚动条正常工作
        """
        self.merge_canvas.configure(scrollregion=self.merge_canvas.bbox("all"))

    def on_tab_changed(self, event):
        """
        标签页切换事件处理
        根据当前激活的标签页更新按钮文本和状态
        """
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # 删除标签页
            self.current_tab = "delete"
            self.process_btn.config(text="删除页面并保存")
            self.status_label.config(text="当前模式：删除页面")
        elif current_tab == 1:  # 旋转标签页
            self.current_tab = "rotate"
            self.process_btn.config(text="旋转页面并保存")
            self.status_label.config(text="当前模式：旋转页面")
        else:  # 合并标签页（索引为2）
            self.current_tab = "merge"
            self.process_btn.config(text="合并PDF并保存")
            self.status_label.config(text="当前模式：合并PDF")

    def browse_pdf(self):
        """选择主PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.pdf_path.set(file_path)
                self.pdf_reader = PyPDF2.PdfReader(file_path)
                self.total_pages = len(self.pdf_reader.pages)
                self.info_label.config(
                    text=f"总页数: {self.total_pages} 页",
                    foreground="black"
                )
                self.status_label.config(text=f"已加载: {os.path.basename(file_path)}")

                # 自动设置输出文件名
                base_name = os.path.splitext(file_path)[0]
                self.output_path.set(f"{base_name}_处理结果.pdf")

            except Exception as e:
                messagebox.showerror("错误", f"无法读取PDF文件:\n{str(e)}")
                self.pdf_path.set("")
                self.info_label.config(text="未选择文件", foreground="gray")
                self.status_label.config(text="加载失败")

    def browse_output(self):
        """选择输出文件路径"""
        if not self.pdf_path.get() and self.current_tab != "merge":
            messagebox.showwarning("警告", "请先选择PDF文件")
            return

        if self.current_tab == "merge" and not self.merge_dir.get():
            messagebox.showwarning("警告", "请先选择包含PDF的目录")
            return

        # 根据当前标签页生成默认文件名
        if self.current_tab == "merge":
            default_name = "合并结果.pdf"
            if self.merge_dir.get():
                dir_name = os.path.basename(self.merge_dir.get())
                default_name = f"{dir_name}_合并结果.pdf"
        else:
            default_name = os.path.basename(self.output_path.get())

        file_path = filedialog.asksaveasfilename(
            title="保存PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_name
        )

        if file_path:
            self.output_path.set(file_path)

    def browse_merge_dir(self):
        """选择包含要合并PDF文件的目录"""
        dir_path = filedialog.askdirectory(title="选择包含PDF文件的目录")
        if dir_path:
            self.merge_dir.set(dir_path)
            self.refresh_merge_files()

    def refresh_merge_files(self):
        """
        刷新合并文件列表
        扫描目录中的所有PDF文件并创建复选框
        """
        # 清空现有列表
        for widget in self.merge_list_frame.winfo_children():
            widget.destroy()

        self.file_vars = []
        self.pdf_files = []

        dir_path = self.merge_dir.get()
        if not dir_path:
            self.merge_info_label.config(text="未选择目录", foreground="gray")
            return

        if not os.path.exists(dir_path):
            self.merge_info_label.config(text="目录不存在", foreground="red")
            return

        # 获取所有PDF文件
        try:
            files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
            files.sort()  # 按文件名排序

            if not files:
                self.merge_info_label.config(text="目录中没有PDF文件", foreground="orange")
                return

            # 为每个文件创建复选框
            for i, filename in enumerate(files):
                var = tk.BooleanVar(value=True)  # 默认选中
                self.file_vars.append(var)
                self.pdf_files.append(filename)

                cb = ttk.Checkbutton(
                    self.merge_list_frame,
                    text=filename,
                    variable=var,
                    width=60
                )
                cb.pack(anchor=tk.W, pady=2)

            # 更新统计信息
            self.merge_info_label.config(
                text=f"找到 {len(files)} 个PDF文件，已全部选中",
                foreground="black"
            )
            self.status_label.config(text=f"已加载目录: {dir_path}，共{len(files)}个PDF文件")

        except Exception as e:
            messagebox.showerror("错误", f"读取目录失败:\n{str(e)}")
            self.merge_info_label.config(text="读取目录失败", foreground="red")

    def select_all_files(self):
        """全选所有文件"""
        for var in self.file_vars:
            var.set(True)
        self.update_merge_info()

    def deselect_all_files(self):
        """取消全选所有文件"""
        for var in self.file_vars:
            var.set(False)
        self.update_merge_info()

    def update_merge_info(self):
        """更新合并统计信息"""
        total = len(self.file_vars)
        selected = sum(1 for var in self.file_vars if var.get())
        if total > 0:
            self.merge_info_label.config(
                text=f"共 {total} 个PDF文件，已选择 {selected} 个",
                foreground="black"
            )

    def parse_pages(self, page_str, max_pages):
        """
        解析页码字符串
        支持格式：单页(5)、多页(1,3,5)、范围(5-10)、混合(1,3,5-8,10)

        Args:
            page_str: 页码字符串
            max_pages: 最大页数

        Returns:
            list: 页码列表，如果格式错误返回None
        """
        pages = set()

        if not page_str.strip():
            return pages

        parts = page_str.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                # 处理页码范围，如 5-10
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    if start > end:
                        start, end = end, start  # 自动修正反向范围
                    for p in range(start, end + 1):
                        if 1 <= p <= max_pages:
                            pages.add(p)
                except ValueError:
                    return None
            else:
                # 处理单个页码
                try:
                    p = int(part)
                    if 1 <= p <= max_pages:
                        pages.add(p)
                    else:
                        return None
                except ValueError:
                    return None

        return sorted(pages)

    def preview_delete_pages(self):
        """预览要删除的页面"""
        if not self.pdf_path.get():
            messagebox.showwarning("警告", "请先选择PDF文件")
            return

        page_str = self.pages_to_delete.get()
        if not page_str.strip():
            messagebox.showwarning("警告", "请输入要删除的页码")
            return

        pages = self.parse_pages(page_str, self.total_pages)
        if pages is None:
            messagebox.showerror("错误", f"无效的页码输入，请检查格式")
            return

        if not pages:
            messagebox.showinfo("提示", "没有有效的页码可删除")
            return

        preview_msg = f"将要删除以下页面 (共{len(pages)}页):\n\n"
        for i, p in enumerate(pages, 1):
            preview_msg += f"{p} "
            if i % 10 == 0:
                preview_msg += "\n"

        messagebox.showinfo("预览 - 删除页面", preview_msg)

    def preview_rotate_pages(self):
        """预览要旋转的页面"""
        if not self.pdf_path.get():
            messagebox.showwarning("警告", "请先选择PDF文件")
            return

        page_str = self.pages_to_rotate.get()
        if not page_str.strip():
            messagebox.showwarning("警告", "请输入要旋转的页码")
            return

        pages = self.parse_pages(page_str, self.total_pages)
        if pages is None:
            messagebox.showerror("错误", f"无效的页码输入，请检查格式")
            return

        if not pages:
            messagebox.showinfo("提示", "没有有效的页码可旋转")
            return

        angle = self.rotation_angle.get()
        preview_msg = f"将要旋转以下页面 (共{len(pages)}页):\n"
        preview_msg += f"旋转角度: {angle}°\n\n"
        for i, p in enumerate(pages, 1):
            preview_msg += f"{p} "
            if i % 10 == 0:
                preview_msg += "\n"

        messagebox.showinfo("预览 - 旋转页面", preview_msg)

    def process_pdf(self):
        """
        处理PDF的主入口
        根据当前标签页调用相应的处理方法
        """
        if self.current_tab == "delete":
            self.process_delete()
        elif self.current_tab == "rotate":
            self.process_rotate()
        else:
            self.process_merge()

    def process_delete(self):
        """执行删除页面操作"""
        if not self.pdf_path.get():
            messagebox.showwarning("警告", "请先选择PDF文件")
            return

        if not self.output_path.get():
            messagebox.showwarning("警告", "请指定输出文件路径")
            return

        delete_str = self.pages_to_delete.get().strip()
        if not delete_str:
            messagebox.showwarning("警告", "请输入要删除的页码")
            return

        pages_to_delete = self.parse_pages(delete_str, self.total_pages)
        if pages_to_delete is None:
            messagebox.showerror("错误", "删除页码格式无效")
            return

        if not pages_to_delete:
            messagebox.showinfo("提示", "没有有效的页码可删除")
            return

        output_file = self.output_path.get()
        if os.path.exists(output_file):
            if not messagebox.askyesno("确认", f"文件 {os.path.basename(output_file)} 已存在，是否覆盖？"):
                return

        try:
            self.progress['value'] = 0
            self.status_label.config(text="正在删除页面...")
            self.root.update()

            reader = PyPDF2.PdfReader(self.pdf_path.get())
            writer = PyPDF2.PdfWriter()

            total_pages = len(reader.pages)
            pages_to_delete_set = set(pages_to_delete)

            # 遍历所有页面，跳过要删除的页
            for i in range(total_pages):
                page_num = i + 1
                if page_num not in pages_to_delete_set:
                    writer.add_page(reader.pages[i])

                # 更新进度
                progress_value = ((i + 1) / total_pages) * 100
                self.progress['value'] = progress_value
                self.root.update()

            # 保存新PDF
            with open(output_file, 'wb') as f:
                writer.write(f)

            self.progress['value'] = 100
            self.status_label.config(text=f"删除完成! 已保存到: {os.path.basename(output_file)}")

            # 显示统计信息
            deleted_count = len(pages_to_delete)
            remaining_pages = total_pages - deleted_count

            info_msg = f"页面删除完成!\n\n"
            info_msg += f"原文件: {os.path.basename(self.pdf_path.get())}\n"
            info_msg += f"总页数: {total_pages}\n"
            info_msg += f"删除页数: {deleted_count}\n"
            info_msg += f"剩余页数: {remaining_pages}\n"
            info_msg += f"保存到: {os.path.basename(output_file)}"

            messagebox.showinfo("删除成功", info_msg)

        except Exception as e:
            messagebox.showerror("错误", f"删除页面时发生错误:\n{str(e)}")
            self.status_label.config(text="删除失败")
            self.progress['value'] = 0
        finally:
            self.root.update()

    def rotate_page(self, page, angle, mode):
        """
        旋转页面 - 使用多种方法确保兼容不同版本的PyPDF2

        Args:
            page: PDF页面对象
            angle: 旋转角度 (90, -90, 180)
            mode: 'absolute' 绝对旋转 或 'relative' 相对旋转

        Returns:
            旋转后的页面对象
        """
        # 方法1: 尝试使用 rotate 方法 (PyPDF2 2.x+)
        try:
            if hasattr(page, 'rotate'):
                if mode == "absolute":
                    if hasattr(page, 'get_object'):
                        page_obj = page.get_object()
                        if '/Rotate' in page_obj:
                            try:
                                from PyPDF2.generic import NumberObject
                                page_obj['/Rotate'] = NumberObject(angle % 360)
                            except:
                                del page_obj['/Rotate']
                    page.rotate(angle)
                else:
                    page.rotate(angle)
                return page
        except:
            pass

        # 方法2: 使用 add_rotation 方法
        try:
            if hasattr(page, 'add_rotation'):
                page.add_rotation(angle)
                return page
        except:
            pass

        # 方法3: 使用 rotateClockwise / rotateCounterClockwise (PyPDF2 1.x)
        try:
            if angle == 90 and hasattr(page, 'rotateClockwise'):
                page.rotateClockwise()
                return page
            elif angle == -90 and hasattr(page, 'rotateCounterClockwise'):
                page.rotateCounterClockwise()
                return page
            elif angle == 180 and hasattr(page, 'rotateClockwise'):
                page.rotateClockwise()
                page.rotateClockwise()
                return page
        except:
            pass

        # 方法4: 直接修改字典 (最底层的方法)
        try:
            if hasattr(page, 'get_object'):
                page_obj = page.get_object()
            else:
                page_obj = page

            current_rotate = 0
            if '/Rotate' in page_obj:
                try:
                    current_rotate = int(page_obj['/Rotate'])
                except:
                    current_rotate = 0

            if mode == "absolute":
                new_rotate = angle % 360
            else:
                new_rotate = (current_rotate + angle) % 360

            try:
                from PyPDF2.generic import NumberObject
                page_obj['/Rotate'] = NumberObject(new_rotate)
            except ImportError:
                try:
                    page_obj['/Rotate'] = new_rotate
                except:
                    page_obj.update({'/Rotate': new_rotate})

            return page
        except Exception as e:
            raise Exception(f"所有旋转方法都失败了: {str(e)}")

    def process_rotate(self):
        """执行旋转页面操作"""
        if not self.pdf_path.get():
            messagebox.showwarning("警告", "请先选择PDF文件")
            return

        if not self.output_path.get():
            messagebox.showwarning("警告", "请指定输出文件路径")
            return

        rotate_str = self.pages_to_rotate.get().strip()
        if not rotate_str:
            messagebox.showwarning("警告", "请输入要旋转的页码")
            return

        pages_to_rotate_list = self.parse_pages(rotate_str, self.total_pages)
        if pages_to_rotate_list is None:
            messagebox.showerror("错误", "旋转页码格式无效")
            return

        if not pages_to_rotate_list:
            messagebox.showinfo("提示", "没有有效的页码可旋转")
            return

        output_file = self.output_path.get()
        if os.path.exists(output_file):
            if not messagebox.askyesno("确认", f"文件 {os.path.basename(output_file)} 已存在，是否覆盖？"):
                return

        try:
            self.progress['value'] = 0
            self.status_label.config(text="正在旋转页面...")
            self.root.update()

            reader = PyPDF2.PdfReader(self.pdf_path.get())
            writer = PyPDF2.PdfWriter()

            total_pages = len(reader.pages)
            angle = int(self.rotation_angle.get())
            mode = self.rotate_mode.get()
            pages_to_rotate = set(pages_to_rotate_list)

            # 遍历所有页面，旋转指定的页面
            for i in range(total_pages):
                page_num = i + 1
                page = reader.pages[i]

                if page_num in pages_to_rotate:
                    page = self.rotate_page(page, angle, mode)

                writer.add_page(page)

                # 更新进度
                progress_value = ((i + 1) / total_pages) * 100
                self.progress['value'] = progress_value
                self.root.update()

            # 保存新PDF
            with open(output_file, 'wb') as f:
                writer.write(f)

            self.progress['value'] = 100
            self.status_label.config(text=f"旋转完成! 已保存到: {os.path.basename(output_file)}")

            # 显示统计信息
            rotated_count = len(pages_to_rotate)

            info_msg = f"页面旋转完成!\n\n"
            info_msg += f"原文件: {os.path.basename(self.pdf_path.get())}\n"
            info_msg += f"总页数: {total_pages}\n"
            info_msg += f"旋转页数: {rotated_count}\n"
            info_msg += f"旋转角度: {angle}°\n"
            info_msg += f"旋转模式: {'相对旋转' if mode == 'relative' else '绝对旋转'}\n"
            info_msg += f"保存到: {os.path.basename(output_file)}"

            messagebox.showinfo("旋转成功", info_msg)

        except Exception as e:
            messagebox.showerror("错误", f"旋转页面时发生错误:\n{str(e)}")
            self.status_label.config(text="旋转失败")
            self.progress['value'] = 0
        finally:
            self.root.update()

    def process_merge(self):
        """
        执行合并PDF操作
        如果有主文件，先添加主文件，然后按顺序添加选中的PDF文件
        """
        if not self.merge_dir.get():
            messagebox.showwarning("警告", "请先选择包含PDF文件的目录")
            return

        if not self.output_path.get():
            messagebox.showwarning("警告", "请指定输出文件路径")
            return

        # 获取选中的文件
        selected_files = []
        for i, var in enumerate(self.file_vars):
            if var.get():
                selected_files.append(self.pdf_files[i])

        if not selected_files:
            messagebox.showwarning("警告", "请至少选择一个PDF文件")
            return

        # 主文件路径
        main_file = self.pdf_path.get()
        output_file = self.output_path.get()

        if os.path.exists(output_file):
            if not messagebox.askyesno("确认", f"文件 {os.path.basename(output_file)} 已存在，是否覆盖？"):
                return

        try:
            self.progress['value'] = 0
            self.status_label.config(text="正在合并PDF...")
            self.root.update()

            writer = PyPDF2.PdfWriter()
            total_files = len(selected_files)
            current_file = 0

            # 如果有主文件，先添加主文件
            if main_file and os.path.exists(main_file):
                try:
                    reader = PyPDF2.PdfReader(main_file)
                    for page in reader.pages:
                        writer.add_page(page)
                    self.status_label.config(text=f"已添加主文件: {os.path.basename(main_file)}")
                    self.root.update()
                except Exception as e:
                    messagebox.showwarning("警告", f"添加主文件失败: {str(e)}")

            # 添加选中的PDF文件
            dir_path = self.merge_dir.get()
            for i, filename in enumerate(selected_files):
                file_path = os.path.join(dir_path, filename)
                try:
                    reader = PyPDF2.PdfReader(file_path)
                    for page in reader.pages:
                        writer.add_page(page)

                    # 更新进度
                    current_file = i + 1
                    progress_value = (current_file / total_files) * 100
                    self.progress['value'] = progress_value
                    self.status_label.config(text=f"正在合并: {filename} ({current_file}/{total_files})")
                    self.root.update()

                except Exception as e:
                    messagebox.showwarning("警告", f"无法添加文件 {filename}: {str(e)}")
                    continue

            # 保存合并后的PDF
            with open(output_file, 'wb') as f:
                writer.write(f)

            self.progress['value'] = 100
            self.status_label.config(text=f"合并完成! 已保存到: {os.path.basename(output_file)}")

            # 显示统计信息
            info_msg = f"PDF合并完成!\n\n"
            if main_file:
                info_msg += f"主文件: {os.path.basename(main_file)}\n"
            info_msg += f"合并文件数: {len(selected_files)}\n"
            if main_file:
                info_msg += f"总文件数: {len(selected_files) + (1 if main_file else 0)}\n"
            info_msg += f"保存到: {os.path.basename(output_file)}"

            messagebox.showinfo("合并成功", info_msg)

        except Exception as e:
            messagebox.showerror("错误", f"合并PDF时发生错误:\n{str(e)}")
            self.status_label.config(text="合并失败")
            self.progress['value'] = 0
        finally:
            self.root.update()

    def clear_all(self):
        """清空所有输入和状态"""
        # 清空主文件相关
        self.pdf_path.set("")
        self.pages_to_delete.set("")
        self.pages_to_rotate.set("")
        self.rotation_angle.set("90")
        self.output_path.set("")
        self.merge_dir.set("")

        # 清空合并文件列表
        for widget in self.merge_list_frame.winfo_children():
            widget.destroy()
        self.file_vars = []
        self.pdf_files = []
        self.merge_info_label.config(text="未选择目录", foreground="gray")

        # 重置状态
        self.info_label.config(text="未选择文件", foreground="gray")
        self.status_label.config(text="已清空")
        self.progress['value'] = 0


def main():
    """程序入口"""
    root = tk.Tk()
    app = PDFDuplicateRemover(root)
    root.mainloop()


if __name__ == "__main__":
    main()