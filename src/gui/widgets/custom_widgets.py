import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
import calendar

PRIMARY = "#1565c0"
PRIMARY_DARK = "#0d47a1"
PRIMARY_LIGHT = "#42a5f5"
SIDEBAR_BG = "#f8f9fa"
HEADER_BG = "#ffffff"
CARD_BG = "#ffffff"
SUCCESS = "#2e7d32"
DANGER = "#c62828"
WARNING = "#f57f17"
TEXT_DARK = "#1a1a2e"
TEXT_MUTED = "#6c757d"
BORDER = "#e8eaed"

ROW_EVEN = "#ffffff"
ROW_ODD = "#f8f9fa"
ROW_HOVER = "#e3f2fd"
ROW_SELECTED = "#bbdefb"
CHECKBOX_COL_WIDTH = 40

# ─────────────────────────────────────────────
# 1. DataTable
# ─────────────────────────────────────────────

class DataTable(ctk.CTkFrame):
    def __init__(self, parent, columns=None, checkbox_mode=False, context_menu=False,
                 page_size=20, row_height=36, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._columns = columns or []
        self._checkbox_mode = checkbox_mode
        self._context_menu_enabled = context_menu
        self._page_size = page_size
        self._row_height = row_height

        self._data = []
        self._filtered_data = []
        self._sort_column = None
        self._sort_ascending = True
        self._selected_row_idx = None
        self._selected_rows = set()
        self._current_page = 1
        self._total_pages = 1
        self._row_frames = []
        self._header_labels = []
        self._resize_active = False
        self._resize_col_index = None
        self._resize_start_x = 0
        self._resize_start_width = 0
        self._after_id = None
        self._sort_states = {}

        if self._checkbox_mode:
            self._checkbox_vars = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        self._header_frame = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=38)
        self._header_frame.grid(row=0, column=0, sticky="ew")
        self._header_frame.grid_propagate(False)
        self._render_header()

    def _render_header(self):
        for w in self._header_frame.winfo_children():
            w.destroy()
        self._header_labels = []
        self._header_separators = []
        offset = CHECKBOX_COL_WIDTH if self._checkbox_mode else 0
        x = offset
        for i, col in enumerate(self._columns):
            w = col.get('width', 120)
            cell = ctk.CTkFrame(self._header_frame, fg_color="transparent", width=w, height=38)
            cell.place(x=x, y=0)
            cell.bind("<Button-1>", lambda e, idx=i: self._on_header_click(idx))
            anchor_map_h = {'left': 'w', 'center': 'center', 'right': 'e'}
            label = ctk.CTkLabel(
                cell, text=col.get('text', col.get('key', '')),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_DARK, anchor=anchor_map_h.get(col.get('align', 'left'), 'w'),
                cursor="hand2"
            )
            label.pack(fill="both", expand=True, padx=(8, 4))
            label.bind("<Button-1>", lambda e, idx=i: self._on_header_click(idx))
            self._header_labels.append(label)
            if i < len(self._columns) - 1:
                sep = ctk.CTkFrame(cell, fg_color=BORDER, width=4, height=20, cursor="sb_h_double_arrow")
                sep.place(relx=1.0, x=0, rely=0.5, anchor="e")
                sep.bind("<Button-1>", lambda e, idx=i: self._on_resize_start(e, idx))
                sep.bind("<B1-Motion>", lambda e, idx=i: self._on_resize_move(e, idx))
                sep.bind("<ButtonRelease-1>", lambda e, idx=i: self._on_resize_end(e, idx))
                self._header_separators.append(sep)
            x += w
        self._header_frame.configure(width=max(x, 10))
        self._update_sort_indicators()

    def _build_body(self):
        self._body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._body_frame.grid(row=1, column=0, sticky="nsew")
        self._body_frame.grid_rowconfigure(0, weight=1)
        self._body_frame.grid_columnconfigure(0, weight=1)
        self._body_frame.grid_columnconfigure(1, weight=0)
        self._body_frame.grid_columnconfigure(2, weight=0)

        self._canvas = tk.Canvas(
            self._body_frame, bg="#f4f6f8", highlightthickness=0, borderwidth=0,
            relief="flat", takefocus=0
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self._v_scrollbar = ctk.CTkScrollbar(
            self._body_frame, orientation="vertical", command=self._canvas.yview
        )
        self._v_scrollbar.grid(row=0, column=1, sticky="ns")
        self._h_scrollbar = ctk.CTkScrollbar(
            self._body_frame, orientation="horizontal", command=self._canvas.xview
        )
        self._h_scrollbar.grid(row=1, column=0, sticky="ew")

        self._canvas.configure(
            yscrollcommand=self._v_scrollbar.set,
            xscrollcommand=self._h_scrollbar.set
        )

        self._rows_container = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._rows_container, anchor="nw", tags="inner"
        )

        self._rows_container.bind("<Configure>", self._on_container_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_container_configure(self, event=None):
        bbox = self._canvas.bbox("all")
        if bbox:
            self._canvas.configure(scrollregion=bbox)

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._canvas.yview_scroll(-3, "units")
        else:
            self._canvas.yview_scroll(3, "units")

    def _build_footer(self):
        self._footer_frame = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=36)
        self._footer_frame.grid(row=2, column=0, sticky="ew")
        self._footer_frame.grid_propagate(False)
        self._footer_frame.grid_columnconfigure(3, weight=1)
        self._footer_btn_first = ctk.CTkButton(
            self._footer_frame, text="\u25c0\u25c0", width=32, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._first_page
        )
        self._footer_btn_first.grid(row=0, column=0, padx=(8, 2), pady=4)
        self._footer_btn_prev = ctk.CTkButton(
            self._footer_frame, text="\u25c0", width=32, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._prev_page
        )
        self._footer_btn_prev.grid(row=0, column=1, padx=2, pady=4)
        self._footer_label = ctk.CTkLabel(
            self._footer_frame, text="Sayfa 0 / 0 (0 kay\u0131t)",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        )
        self._footer_label.grid(row=0, column=2, padx=12)
        self._footer_btn_next = ctk.CTkButton(
            self._footer_frame, text="\u25b6", width=32, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._next_page
        )
        self._footer_btn_next.grid(row=0, column=4, padx=2, pady=4)
        self._footer_btn_last = ctk.CTkButton(
            self._footer_frame, text="\u25b6\u25b6", width=32, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._last_page
        )
        self._footer_btn_last.grid(row=0, column=5, padx=(2, 8), pady=4)

    def _on_header_click(self, col_idx):
        if col_idx >= len(self._columns):
            return
        key = self._columns[col_idx]['key']
        if self._sort_column == key:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = key
            self._sort_ascending = True
        self._sort_data()
        self._render_page()
        self._update_sort_indicators()

    def _update_sort_indicators(self):
        for i, col in enumerate(self._columns):
            if i < len(self._header_labels):
                text = col.get('text', col.get('key', ''))
                if col['key'] == self._sort_column:
                    arrow = "\u25b2" if self._sort_ascending else "\u25bc"
                    self._header_labels[i].configure(text=f"{text} {arrow}")
                else:
                    self._header_labels[i].configure(text=text)

    def _sort_data(self):
        if not self._sort_column or not self._filtered_data:
            return
        try:
            self._filtered_data.sort(
                key=lambda r: (r.get(self._sort_column) is None, str(r.get(self._sort_column, '')).lower()),
                reverse=not self._sort_ascending
            )
        except Exception:
            pass

    def _on_resize_start(self, event, col_idx):
        self._resize_active = True
        self._resize_col_index = col_idx
        self._resize_start_x = event.x_root
        w = self._columns[col_idx].get('width', 120)
        self._resize_start_width = w

    def _on_resize_move(self, event, col_idx):
        if not self._resize_active or self._resize_col_index != col_idx:
            return
        delta = event.x_root - self._resize_start_x
        new_w = max(40, self._resize_start_width + delta)
        self._columns[col_idx]['width'] = new_w
        self._relayout_columns()
        self._on_container_configure()

    def _on_resize_end(self, event, col_idx):
        self._resize_active = False
        self._resize_col_index = None

    def _relayout_columns(self):
        self._render_header()
        for row_frame in self._row_frames:
            if row_frame and row_frame.winfo_exists():
                self._render_row_cells(row_frame)

    def _first_page(self):
        if self._current_page != 1:
            self._current_page = 1
            self._render_page()

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._render_page()

    def _last_page(self):
        if self._current_page != self._total_pages:
            self._current_page = self._total_pages
            self._render_page()

    def load_data(self, data):
        self._data = list(data) if data else []
        self._filtered_data = list(self._data)
        self._sort_column = None
        self._sort_ascending = True
        self._current_page = 1
        self._selected_row_idx = None
        self._selected_rows.clear()
        if self._checkbox_mode:
            self._checkbox_vars.clear()
        self._sort_data()
        self._render_page()

    def get_selected(self):
        if self._checkbox_mode:
            return [self._filtered_data[i] for i in sorted(self._selected_rows) if i < len(self._filtered_data)] if self._selected_rows else None
        if self._selected_row_idx is not None and self._selected_row_idx < len(self._filtered_data):
            return self._filtered_data[self._selected_row_idx]
        return None

    def get_selected_index(self):
        if self._checkbox_mode:
            return sorted(self._selected_rows) if self._selected_rows else None
        return self._selected_row_idx

    def get_row_count(self):
        return len(self._data)

    def get_filtered_row_count(self):
        return len(self._filtered_data)

    def clear(self):
        self.load_data([])

    def set_filter(self, filter_func):
        if filter_func:
            self._filtered_data = [r for r in self._data if filter_func(r)]
        else:
            self._filtered_data = list(self._data)
        self._current_page = 1
        self._selected_row_idx = None
        self._selected_rows.clear()
        self._render_page()

    def _render_page(self):
        self._clear_rows()
        total = len(self._filtered_data)
        if total == 0:
            self._total_pages = 1
            self._update_footer()
            self._show_empty_state()
            return

        self._total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages

        start = (self._current_page - 1) * self._page_size
        end = min(start + self._page_size, total)
        page_data = self._filtered_data[start:end]

        for row_idx, row_data in enumerate(page_data):
            self._create_row_widget(row_idx, row_data, start + row_idx)

        self._update_footer()
        self._on_container_configure()

    def _create_row_widget(self, visual_idx, row_data, data_idx):
        alt_bg = ROW_EVEN if visual_idx % 2 == 0 else ROW_ODD
        row_frame = ctk.CTkFrame(self._rows_container, fg_color=alt_bg, corner_radius=0, height=self._row_height)
        row_frame.pack(fill="x", pady=0)
        row_frame.pack_propagate(False)

        row_frame._data_idx = data_idx
        row_frame._visual_idx = visual_idx

        row_frame.bind("<Button-1>", lambda e, idx=data_idx: self._on_row_click(e, idx))
        row_frame.bind("<Enter>", lambda e, idx=data_idx: self._on_row_enter(e, idx))
        row_frame.bind("<Leave>", lambda e, idx=data_idx: self._on_row_leave(e, idx))

        if self._context_menu_enabled:
            row_frame.bind("<Button-3>", lambda e, idx=data_idx, d=row_data: self._on_context_menu(e, idx, d))

        cell_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        cell_frame.pack(fill="both", expand=True)
        cell_frame.bind("<Button-1>", lambda e, idx=data_idx: self._on_row_click(e, idx))

        offset = 0
        if self._checkbox_mode:
            chk_var = tk.BooleanVar(value=data_idx in self._selected_rows)
            chk = ctk.CTkCheckBox(
                cell_frame, text="", variable=chk_var, width=CHECKBOX_COL_WIDTH - 8,
                checkbox_width=18, checkbox_height=18,
                command=lambda idx=data_idx, var=chk_var: self._on_checkbox_toggle(idx, var)
            )
            chk.place(x=4, y=(self._row_height - 22) // 2)
            chk.bind("<Button-1>", lambda e, idx=data_idx, var=chk_var: self._on_checkbox_click(e, idx, var))
            self._checkbox_vars.append(chk_var)
            offset = CHECKBOX_COL_WIDTH

        x = offset
        for col_i, col in enumerate(self._columns):
            w = col.get('width', 120)
            val = row_data.get(col['key'], '')
            if isinstance(val, (datetime, date)):
                val = val.strftime("%d.%m.%Y") if hasattr(val, 'strftime') else str(val)
            val = str(val) if val is not None else ""
            align = col.get('align', 'left')
            anchor_map = {'left': 'w', 'center': 'center', 'right': 'e'}
            lbl = ctk.CTkLabel(
                cell_frame, text=val, font=ctk.CTkFont(size=11),
                text_color=TEXT_DARK, anchor=anchor_map.get(align, 'w'),
                width=w, height=self._row_height
            )
            lbl.place(x=x, y=0)
            lbl.bind("<Button-1>", lambda e, idx=data_idx: self._on_row_click(e, idx))
            if self._context_menu_enabled:
                lbl.bind("<Button-3>", lambda e, idx=data_idx, d=row_data: self._on_context_menu(e, idx, d))
            x += w

        if self._selected_row_idx == data_idx:
            row_frame.configure(fg_color=ROW_SELECTED)
        elif self._checkbox_mode and data_idx in self._selected_rows:
            row_frame.configure(fg_color=ROW_SELECTED)

        self._row_frames.append(row_frame)

    def _render_row_cells(self, row_frame):
        idx = getattr(row_frame, '_data_idx', None)
        if idx is None:
            return
        for w in row_frame.winfo_children():
            w.destroy()
        data_idx = idx
        visual_idx = getattr(row_frame, '_visual_idx', 0)
        row_data = self._filtered_data[data_idx] if data_idx < len(self._filtered_data) else None
        if not row_data:
            return

        alt_bg = ROW_EVEN if visual_idx % 2 == 0 else ROW_ODD
        if self._selected_row_idx == data_idx:
            alt_bg = ROW_SELECTED
        elif self._checkbox_mode and data_idx in self._selected_rows:
            alt_bg = ROW_SELECTED
        row_frame.configure(fg_color=alt_bg)

        cell_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        cell_frame.pack(fill="both", expand=True)
        cell_frame.bind("<Button-1>", lambda e, idx=data_idx: self._on_row_click(e, idx))

        offset = 0
        if self._checkbox_mode:
            chk_var = tk.BooleanVar(value=data_idx in self._selected_rows)
            chk = ctk.CTkCheckBox(
                cell_frame, text="", variable=chk_var, width=CHECKBOX_COL_WIDTH - 8,
                checkbox_width=18, checkbox_height=18,
                command=lambda idx=data_idx, var=chk_var: self._on_checkbox_toggle(idx, var)
            )
            chk.place(x=4, y=(self._row_height - 22) // 2)
            chk.bind("<Button-1>", lambda e, idx=data_idx, var=chk_var: self._on_checkbox_click(e, idx, var))
            offset = CHECKBOX_COL_WIDTH

        x = offset
        for col_i, col in enumerate(self._columns):
            w = col.get('width', 120)
            val = row_data.get(col['key'], '')
            if isinstance(val, (datetime, date)):
                val = val.strftime("%d.%m.%Y") if hasattr(val, 'strftime') else str(val)
            val = str(val) if val is not None else ""
            align = col.get('align', 'left')
            anchor_map = {'left': 'w', 'center': 'center', 'right': 'e'}
            lbl = ctk.CTkLabel(
                cell_frame, text=val, font=ctk.CTkFont(size=11),
                text_color=TEXT_DARK, anchor=anchor_map.get(align, 'w'),
                width=w, height=self._row_height
            )
            lbl.place(x=x, y=0)
            lbl.bind("<Button-1>", lambda e, idx=data_idx: self._on_row_click(e, idx))
            if self._context_menu_enabled:
                lbl.bind("<Button-3>", lambda e, idx=data_idx, d=row_data: self._on_context_menu(e, idx, d))
            x += w

    def _clear_rows(self):
        for rf in self._row_frames:
            if rf and rf.winfo_exists():
                rf.destroy()
        self._row_frames = []
        if self._checkbox_mode:
            self._checkbox_vars.clear()

    def _show_empty_state(self):
        empty_lbl = ctk.CTkLabel(
            self._rows_container, text="Kay\u0131t bulunamad\u0131",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        )
        empty_lbl.pack(expand=True, pady=40)
        self._row_frames.append(empty_lbl)

    def _update_footer(self):
        total = len(self._filtered_data)
        self._footer_label.configure(
            text=f"Sayfa {self._current_page} / {self._total_pages} ({total} kay\u0131t)"
        )

    def _on_row_click(self, event, data_idx):
        if not self._checkbox_mode:
            self._selected_row_idx = data_idx
            self._update_row_colors()
            if hasattr(self, '_on_select_callback') and self._on_select_callback:
                self._on_select_callback(self.get_selected())

    def _on_row_enter(self, event, data_idx):
        if not self._checkbox_mode and self._selected_row_idx != data_idx:
            rf = self._find_row_frame(data_idx)
            if rf and rf.winfo_exists() and rf.cget("fg_color") != ROW_SELECTED:
                rf.configure(fg_color=ROW_HOVER)

    def _on_row_leave(self, event, data_idx):
        if not self._checkbox_mode and self._selected_row_idx != data_idx:
            rf = self._find_row_frame(data_idx)
            if rf and rf.winfo_exists():
                idx = getattr(rf, '_visual_idx', 0)
                rf.configure(fg_color=ROW_EVEN if idx % 2 == 0 else ROW_ODD)

    def _on_checkbox_toggle(self, data_idx, var):
        if var.get():
            self._selected_rows.add(data_idx)
        else:
            self._selected_rows.discard(data_idx)
        rf = self._find_row_frame(data_idx)
        if rf and rf.winfo_exists():
            if data_idx in self._selected_rows:
                rf.configure(fg_color=ROW_SELECTED)
            else:
                idx = getattr(rf, '_visual_idx', 0)
                rf.configure(fg_color=ROW_EVEN if idx % 2 == 0 else ROW_ODD)
        if hasattr(self, '_on_select_callback') and self._on_select_callback:
            self._on_select_callback(self.get_selected())

    def _on_checkbox_click(self, event, data_idx, var):
        pass

    def _update_row_colors(self):
        for rf in self._row_frames:
            if not rf or not rf.winfo_exists():
                continue
            idx = getattr(rf, '_data_idx', None)
            if idx is None:
                continue
            vis = getattr(rf, '_visual_idx', 0)
            if idx == self._selected_row_idx:
                rf.configure(fg_color=ROW_SELECTED)
            else:
                rf.configure(fg_color=ROW_EVEN if vis % 2 == 0 else ROW_ODD)

    def _find_row_frame(self, data_idx):
        for rf in self._row_frames:
            if rf and rf.winfo_exists() and getattr(rf, '_data_idx', None) == data_idx:
                return rf
        return None

    def _on_context_menu(self, event, data_idx, row_data):
        if hasattr(self, '_context_menu_callback') and self._context_menu_callback:
            self._context_menu_callback(event, data_idx, row_data)

    def on_select(self, callback):
        self._on_select_callback = callback

    def on_context_menu(self, callback):
        self._context_menu_callback = callback
        self._context_menu_enabled = True

    def select_all(self):
        if not self._checkbox_mode:
            return
        self._selected_rows = set(range(len(self._filtered_data)))
        self._update_checkboxes()
        self._update_row_colors()
        if hasattr(self, '_on_select_callback') and self._on_select_callback:
            self._on_select_callback(self.get_selected())

    def deselect_all(self):
        if not self._checkbox_mode:
            return
        self._selected_rows.clear()
        self._update_checkboxes()
        self._update_row_colors()
        if hasattr(self, '_on_select_callback') and self._on_select_callback:
            self._on_select_callback(self.get_selected())

    def _update_checkboxes(self):
        for i, rf in enumerate(self._row_frames):
            if not rf or not rf.winfo_exists():
                continue
            data_idx = getattr(rf, '_data_idx', None)
            if data_idx is not None and i < len(self._checkbox_vars):
                self._checkbox_vars[i].set(data_idx in self._selected_rows)

    def get_visible_columns(self):
        return list(self._columns)

    def set_columns(self, columns):
        self._columns = list(columns)
        self._render_header()
        self._render_page()


# ─────────────────────────────────────────────
# 2. SearchBar
# ─────────────────────────────────────────────

class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, on_search=None, show_filter=False, filter_options=None,
                 show_date_range=False, placeholder="Ara...", **kwargs):
        super().__init__(parent, fg_color=HEADER_BG, corner_radius=8, **kwargs)
        self._on_search_callback = on_search

        self.grid_columnconfigure(1, weight=1)

        self._search_icon = ctk.CTkLabel(self, text="\U0001f50d", font=ctk.CTkFont(size=14), width=24)
        self._search_icon.grid(row=0, column=0, padx=(10, 0), pady=6)

        self._search_entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, height=32,
            border_color=BORDER, fg_color="#f4f6f8"
        )
        self._search_entry.grid(row=0, column=1, padx=(4, 6), pady=6, sticky="ew")
        self._search_entry.bind("<Return>", lambda e: self._do_search())

        self._search_btn = ctk.CTkButton(
            self, text="Ara", width=60, height=32,
            fg_color=PRIMARY, hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(size=12), command=self._do_search
        )
        self._search_btn.grid(row=0, column=2, padx=(0, 6), pady=6)

        self._filter_var = tk.StringVar()
        self._filter_dropdown = None
        self._date_from_entry = None
        self._date_to_entry = None

        col_offset = 3

        if show_filter and filter_options:
            self._filter_dropdown = ctk.CTkComboBox(
                self, values=filter_options, variable=self._filter_var,
                width=140, height=32, border_color=BORDER,
                state="readonly"
            )
            self._filter_dropdown.grid(row=0, column=col_offset, padx=4, pady=6)
            if filter_options:
                self._filter_var.set(filter_options[0])
            col_offset += 1

        if show_date_range:
            date_frame = ctk.CTkFrame(self, fg_color="transparent")
            date_frame.grid(row=0, column=col_offset, padx=4, pady=6)
            ctk.CTkLabel(date_frame, text="Ba\u015f:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 2))
            self._date_from_entry = ctk.CTkEntry(
                date_frame, placeholder_text="gg.aa.yyyy", width=100, height=32,
                border_color=BORDER, fg_color="#f4f6f8"
            )
            self._date_from_entry.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(date_frame, text="Bit:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 2))
            self._date_to_entry = ctk.CTkEntry(
                date_frame, placeholder_text="gg.aa.yyyy", width=100, height=32,
                border_color=BORDER, fg_color="#f4f6f8"
            )
            self._date_to_entry.pack(side="left")
            self._clear_date_btn = ctk.CTkButton(
                date_frame, text="X", width=24, height=24,
                fg_color="transparent", text_color=TEXT_MUTED,
                hover_color=BORDER, font=ctk.CTkFont(size=10),
                command=self._clear_dates
            )
            self._clear_date_btn.pack(side="left", padx=(4, 0))

    def _do_search(self):
        if self._on_search_callback:
            query = self._search_entry.get().strip()
            filter_val = self._filter_var.get() if self._filter_dropdown else None
            date_from = self._date_from_entry.get().strip() if self._date_from_entry else None
            date_to = self._date_to_entry.get().strip() if self._date_to_entry else None
            self._on_search_callback(query, filter_val, date_from, date_to)

    def _clear_dates(self):
        if self._date_from_entry:
            self._date_from_entry.delete(0, "end")
        if self._date_to_entry:
            self._date_to_entry.delete(0, "end")

    def clear(self):
        self._search_entry.delete(0, "end")
        self._clear_dates()
        if self._filter_dropdown and self._filter_dropdown.cget("values"):
            self._filter_var.set(self._filter_dropdown.cget("values")[0])

    def get_search_text(self):
        return self._search_entry.get().strip()

    def set_search_text(self, text):
        self._search_entry.delete(0, "end")
        self._search_entry.insert(0, text)

    def get_filter_value(self):
        return self._filter_var.get() if self._filter_dropdown else None

    def set_filter_value(self, value):
        if self._filter_dropdown:
            self._filter_var.set(value)

    def on_search(self, callback):
        self._on_search_callback = callback


# ─────────────────────────────────────────────
# 3. StatsCard
# ─────────────────────────────────────────────

class StatsCard(ctk.CTkFrame):
    def __init__(self, parent, title="", value="", change=None, icon=None,
                 footer=None, change_color=None, card_color=CARD_BG,
                 text_color=TEXT_DARK, value_color=PRIMARY, **kwargs):
        super().__init__(parent, fg_color=card_color, corner_radius=10, **kwargs)
        self._click_callback = None

        self.configure(border_width=1, border_color=BORDER)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=14, pady=(12, 0), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        if icon:
            icon_lbl = ctk.CTkLabel(
                top_frame, text=icon, font=ctk.CTkFont(size=18), width=28
            )
            icon_lbl.grid(row=0, column=0, padx=(0, 6), sticky="w")

        title_lbl = ctk.CTkLabel(
            top_frame, text=title, font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED, anchor="w"
        )
        title_lbl.grid(row=0, column=1, sticky="w")

        value_frame = ctk.CTkFrame(self, fg_color="transparent")
        value_frame.grid(row=1, column=0, padx=14, pady=(4, 4), sticky="ew")
        value_frame.grid_columnconfigure(0, weight=1)

        self._value_label = ctk.CTkLabel(
            value_frame, text=str(value), font=ctk.CTkFont(size=24, weight="bold"),
            text_color=value_color, anchor="w"
        )
        self._value_label.grid(row=0, column=0, sticky="w")

        if change is not None:
            if change_color is None:
                change_color = SUCCESS if change >= 0 else DANGER
            arrow = "\u25b2" if change >= 0 else "\u25bc"
            change_text = f"{arrow} {abs(change)}%"
            self._change_label = ctk.CTkLabel(
                value_frame, text=change_text, font=ctk.CTkFont(size=11),
                text_color=change_color, anchor="w"
            )
            self._change_label.grid(row=0, column=1, padx=(8, 0), sticky="w")

        if footer:
            footer_lbl = ctk.CTkLabel(
                self, text=footer, font=ctk.CTkFont(size=10),
                text_color=TEXT_MUTED, anchor="w"
            )
            footer_lbl.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

        self.bind("<Button-1>", self._on_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._on_click)

    def _on_click(self, event=None):
        if self._click_callback:
            self._click_callback()

    def on_click(self, callback):
        self._click_callback = callback

    def set_value(self, value):
        self._value_label.configure(text=str(value))

    def set_change(self, change, color=None):
        if change is not None:
            if color is None:
                color = SUCCESS if change >= 0 else DANGER
            arrow = "\u25b2" if change >= 0 else "\u25bc"
            text = f"{arrow} {abs(change)}%"
            if hasattr(self, '_change_label'):
                self._change_label.configure(text=text, text_color=color)
        elif hasattr(self, '_change_label'):
            self._change_label.configure(text="")

    def set_footer(self, text):
        pass


# ─────────────────────────────────────────────
# 4. FormField
# ─────────────────────────────────────────────

class FormField(ctk.CTkFrame):
    FIELD_TYPES = ("entry", "combobox", "textbox", "checkbox", "switch", "optionmenu")

    def __init__(self, parent, label="", field_type="entry", required=False,
                 validation_pattern=None, validation_message=None,
                 tooltip=None, error_message=None, height=28, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._field_type = field_type
        self._required = required
        self._validation_pattern = validation_pattern
        self._validation_message = validation_message
        self._field = None
        self._error_label = None
        self._tooltip_window = None
        self._textbox_dirty = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        label_frame = ctk.CTkFrame(self, fg_color="transparent")
        label_frame.grid(row=0, column=0, sticky="w", pady=(0, 2))

        label_text = label.rstrip("* ")
        if required:
            label_text += " *"

        self._label_widget = ctk.CTkLabel(
            label_frame, text=label_text, font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DARK, anchor="w"
        )
        self._label_widget.pack(side="left")

        if tooltip:
            tip_btn = ctk.CTkLabel(
                label_frame, text="\u24d8", font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED, cursor="question_arrow"
            )
            tip_btn.pack(side="left", padx=(4, 0))
            tip_btn.bind("<Enter>", lambda e: self._show_tooltip(tooltip, tip_btn))
            tip_btn.bind("<Leave>", lambda e: self._hide_tooltip())

        self._create_field(height)

    def _create_field(self, height):
        if self._field_type == "entry":
            self._field = ctk.CTkEntry(
                self, height=height, border_color=BORDER,
                fg_color="#ffffff", text_color=TEXT_DARK
            )
            self._field.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        elif self._field_type == "combobox":
            self._field = ctk.CTkComboBox(
                self, values=[], height=height, border_color=BORDER,
                fg_color="#ffffff", text_color=TEXT_DARK,
                state="readonly"
            )
            self._field.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        elif self._field_type == "textbox":
            self._field = ctk.CTkTextbox(
                self, height=height * 3, border_width=1,
                border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK
            )
            self._field.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        elif self._field_type == "checkbox":
            self._field = ctk.CTkCheckBox(
                self, text="", checkbox_width=20, checkbox_height=20,
                border_color=BORDER
            )
            self._field.grid(row=1, column=0, sticky="w", pady=(4, 2))

        elif self._field_type == "switch":
            self._field = ctk.CTkSwitch(self, text="")
            self._field.grid(row=1, column=0, sticky="w", pady=(4, 2))

        elif self._field_type == "optionmenu":
            self._field = ctk.CTkOptionMenu(
                self, values=[], height=height, fg_color="#ffffff",
                text_color=TEXT_DARK, button_color=PRIMARY,
                button_hover_color=PRIMARY_DARK
            )
            self._field.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        self._error_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=9), text_color=DANGER, anchor="w"
        )
        self._error_label.grid(row=2, column=0, sticky="w", pady=(0, 0))
        self._error_label.grid_remove()

    def get_value(self):
        if self._field_type == "entry" or self._field_type == "combobox":
            return self._field.get()
        elif self._field_type == "textbox":
            val = self._field.get("1.0", "end-1c").strip()
            return val
        elif self._field_type == "checkbox":
            return self._field.get()
        elif self._field_type == "switch":
            return self._field.get()
        elif self._field_type == "optionmenu":
            return self._field.get()
        return None

    def set_value(self, value):
        if value is None:
            return
        if self._field_type == "entry":
            self._field.delete(0, "end")
            self._field.insert(0, str(value))
        elif self._field_type == "combobox":
            self._field.set(str(value))
        elif self._field_type == "textbox":
            self._field.delete("1.0", "end")
            self._field.insert("1.0", str(value))
        elif self._field_type == "checkbox":
            self._field.select() if value else self._field.deselect()
        elif self._field_type == "switch":
            if value:
                self._field.select()
            else:
                self._field.deselect()
        elif self._field_type == "optionmenu":
            self._field.set(str(value))

    def set_options(self, options):
        if self._field_type == "combobox":
            self._field.configure(values=list(options))
            if options:
                self._field.set(options[0])
        elif self._field_type == "optionmenu":
            self._field.configure(values=list(options))
            if options:
                self._field.set(options[0])

    def get_field(self):
        return self._field

    def validate(self):
        val = self.get_value()
        if self._required:
            if self._field_type in ("checkbox", "switch"):
                if not val:
                    self._show_error("Bu alan zorunludur")
                    return False
            elif not val or (isinstance(val, str) and not val.strip()):
                self._show_error("Bu alan zorunludur")
                return False

        if self._validation_pattern and val:
            import re
            if not re.match(self._validation_pattern, str(val)):
                self._show_error(self._validation_message or "Ge\u00e7ersiz format")
                return False

        self._show_success()
        return True

    def set_valid(self, valid, message=""):
        if valid:
            self._show_success()
        else:
            self._show_error(message)

    def _show_error(self, message):
        if self._field:
            border_color = DANGER
            if hasattr(self._field, 'configure'):
                try:
                    self._field.configure(border_color=border_color)
                except Exception:
                    pass
        if self._error_label:
            self._error_label.configure(text=message, text_color=DANGER)
            self._error_label.grid()

    def _show_success(self):
        if self._field:
            try:
                self._field.configure(border_color=BORDER)
            except Exception:
                pass
        if self._error_label:
            self._error_label.configure(text="")
            self._error_label.grid_remove()

    def clear(self):
        if self._field_type == "entry":
            self._field.delete(0, "end")
        elif self._field_type == "textbox":
            self._field.delete("1.0", "end")
        elif self._field_type == "checkbox":
            self._field.deselect()
        elif self._field_type == "switch":
            self._field.deselect()
        elif self._field_type == "combobox":
            if self._field.cget("values"):
                self._field.set(self._field.cget("values")[0])
            else:
                self._field.set("")
        elif self._field_type == "optionmenu":
            if self._field.cget("values"):
                self._field.set(self._field.cget("values")[0])
            else:
                self._field.set("")
        self._show_success()

    def _show_tooltip(self, text, anchor):
        if self._tooltip_window:
            self._hide_tooltip()
        self._tooltip_window = tk.Toplevel(self, bg="#ffffe0", padx=4, pady=2)
        self._tooltip_window.overrideredirect(True)
        self._tooltip_window.attributes("-topmost", True)
        lbl = tk.Label(
            self._tooltip_window, text=text, bg="#ffffe0", fg="#333333",
            font=("Segoe UI", 9), wraplength=250, justify="left"
        )
        lbl.pack()
        x = anchor.winfo_rootx() + 20
        y = anchor.winfo_rooty() - 10
        self._tooltip_window.geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        if self._tooltip_window:
            try:
                self._tooltip_window.destroy()
            except Exception:
                pass
            self._tooltip_window = None


# ─────────────────────────────────────────────
# 5. ActionButton
# ─────────────────────────────────────────────

ACTION_COLORS = {
    "primary": (PRIMARY, PRIMARY_DARK, "#ffffff"),
    "success": (SUCCESS, "#1b5e20", "#ffffff"),
    "danger": (DANGER, "#b71c1c", "#ffffff"),
    "warning": (WARNING, "#e65100", "#ffffff"),
    "info": (PRIMARY_LIGHT, "#1e88e5", "#ffffff"),
}

BUTTON_SIZES = {
    "sm": {"height": 28, "font": 11, "padx": 10},
    "md": {"height": 34, "font": 12, "padx": 16},
    "lg": {"height": 42, "font": 14, "padx": 24},
}

class ActionButton(ctk.CTkButton):
    def __init__(self, parent, text="", icon=None, color="primary", size="md", **kwargs):
        self._action_color = color
        self._action_size = size
        self._action_icon = icon

        color_cfg = ACTION_COLORS.get(color, ACTION_COLORS["primary"])
        size_cfg = BUTTON_SIZES.get(size, BUTTON_SIZES["md"])

        display_text = f"{icon} {text}" if icon else text

        super().__init__(
            parent,
            text=display_text,
            fg_color=color_cfg[0],
            hover_color=color_cfg[1],
            text_color=color_cfg[2],
            font=ctk.CTkFont(size=size_cfg["font"], weight="bold"),
            height=size_cfg["height"],
            corner_radius=6,
            cursor="hand2",
            **kwargs
        )

    def set_text(self, text):
        display = f"{self._action_icon} {text}" if self._action_icon else text
        self.configure(text=display)

    def set_icon(self, icon):
        self._action_icon = icon
        self.set_text(self.cget("text").replace(f"{self._action_icon} ", "") if self._action_icon else "")

    def set_color(self, color):
        self._action_color = color
        color_cfg = ACTION_COLORS.get(color, ACTION_COLORS["primary"])
        self.configure(fg_color=color_cfg[0], hover_color=color_cfg[1], text_color=color_cfg[2])

    def set_size(self, size):
        self._action_size = size
        size_cfg = BUTTON_SIZES.get(size, BUTTON_SIZES["md"])
        self.configure(
            height=size_cfg["height"],
            font=ctk.CTkFont(size=size_cfg["font"], weight="bold")
        )


# ─────────────────────────────────────────────
# 6. ModalDialog
# ─────────────────────────────────────────────

class ModalDialog(ctk.CTkToplevel):
    RESULT_OK = "ok"
    RESULT_CANCEL = "cancel"
    RESULT_YES = "yes"
    RESULT_NO = "no"

    def __init__(self, parent, title="", message="", detail=None, buttons="ok_cancel",
                 form_fields=None, width=420, height=None):
        super().__init__(parent)
        self._result = None

        self.title(title)
        self.lift()
        self.focus_force()
        self.grab_set()
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())

        if height:
            self.geometry(f"{width}x{height}")
        else:
            self.geometry(f"{width}x0")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_frame.grid_columnconfigure(0, weight=1)

        row = 0
        if title:
            title_lbl = ctk.CTkLabel(
                main_frame, text=title,
                font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_DARK,
                anchor="w", justify="left"
            )
            title_lbl.grid(row=row, column=0, padx=20, pady=(20, 8), sticky="ew")
            row += 1

        msg_lbl = ctk.CTkLabel(
            main_frame, text=message,
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
            anchor="w", justify="left", wraplength=width - 40
        )
        msg_lbl.grid(row=row, column=0, padx=20, pady=(0, 8), sticky="ew")
        row += 1

        if detail:
            detail_lbl = ctk.CTkLabel(
                main_frame, text=detail,
                font=ctk.CTkFont(size=11), text_color=TEXT_DARK,
                anchor="w", justify="left", wraplength=width - 40
            )
            detail_lbl.grid(row=row, column=0, padx=20, pady=(0, 12), sticky="ew")
            row += 1

        self._form_fields = []
        if form_fields:
            for ff_config in form_fields:
                ff = FormField(main_frame, **ff_config)
                ff.grid(row=row, column=0, padx=20, pady=(0, 8), sticky="ew")
                self._form_fields.append(ff)
                row += 1

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, padx=20, pady=(8, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        self._buttons = []
        if buttons == "ok_cancel":
            self._add_button(btn_frame, "\u0130ptal", "secondary", self.RESULT_CANCEL, left=True)
            self._add_button(btn_frame, "Tamam", "primary", self.RESULT_OK)
        elif buttons == "yes_no":
            self._add_button(btn_frame, "Hay\u0131r", "secondary", self.RESULT_NO, left=True)
            self._add_button(btn_frame, "Evet", "primary", self.RESULT_YES)
        elif buttons == "ok":
            self._add_button(btn_frame, "Tamam", "primary", self.RESULT_OK)
        elif buttons == "close":
            self._add_button(btn_frame, "Kapat", "secondary", self.RESULT_CANCEL)
        elif isinstance(buttons, list):
            for i, btn_def in enumerate(buttons):
                is_left = i == 0
                self._add_button(
                    btn_frame, btn_def.get("text", ""),
                    btn_def.get("style", "secondary"),
                    btn_def.get("result", self.RESULT_OK),
                    left=is_left
                )

        self.update_idletasks()
        self._center_on_parent(parent)
        self.transient(parent)

    def _add_button(self, parent, text, style, result, left=False):
        if style == "primary":
            fg, hov, txt = ACTION_COLORS["primary"]
        elif style == "danger":
            fg, hov, txt = ACTION_COLORS["danger"]
        elif style == "success":
            fg, hov, txt = ACTION_COLORS["success"]
        else:
            fg, hov, txt = "transparent", BORDER, TEXT_DARK

        btn = ctk.CTkButton(
            parent, text=text, fg_color=fg, hover_color=hov,
            text_color=txt, font=ctk.CTkFont(size=12),
            height=32, width=90, corner_radius=6,
            command=lambda r=result: self._set_result(r)
        )
        if left:
            btn.grid(row=0, column=0, padx=(0, 6), sticky="w")
        else:
            btn.grid(row=0, column=1, padx=(6, 0), sticky="e")
        self._buttons.append(btn)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw = self.winfo_width()
        dh = self.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _set_result(self, result):
        self._result = result
        self._on_close()

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def show(self):
        self.master.wait_window(self)
        return self._result

    def get_form_values(self):
        return {ff._label_widget.cget("text").rstrip(" *"): ff.get_value() for ff in self._form_fields}

    def get_form_field(self, index):
        if 0 <= index < len(self._form_fields):
            return self._form_fields[index]
        return None


# ─────────────────────────────────────────────
# 7. ToastNotification
# ─────────────────────────────────────────────

TOAST_COLORS = {
    "success": (SUCCESS, "#ffffff"),
    "error": (DANGER, "#ffffff"),
    "warning": (WARNING, "#ffffff"),
    "info": (PRIMARY, "#ffffff"),
}

TOAST_ICONS = {
    "success": "\u2713",
    "error": "\u2717",
    "warning": "\u26a0",
    "info": "\u2139",
}

class ToastNotification:
    _active_toasts = []

    def __init__(self):
        pass

    @classmethod
    def show(cls, parent, message, toast_type="info", duration=3000):
        color_cfg = TOAST_COLORS.get(toast_type, TOAST_COLORS["info"])
        icon = TOAST_ICONS.get(toast_type, "\u2139")

        toast = ctk.CTkToplevel(parent)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.lift()

        toast.configure(fg_color=color_cfg[0])
        toast.frame = ctk.CTkFrame(toast, fg_color=color_cfg[0], corner_radius=8)
        toast.frame.pack(fill="both", expand=True, padx=0, pady=0)

        icon_lbl = ctk.CTkLabel(
            toast.frame, text=icon,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=color_cfg[1]
        )
        icon_lbl.pack(side="left", padx=(12, 4), pady=10)

        msg_lbl = ctk.CTkLabel(
            toast.frame, text=message,
            font=ctk.CTkFont(size=12),
            text_color=color_cfg[1], wraplength=280
        )
        msg_lbl.pack(side="left", padx=(0, 16), pady=10)

        close_btn = ctk.CTkButton(
            toast.frame, text="X", width=20, height=20,
            fg_color="transparent", hover_color="#ffffff",
            text_color=color_cfg[1], font=ctk.CTkFont(size=10),
            command=lambda: cls._dismiss(toast)
        )
        close_btn.pack(side="right", padx=(0, 8))

        toast.update_idletasks()
        tw = toast.winfo_width() or 320
        th = toast.winfo_height() or 50

        parent.update_idletasks()
        pw = parent.winfo_width()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        start_x = px + pw - tw - 20
        base_y = py + 60
        offset = len(cls._active_toasts) * (th + 8)
        start_y = base_y + offset

        toast.geometry(f"{tw}x{th}+{start_x}+{start_y}")
        toast._target_y = start_y

        toast.attributes("-alpha", 0.0)
        cls._active_toasts.append(toast)
        cls._fade_in(toast, 10)

        if duration > 0:
            toast.after(duration, lambda: cls._dismiss(toast))

        return toast

    @classmethod
    def _fade_in(cls, toast, step=0):
        if not toast.winfo_exists():
            return
        try:
            alpha = min(1.0, step / 10)
            toast.attributes("-alpha", alpha)
            if alpha < 1.0:
                toast.after(20, lambda: cls._fade_in(toast, step + 1))
        except Exception:
            pass

    @classmethod
    def _fade_out(cls, toast, step=10):
        if not toast.winfo_exists():
            cls._cleanup(toast)
            return
        try:
            alpha = max(0, step / 10)
            toast.attributes("-alpha", alpha)
            if alpha > 0:
                toast.after(20, lambda: cls._fade_out(toast, step - 1))
            else:
                cls._dismiss_now(toast)
        except Exception:
            cls._dismiss_now(toast)

    @classmethod
    def _dismiss(cls, toast):
        if toast in cls._active_toasts:
            cls._fade_out(toast, 10)

    @classmethod
    def _dismiss_now(cls, toast):
        if toast in cls._active_toasts:
            cls._active_toasts.remove(toast)
        try:
            toast.destroy()
        except Exception:
            pass
        cls._reposition()

    @classmethod
    def _cleanup(cls, toast):
        if toast in cls._active_toasts:
            cls._active_toasts.remove(toast)
        cls._reposition()

    @classmethod
    def _reposition(cls):
        base_y = 0
        for i, t in enumerate(cls._active_toasts):
            if t.winfo_exists():
                th = t.winfo_height() or 50
                target_y = base_y + 60 + i * (th + 8)
                try:
                    geo = t.geometry()
                    parts = geo.split("+")
                    if len(parts) >= 3:
                        x = parts[1]
                        t.geometry(f"+{x}+{target_y}")
                except Exception:
                    pass

    @classmethod
    def dismiss_all(cls):
        for t in list(cls._active_toasts):
            cls._dismiss_now(t)


# ─────────────────────────────────────────────
# 8. DatePicker
# ─────────────────────────────────────────────

TR_MONTHS = [
    "", "Ocak", "\u015eubat", "Mart", "Nisan", "May\u0131s", "Haziran",
    "Temmuz", "A\u011fustos", "Eyl\u00fcl", "Ekim", "Kas\u0131m", "Aral\u0131k"
]
TR_DAYS = ["Paz", "Pzt", "Sal", "\u00c7ar", "Per", "Cum", "Cmt"]
TR_DAYS_FULL = ["Pazar", "Pazartesi", "Sal\u0131", "\u00c7ar\u015famba", "Per\u015fembe", "Cuma", "Cumartesi"]

class DatePicker(ctk.CTkFrame):
    def __init__(self, parent, on_date_selected=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_date_selected = on_date_selected
        self._selected_date = None
        self._popup = None

        self.grid_columnconfigure(1, weight=1)

        self._entry = ctk.CTkEntry(
            self, placeholder_text="gg.aa.yyyy", height=32,
            border_color=BORDER, fg_color="#ffffff", text_color=TEXT_DARK
        )
        self._entry.grid(row=0, column=0, padx=(0, 4), pady=0, sticky="ew")
        self._entry.bind("<Button-1>", lambda e: self._open_popup())
        self._entry.bind("<FocusIn>", lambda e: self._open_popup())
        self._entry.bind("<Key>", lambda e: self._check_manual_entry() if e.keysym == "Return" else None)

        self._btn = ctk.CTkButton(
            self, text="\U0001f4c5", width=32, height=32,
            fg_color="transparent", text_color=TEXT_MUTED,
            hover_color=BORDER, font=ctk.CTkFont(size=14),
            command=self._open_popup
        )
        self._btn.grid(row=0, column=1, padx=0, pady=0)

        self._clear_btn = ctk.CTkButton(
            self, text="X", width=24, height=24,
            fg_color="transparent", text_color=TEXT_MUTED,
            hover_color=BORDER, font=ctk.CTkFont(size=10),
            command=self.clear
        )
        self._clear_btn.grid(row=0, column=2, padx=(2, 0), pady=0)

    def _open_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.lift()
            return

        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.resizable(False, False)

        now = self._selected_date or date.today()
        self._cal_year = now.year
        self._cal_month = now.month

        main = ctk.CTkFrame(self._popup, fg_color=CARD_BG, corner_radius=8,
                            border_width=1, border_color=BORDER)
        main.pack(fill="both", expand=True, padx=0, pady=0)

        self._nav_frame = ctk.CTkFrame(main, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=6, pady=(6, 2))

        btn_prev = ctk.CTkButton(
            self._nav_frame, text="\u25c0", width=28, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._prev_month
        )
        btn_prev.pack(side="left", padx=2)

        self._month_year_label = ctk.CTkLabel(
            self._nav_frame,
            text=f"{TR_MONTHS[self._cal_month]} {self._cal_year}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK
        )
        self._month_year_label.pack(side="left", expand=True, fill="x")

        btn_next = ctk.CTkButton(
            self._nav_frame, text="\u25b6", width=28, height=26,
            fg_color="transparent", text_color=TEXT_DARK, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._next_month
        )
        btn_next.pack(side="right", padx=2)

        self._cal_frame = ctk.CTkFrame(main, fg_color="transparent")
        self._cal_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self._render_calendar()

        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.pack(fill="x", padx=6, pady=(2, 6))

        today_btn = ctk.CTkButton(
            bottom, text="Bug\u00fcn", width=60, height=26,
            fg_color="transparent", text_color=PRIMARY, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._select_today
        )
        today_btn.pack(side="left", padx=2)

        clear_btn = ctk.CTkButton(
            bottom, text="Temizle", width=60, height=26,
            fg_color="transparent", text_color=TEXT_MUTED, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._clear_from_popup
        )
        clear_btn.pack(side="left", padx=2)

        close_btn = ctk.CTkButton(
            bottom, text="Kapat", width=60, height=26,
            fg_color="transparent", text_color=TEXT_MUTED, hover_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._close_popup
        )
        close_btn.pack(side="right", padx=2)

        self._position_popup()

    def _position_popup(self):
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        self._popup.geometry(f"+{x}+{y}")

    def _render_calendar(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        header.pack(fill="x")
        for d in TR_DAYS:
            lbl = ctk.CTkLabel(header, text=d, font=ctk.CTkFont(size=9, weight="bold"),
                               text_color=TEXT_MUTED, width=36, height=20)
            lbl.pack(side="left")

        first_day = date(self._cal_year, self._cal_month, 1)
        _, last_day_num = calendar.monthrange(self._cal_year, self._cal_month)
        start_weekday = first_day.weekday()
        start_sunday = (start_weekday + 1) % 7

        grid = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)

        day = 1
        for row_idx in range(6):
            if day > last_day_num:
                break
            row_frame = ctk.CTkFrame(grid, fg_color="transparent")
            row_frame.pack(fill="x")
            for col_idx in range(7):
                if (row_idx == 0 and col_idx < start_sunday) or day > last_day_num:
                    empty = ctk.CTkLabel(row_frame, text="", width=36, height=28)
                    empty.pack(side="left")
                else:
                    is_today = (self._cal_year == date.today().year and
                                self._cal_month == date.today().month and
                                day == date.today().day)
                    is_selected = (self._selected_date and
                                   self._cal_year == self._selected_date.year and
                                   self._cal_month == self._selected_date.month and
                                   day == self._selected_date.day)
                    day_num = day
                    btn_bg = ROW_SELECTED if is_selected else ("transparent" if not is_today else "#e8f5e9")
                    btn = ctk.CTkButton(
                        row_frame, text=str(day_num), width=36, height=28,
                        fg_color=btn_bg, hover_color=ROW_HOVER,
                        text_color=PRIMARY if is_today else TEXT_DARK,
                        font=ctk.CTkFont(size=10, weight="bold" if is_today else "normal"),
                        corner_radius=4,
                        command=lambda d=day_num: self._select_date(d)
                    )
                    btn.pack(side="left")
                    day += 1

    def _prev_month(self):
        if self._cal_month == 1:
            self._cal_month = 12
            self._cal_year -= 1
        else:
            self._cal_month -= 1
        self._month_year_label.configure(
            text=f"{TR_MONTHS[self._cal_month]} {self._cal_year}"
        )
        self._render_calendar()

    def _next_month(self):
        if self._cal_month == 12:
            self._cal_month = 1
            self._cal_year += 1
        else:
            self._cal_month += 1
        self._month_year_label.configure(
            text=f"{TR_MONTHS[self._cal_month]} {self._cal_year}"
        )
        self._render_calendar()

    def _select_date(self, day):
        self._selected_date = date(self._cal_year, self._cal_month, day)
        self._entry.delete(0, "end")
        self._entry.insert(0, self._selected_date.strftime("%d.%m.%Y"))
        self._close_popup()
        if self._on_date_selected:
            self._on_date_selected(self._selected_date)

    def _select_today(self):
        self._selected_date = date.today()
        self._entry.delete(0, "end")
        self._entry.insert(0, self._selected_date.strftime("%d.%m.%Y"))
        self._close_popup()
        if self._on_date_selected:
            self._on_date_selected(self._selected_date)

    def _clear_from_popup(self):
        self._selected_date = None
        self._entry.delete(0, "end")
        self._close_popup()
        if self._on_date_selected:
            self._on_date_selected(None)

    def _close_popup(self):
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None

    def _check_manual_entry(self):
        try:
            dt = datetime.strptime(self._entry.get().strip(), "%d.%m.%Y")
            self._selected_date = dt.date()
            if self._on_date_selected:
                self._on_date_selected(self._selected_date)
        except (ValueError, AttributeError):
            pass

    def get_date(self):
        if self._selected_date:
            return self._selected_date
        try:
            dt = datetime.strptime(self._entry.get().strip(), "%d.%m.%Y")
            return dt.date()
        except (ValueError, AttributeError):
            return None

    def set_date(self, d):
        self._selected_date = d
        if d:
            self._entry.delete(0, "end")
            self._entry.insert(0, d.strftime("%d.%m.%Y"))
        else:
            self._entry.delete(0, "end")

    def clear(self):
        self._selected_date = None
        self._entry.delete(0, "end")
        if self._on_date_selected:
            self._on_date_selected(None)


# ─────────────────────────────────────────────
# 9. TabView
# ─────────────────────────────────────────────

class TabView(ctk.CTkTabview):
    def __init__(self, parent, closable=False, reorderable=False, **kwargs):
        super().__init__(parent, **kwargs)
        self._closable = closable
        self._reorderable = reorderable
        self._tab_icons = {}
        self._tab_badges = {}
        self._tab_name_to_text = {}

    def add_tab(self, text, icon=None):
        name = text
        display = f"{icon} {text}" if icon else text
        self._tab_name_to_text[name] = text
        super().add(name)
        tab_btn = self._get_tab_button(name)
        if tab_btn:
            tab_btn.configure(text=display)

        if icon:
            self._tab_icons[name] = icon

        if self._closable:
            self._add_close_button(name)

        return name

    def _add_close_button(self, tab_name):
        tab_btn = self._get_tab_button(tab_name)
        if not tab_btn:
            return

        tab_btn.update_idletasks()

        close_btn = ctk.CTkButton(
            tab_btn, text="X", width=16, height=16,
            fg_color="transparent", hover_color=DANGER,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=8),
            corner_radius=8,
            command=lambda t=tab_name: self._close_tab(t)
        )
        close_btn.pack(side="right", padx=(2, 4), pady=0)

    def _get_tab_button(self, tab_name):
        for child in self.winfo_children():
            if hasattr(child, '_segmented_button') and hasattr(child._segmented_button, '_buttons_dict'):
                buttons = child._segmented_button._buttons_dict
                if tab_name in buttons:
                    return buttons[tab_name]
            if isinstance(child, ctk.CTkFrame):
                for sub in child.winfo_children():
                    if hasattr(sub, '_segmented_button') and hasattr(sub._segmented_button, '_buttons_dict'):
                        buttons = sub._segmented_button._buttons_dict
                        if tab_name in buttons:
                            return buttons[tab_name]
        return None

    def _close_tab(self, tab_name):
        if self._closable:
            try:
                self.delete(tab_name)
            except Exception:
                pass
            if tab_name in self._tab_icons:
                del self._tab_icons[tab_name]
            if tab_name in self._tab_badges:
                del self._tab_badges[tab_name]
            if tab_name in self._tab_name_to_text:
                del self._tab_name_to_text[tab_name]

    def set_badge(self, tab_name, count):
        self._tab_badges[tab_name] = count
        tab_btn = self._get_tab_button(tab_name)
        if tab_btn:
            text = self._tab_name_to_text.get(tab_name, tab_name)
            icon = self._tab_icons.get(tab_name, "")
            icon_str = f"{icon} " if icon else ""
            badge_str = f" ({count})" if count > 0 else ""
            tab_btn.configure(text=f"{icon_str}{text}{badge_str}")

    def clear_badge(self, tab_name):
        self.set_badge(tab_name, 0)

    def get_tab_text(self, tab_name):
        return self._tab_name_to_text.get(tab_name, tab_name)

    def rename_tab(self, tab_name, new_text, icon=None):
        self._tab_name_to_text[tab_name] = new_text
        if icon:
            self._tab_icons[tab_name] = icon
        display_icon = self._tab_icons.get(tab_name, "")
        icon_str = f"{display_icon} " if display_icon else ""
        badge_count = self._tab_badges.get(tab_name, 0)
        badge_str = f" ({badge_count})" if badge_count > 0 else ""
        tab_btn = self._get_tab_button(tab_name)
        if tab_btn:
            tab_btn.configure(text=f"{icon_str}{new_text}{badge_str}")

    def tab_count(self):
        return len(self._tab_name_to_text)

    def tab_names(self):
        return list(self._tab_name_to_text.keys())


# ─────────────────────────────────────────────
# 10. LoadingOverlay
# ─────────────────────────────────────────────

SPINNER_CHARS = ["\u27f3", "\u27f2", "\u21bb", "\u21ba"]

class LoadingOverlay(ctk.CTkFrame):
    def __init__(self, parent, message="Y\u00fckleniyor...", spinner_speed=150, **kwargs):
        super().__init__(
            parent, fg_color="#1a1a2e", corner_radius=0,
            **kwargs
        )
        self._message = message
        self._spinner_speed = spinner_speed
        self._spinner_index = 0
        self._animating = False
        self._after_id = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        container.grid(row=0, column=0)

        self._spinner_label = ctk.CTkLabel(
            container, text=SPINNER_CHARS[0],
            font=ctk.CTkFont(size=32), text_color=PRIMARY
        )
        self._spinner_label.pack(padx=40, pady=(30, 8))

        self._msg_label = ctk.CTkLabel(
            container, text=message,
            font=ctk.CTkFont(size=13), text_color=TEXT_DARK
        )
        self._msg_label.pack(padx=40, pady=(0, 30))

    def show(self):
        self._animating = True
        self._start_spinner()
        if self.master:
            self.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.lift()

    def hide(self):
        self._animating = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        try:
            self.place_forget()
        except Exception:
            pass

    def _start_spinner(self):
        if not self._animating:
            return
        try:
            self._spinner_index = (self._spinner_index + 1) % len(SPINNER_CHARS)
            if self._spinner_label and self._spinner_label.winfo_exists():
                self._spinner_label.configure(text=SPINNER_CHARS[self._spinner_index])
            self._after_id = self.after(self._spinner_speed, self._start_spinner)
        except Exception:
            pass

    def set_message(self, message):
        self._message = message
        if self._msg_label and self._msg_label.winfo_exists():
            self._msg_label.configure(text=message)

    def destroy(self):
        self._animating = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        super().destroy()
