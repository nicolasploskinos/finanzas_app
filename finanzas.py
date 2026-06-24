import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, date
from collections import defaultdict
from tkcalendar import DateEntry

DATA_FILE = os.path.join(os.path.dirname(__file__), "finanzas_data.json")

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

COLORES = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "surface2": "#313148",
    "accent_green": "#4ade80",
    "accent_red": "#f87171",
    "accent_blue": "#60a5fa",
    "accent_yellow": "#fbbf24",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "border": "#3f3f5a",
}


def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


class FinanzasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Finanzas")
        self.root.geometry("1100x720")
        self.root.configure(bg=COLORES["bg"])
        self.root.resizable(True, True)

        self.datos = cargar_datos()
        self.filtro_mes = tk.StringVar(value="Todos")
        self.filtro_anio = tk.StringVar(value=str(date.today().year))
        self.filtro_tipo = tk.StringVar(value="Todos")
        self.filtro_cat = tk.StringVar(value="Todas")

        self._configurar_estilos()
        self._construir_ui()
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORES["bg"], foreground=COLORES["text"],
                        fieldbackground=COLORES["surface2"], borderwidth=0)
        style.configure("TFrame", background=COLORES["bg"])
        style.configure("Surface.TFrame", background=COLORES["surface"])
        style.configure("TLabel", background=COLORES["bg"], foreground=COLORES["text"],
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=COLORES["bg"], foreground=COLORES["text"],
                        font=("Segoe UI", 18, "bold"))
        style.configure("Card.TLabel", background=COLORES["surface"], foreground=COLORES["text"],
                        font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=COLORES["surface"],
                        foreground=COLORES["text_muted"], font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background=COLORES["surface"],
                        font=("Segoe UI", 20, "bold"))
        style.configure("Green.CardValue.TLabel", foreground=COLORES["accent_green"])
        style.configure("Red.CardValue.TLabel", foreground=COLORES["accent_red"])
        style.configure("Blue.CardValue.TLabel", foreground=COLORES["accent_blue"])

        style.configure("TButton", background=COLORES["accent_blue"], foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(12, 8))
        style.map("TButton", background=[("active", "#3b82f6"), ("pressed", "#2563eb")])

        style.configure("Danger.TButton", background=COLORES["accent_red"], foreground="white",
                        font=("Segoe UI", 9, "bold"), borderwidth=0, padding=(8, 5))
        style.map("Danger.TButton", background=[("active", "#ef4444")])

        style.configure("TCombobox", fieldbackground=COLORES["surface2"],
                        background=COLORES["surface2"], foreground=COLORES["text"],
                        arrowcolor=COLORES["text_muted"], borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", COLORES["surface2"])],
                  foreground=[("readonly", COLORES["text"])])

        style.configure("Treeview", background=COLORES["surface2"], foreground=COLORES["text"],
                        fieldbackground=COLORES["surface2"], rowheight=32,
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background=COLORES["surface"],
                        foreground=COLORES["text_muted"], font=("Segoe UI", 10, "bold"),
                        borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", "#3b4a6b")],
                  foreground=[("selected", COLORES["text"])])
        style.map("Treeview.Heading", background=[("active", COLORES["border"])])

        style.configure("TSeparator", background=COLORES["border"])

    def _construir_ui(self):
        # Header
        header = tk.Frame(self.root, bg=COLORES["surface"], height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(header, text="💰 Control de Finanzas", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 16, "bold")).pack(side="left", padx=20, pady=15)

        hoy = date.today()
        today_str = f"{hoy.day} de {MESES[hoy.month - 1].lower()} de {hoy.year}"
        tk.Label(header, text=today_str, bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 10)).pack(side="right", padx=20)

        # Main layout
        main = tk.Frame(self.root, bg=COLORES["bg"])
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Left panel: form
        left = tk.Frame(main, bg=COLORES["surface"], bd=0, relief="flat")
        left.pack(side="left", fill="y", padx=(0, 10), ipadx=10, ipady=10)

        self._construir_formulario(left)

        # Right panel: filters + table + balances
        right = tk.Frame(main, bg=COLORES["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._construir_tarjetas_balance(right)
        self._construir_filtros(right)
        self._construir_tabla(right)

    def _construir_formulario(self, parent):
        tk.Label(parent, text="Nueva Transacción", bg=COLORES["surface"],
                 fg=COLORES["text"], font=("Segoe UI", 13, "bold")).pack(pady=(15, 5), padx=15, anchor="w")

        sep = tk.Frame(parent, bg=COLORES["border"], height=1)
        sep.pack(fill="x", padx=15, pady=5)

        form = tk.Frame(parent, bg=COLORES["surface"])
        form.pack(fill="x", padx=15, pady=5)

        def label(text):
            tk.Label(form, text=text, bg=COLORES["surface"], fg=COLORES["text_muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))

        # Tipo
        label("Tipo")
        self.tipo_var = tk.StringVar(value="Gasto")
        tipo_frame = tk.Frame(form, bg=COLORES["surface"])
        tipo_frame.pack(fill="x")
        self.btn_gasto = tk.Button(tipo_frame, text="Gasto", bg=COLORES["accent_red"],
                                   fg="white", font=("Segoe UI", 10, "bold"), bd=0,
                                   relief="flat", padx=15, pady=6, cursor="hand2",
                                   command=lambda: self._set_tipo("Gasto"))
        self.btn_gasto.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.btn_ingreso = tk.Button(tipo_frame, text="Ingreso", bg=COLORES["surface2"],
                                     fg=COLORES["text_muted"], font=("Segoe UI", 10, "bold"), bd=0,
                                     relief="flat", padx=15, pady=6, cursor="hand2",
                                     command=lambda: self._set_tipo("Ingreso"))
        self.btn_ingreso.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # Monto
        label("Monto ($)")
        self.monto_var = tk.StringVar()
        monto_entry = tk.Entry(form, textvariable=self.monto_var, bg=COLORES["surface2"],
                               fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                               insertbackground=COLORES["text"], relief="flat")
        monto_entry.pack(fill="x", ipady=7)
        monto_frame = tk.Frame(form, bg=COLORES["accent_blue"], height=2)
        monto_frame.pack(fill="x")

        # Fecha
        label("Fecha")
        self.fecha_entry = DateEntry(
            form,
            width=20,
            date_pattern="dd/mm/yyyy",
            locale="es_ES",
            background=COLORES["accent_blue"],
            foreground="white",
            selectbackground=COLORES["accent_blue"],
            selectforeground="white",
            normalbackground=COLORES["surface2"],
            normalforeground=COLORES["text"],
            weekendbackground=COLORES["surface2"],
            weekendforeground=COLORES["accent_yellow"],
            headersbackground=COLORES["surface"],
            headersforeground=COLORES["text_muted"],
            othermonthbackground=COLORES["bg"],
            othermonthforeground=COLORES["border"],
            font=("Segoe UI", 11),
        )
        self.fecha_entry.set_date(date.today())
        self.fecha_entry.pack(fill="x", ipady=5)

        # Categoría
        label("Categoría")
        self.cat_var = tk.StringVar()
        cat_entry = tk.Entry(form, textvariable=self.cat_var, bg=COLORES["surface2"],
                             fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                             insertbackground=COLORES["text"], relief="flat")
        cat_entry.pack(fill="x", ipady=7)
        tk.Frame(form, bg=COLORES["accent_blue"], height=2).pack(fill="x")

        # Descripción
        label("Descripción")
        self.desc_var = tk.StringVar()
        desc_entry = tk.Entry(form, textvariable=self.desc_var, bg=COLORES["surface2"],
                              fg=COLORES["text"], font=("Segoe UI", 11), bd=0,
                              insertbackground=COLORES["text"], relief="flat")
        desc_entry.pack(fill="x", ipady=7)
        tk.Frame(form, bg=COLORES["accent_blue"], height=2).pack(fill="x")

        # Botón agregar
        tk.Frame(form, bg=COLORES["surface"], height=15).pack()
        btn_agregar = tk.Button(form, text="+ Agregar Transacción",
                                bg=COLORES["accent_blue"], fg="white",
                                font=("Segoe UI", 11, "bold"), bd=0, relief="flat",
                                pady=10, cursor="hand2", command=self._agregar_transaccion)
        btn_agregar.pack(fill="x")
        btn_agregar.bind("<Enter>", lambda e: btn_agregar.config(bg="#3b82f6"))
        btn_agregar.bind("<Leave>", lambda e: btn_agregar.config(bg=COLORES["accent_blue"]))

        # Info
        tk.Frame(parent, bg=COLORES["surface"], height=10).pack()
        self.info_label = tk.Label(parent, text="", bg=COLORES["surface"],
                                   fg=COLORES["accent_green"], font=("Segoe UI", 9),
                                   wraplength=220)
        self.info_label.pack(padx=15, anchor="w")

    def _set_tipo(self, tipo):
        self.tipo_var.set(tipo)
        if tipo == "Gasto":
            self.btn_gasto.config(bg=COLORES["accent_red"], fg="white")
            self.btn_ingreso.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])
        else:
            self.btn_ingreso.config(bg=COLORES["accent_green"], fg="#1e1e2e")
            self.btn_gasto.config(bg=COLORES["surface2"], fg=COLORES["text_muted"])

    def _construir_tarjetas_balance(self, parent):
        frame = tk.Frame(parent, bg=COLORES["bg"])
        frame.pack(fill="x", pady=(0, 10))

        self.card_ingresos = self._tarjeta(frame, "Ingresos", "$0.00", COLORES["accent_green"])
        self.card_gastos = self._tarjeta(frame, "Gastos", "$0.00", COLORES["accent_red"])
        self.card_balance = self._tarjeta(frame, "Balance", "$0.00", COLORES["accent_blue"])

    def _tarjeta(self, parent, titulo, valor, color):
        card = tk.Frame(parent, bg=COLORES["surface"], bd=0, relief="flat")
        card.pack(side="left", fill="both", expand=True, padx=4, ipady=12, ipadx=10)

        tk.Label(card, text=titulo.upper(), bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

        val_label = tk.Label(card, text=valor, bg=COLORES["surface"],
                             fg=color, font=("Segoe UI", 22, "bold"))
        val_label.pack(anchor="w", padx=12, pady=(0, 10))
        return val_label

    def _construir_filtros(self, parent):
        frame = tk.Frame(parent, bg=COLORES["surface"])
        frame.pack(fill="x", pady=(0, 10), ipady=6)

        tk.Label(frame, text="Filtros:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(12, 8), pady=8)

        # Mes
        tk.Label(frame, text="Mes:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        mes_combo = ttk.Combobox(frame, textvariable=self.filtro_mes,
                                  values=["Todos"] + MESES, state="readonly",
                                  width=10, font=("Segoe UI", 9))
        mes_combo.pack(side="left", padx=(0, 10))
        mes_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Año
        anios = [str(y) for y in range(2020, date.today().year + 2)]
        tk.Label(frame, text="Año:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        anio_combo = ttk.Combobox(frame, textvariable=self.filtro_anio,
                                   values=anios, state="readonly",
                                   width=7, font=("Segoe UI", 9))
        anio_combo.pack(side="left", padx=(0, 10))
        anio_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Tipo
        tk.Label(frame, text="Tipo:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        tipo_combo = ttk.Combobox(frame, textvariable=self.filtro_tipo,
                                   values=["Todos", "Gasto", "Ingreso"], state="readonly",
                                   width=8, font=("Segoe UI", 9))
        tipo_combo.pack(side="left", padx=(0, 10))
        tipo_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Categoría
        tk.Label(frame, text="Categoría:", bg=COLORES["surface"],
                 fg=COLORES["text_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.cat_filtro_combo = ttk.Combobox(frame, textvariable=self.filtro_cat,
                                              values=["Todas"], state="readonly",
                                              width=13, font=("Segoe UI", 9))
        self.cat_filtro_combo.pack(side="left", padx=(0, 10))
        self.cat_filtro_combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Botón limpiar filtros
        tk.Button(frame, text="Mostrar todos", bg=COLORES["surface2"], fg=COLORES["text_muted"],
                  font=("Segoe UI", 9), bd=0, relief="flat", padx=8, pady=4, cursor="hand2",
                  command=self._limpiar_filtros).pack(side="left", padx=4)

    def _construir_tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES["surface"])
        frame.pack(fill="both", expand=True)

        # Barra de acción
        action_bar = tk.Frame(frame, bg=COLORES["surface"])
        action_bar.pack(fill="x", padx=12, pady=(10, 5))

        self.count_label = tk.Label(action_bar, text="0 transacciones",
                                     bg=COLORES["surface"], fg=COLORES["text_muted"],
                                     font=("Segoe UI", 9))
        self.count_label.pack(side="left")

        tk.Button(action_bar, text="Eliminar seleccionado",
                  bg=COLORES["accent_red"], fg="white",
                  font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=self._eliminar_seleccionado).pack(side="right")

        # Tabla
        cols = ("Fecha", "Tipo", "Categoría", "Descripción", "Monto")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  selectmode="browse")

        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Categoría", text="Categoría")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Monto", text="Monto")

        self.tree.column("Fecha", width=100, anchor="center")
        self.tree.column("Tipo", width=80, anchor="center")
        self.tree.column("Categoría", width=130, anchor="center")
        self.tree.column("Descripción", width=250)
        self.tree.column("Monto", width=110, anchor="e")

        # Scrollbar
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb.pack(side="right", fill="y", pady=(0, 12), padx=(0, 12))

        # Tags de color por tipo
        self.tree.tag_configure("ingreso", foreground=COLORES["accent_green"])
        self.tree.tag_configure("gasto", foreground=COLORES["accent_red"])

    def _agregar_transaccion(self):
        monto_str = self.monto_var.get().strip().replace(",", ".")
        cat = self.cat_var.get()
        desc = self.desc_var.get().strip()
        tipo = self.tipo_var.get()

        if not monto_str:
            messagebox.showerror("Error", "Ingresá un monto.")
            return
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número positivo.")
            return

        fecha = self.fecha_entry.get_date()

        transaccion = {
            "id": int(datetime.now().timestamp() * 1000),
            "tipo": tipo,
            "monto": monto,
            "fecha": fecha.isoformat(),
            "categoria": cat,
            "descripcion": desc,
        }

        self.datos.append(transaccion)
        guardar_datos(self.datos)

        self.monto_var.set("")
        self.desc_var.set("")
        self.fecha_entry.set_date(date.today())

        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

        signo = "+" if tipo == "Ingreso" else "-"
        self.info_label.config(
            text=f"✓ {tipo} de {signo}${monto:.2f} agregado.",
            fg=COLORES["accent_green"] if tipo == "Ingreso" else COLORES["accent_red"]
        )
        self.root.after(3000, lambda: self.info_label.config(text=""))

    def _datos_filtrados(self):
        mes_sel = self.filtro_mes.get()
        anio_sel = self.filtro_anio.get()
        tipo_sel = self.filtro_tipo.get()
        cat_sel = self.filtro_cat.get()

        resultado = []
        for t in self.datos:
            f = date.fromisoformat(t["fecha"])
            if mes_sel != "Todos" and MESES[f.month - 1] != mes_sel:
                continue
            if anio_sel and str(f.year) != anio_sel:
                continue
            if tipo_sel != "Todos" and t["tipo"] != tipo_sel:
                continue
            if cat_sel != "Todas" and t.get("categoria", "") != cat_sel:
                continue
            resultado.append(t)

        resultado.sort(key=lambda x: x["fecha"], reverse=True)
        return resultado

    def _actualizar_categorias_filtro(self):
        cats = sorted({t.get("categoria", "") for t in self.datos if t.get("categoria", "")})
        self.cat_filtro_combo.config(values=["Todas"] + cats)
        if self.filtro_cat.get() not in ["Todas"] + cats:
            self.filtro_cat.set("Todas")

    def _actualizar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtrados = self._datos_filtrados()
        self.count_label.config(text=f"{len(filtrados)} transacciones")

        for t in filtrados:
            f = date.fromisoformat(t["fecha"])
            fecha_fmt = f.strftime("%d/%m/%Y")
            signo = "+" if t["tipo"] == "Ingreso" else "-"
            monto_fmt = f"{signo}${t['monto']:,.2f}"
            tag = "ingreso" if t["tipo"] == "Ingreso" else "gasto"
            self.tree.insert("", "end",
                             values=(fecha_fmt, t["tipo"], t["categoria"],
                                     t["descripcion"], monto_fmt),
                             tags=(tag,),
                             iid=str(t["id"]))

    def _actualizar_balances(self):
        filtrados = self._datos_filtrados()
        total_ingresos = sum(t["monto"] for t in filtrados if t["tipo"] == "Ingreso")
        total_gastos = sum(t["monto"] for t in filtrados if t["tipo"] == "Gasto")
        balance = total_ingresos - total_gastos

        self.card_ingresos.config(text=f"+${total_ingresos:,.2f}")
        self.card_gastos.config(text=f"-${total_gastos:,.2f}")

        color_balance = COLORES["accent_green"] if balance >= 0 else COLORES["accent_red"]
        signo = "+" if balance >= 0 else ""
        self.card_balance.config(text=f"{signo}${balance:,.2f}", fg=color_balance)

    def _aplicar_filtros(self):
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

    def _limpiar_filtros(self):
        self.filtro_mes.set("Todos")
        self.filtro_anio.set(str(date.today().year))
        self.filtro_tipo.set("Todos")
        self.filtro_cat.set("Todas")
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()

    def _eliminar_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleccioná una transacción para eliminar.")
            return
        iid = int(sel[0])
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta transacción?"):
            return
        self.datos = [t for t in self.datos if t["id"] != iid]
        guardar_datos(self.datos)
        self._actualizar_categorias_filtro()
        self._actualizar_tabla()
        self._actualizar_balances()


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanzasApp(root)
    root.mainloop()
