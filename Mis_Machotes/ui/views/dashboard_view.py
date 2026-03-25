import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from datetime import datetime

from ui.components import BaseView, CURRENT_THEME

class DashboardView(BaseView):
    title = "Santuario del Reino"
    subtitle = "Vista general del inventario, hallazgos y señales clave del negocio."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(3, weight=1)
        self.metric_labels = {}
        self.chart_canvas = None
        self.summary_tree = None

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        self.filter_var = ctk.StringVar(value="Todos")
        self.segment = ctk.CTkSegmentedButton(controls, values=["Todos", "Disponibles", "Usados", "XML"], variable=self.filter_var, command=lambda _: self.refresh(), selected_color=CURRENT_THEME["gold"], selected_hover_color=CURRENT_THEME["gold_hover"], unselected_color=CURRENT_THEME["panel_alt"], unselected_hover_color=CURRENT_THEME["panel"])
        self.segment.pack(anchor="w")
        ctk.CTkButton(controls, text="Exportar Dashboard", width=150, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"], command=self.export_dashboard_snapshot).pack(anchor="e")
        period_row = ctk.CTkFrame(controls, fg_color="transparent")
        period_row.pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(period_row, text="Periodo:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(0, 8))
        self.period_var = ctk.StringVar(value="Todo")
        self.custom_range = None
        self.period_segment = ctk.CTkSegmentedButton(
            period_row,
            values=["Todo", "Hoy", "7d", "30d", "90d", "Rango"],
            variable=self.period_var,
            command=self.on_period_change,
            selected_color=CURRENT_THEME["gold"],
            selected_hover_color=CURRENT_THEME["gold_hover"],
            unselected_color=CURRENT_THEME["panel_alt"],
            unselected_hover_color=CURRENT_THEME["panel"],
        )
        self.period_segment.pack(side="left")
        ctk.CTkLabel(period_row, text="Desde:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(14, 4))
        self.from_date_entry = ctk.CTkEntry(period_row, width=105, placeholder_text="YYYY-MM-DD")
        self.from_date_entry.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(period_row, text="Hasta:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(4, 4))
        self.to_date_entry = ctk.CTkEntry(period_row, width=105, placeholder_text="YYYY-MM-DD")
        self.to_date_entry.pack(side="left", padx=(0, 6))
        ctk.CTkButton(period_row, text="Aplicar rango", width=110, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"], command=self.apply_custom_range).pack(side="left", padx=(4, 0))
        ctk.CTkButton(period_row, text="Limpiar", width=80, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.clear_custom_range).pack(side="left", padx=(6, 0))

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.grid(row=2, column=0, sticky="ew", padx=18)
        for idx in range(4):
            metrics.grid_columnconfigure(idx, weight=1)

        self._metric_card(metrics, 0, "Rupias Totales", "$0.00", "total")
        self._metric_card(metrics, 1, "Reliquias Activas", "0", "pieces")
        self._metric_card(metrics, 2, "Participación Rubro", "0%", "share")
        self._metric_card(metrics, 3, "Ticket Promedio", "$0.00", "avg")
        self.compare_label = ctk.CTkLabel(self, text="Comparativo: sin periodo seleccionado.", text_color=CURRENT_THEME["muted"])
        self.compare_label.grid(row=2, column=0, sticky="e", padx=24, pady=(94, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, sticky="nsew", padx=18, pady=(12, 18))
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        # Upper charts row
        charts_row = ctk.CTkFrame(content, fg_color="transparent")
        charts_row.grid(row=0, column=0, columnspan=2, sticky="nsew")
        charts_row.grid_rowconfigure(0, weight=1)
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        pie_card = ctk.CTkFrame(charts_row, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        pie_card.grid_rowconfigure(1, weight=1)
        pie_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pie_card, text="Distribución de Sucursales", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.chart_container = ctk.CTkFrame(pie_card, fg_color="transparent")
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        bar_card = ctk.CTkFrame(charts_row, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        bar_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        bar_card.grid_rowconfigure(1, weight=1)
        bar_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bar_card, text="Top 10 Modelos (Stock)", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.bar_chart_container = ctk.CTkFrame(bar_card, fg_color="transparent")
        self.bar_chart_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.bar_chart_canvas = None

        # Lower summary row
        summary_card = ctk.CTkFrame(content, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        summary_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(18, 0))
        summary_card.grid_rowconfigure(1, weight=1)
        summary_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(summary_card, text="Resumen por Sucursal (Doble clic para ver inventario)", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.summary_tree = self.app.create_treeview(summary_card, [
            ("sucursal", "Sucursal", 160),
            ("cantidad", "Cantidad", 100),
            ("porcentaje", "% del total", 110),
            ("total", "Total", 140),
        ])
        self.summary_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.summary_tree.bind("<Double-1>", self.on_summary_double_click)

    def _metric_card(self, parent, column, title, value, key):
        card = ctk.CTkFrame(parent, fg_color=CURRENT_THEME["panel_alt"], corner_radius=16, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=0, column=column, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=title, text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(12, 0))
        label = ctk.CTkLabel(card, text=value, text_color=CURRENT_THEME["text"], font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(anchor="w", padx=16, pady=(2, 14))
        self.metric_labels[key] = label

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return

        rep_df = self._filter_by_period(inventory.get("reporte"))
        us_df = self._filter_by_period(inventory.get("usados"))
        xml_df = self._filter_by_period(inventory.get("xml"))

        dfs = []
        filtro = self.filter_var.get()
        if filtro in ["Todos", "Disponibles"]: dfs.append(rep_df)
        if filtro in ["Todos", "Usados"]: dfs.append(us_df)
        if filtro in ["Todos", "XML"]: dfs.append(xml_df)

        total_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True) if any(not df.empty for df in dfs) else pd.DataFrame()
        total_money = pd.to_numeric(total_df.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not total_df.empty else 0
        total_pieces = len(total_df)

        global_total = len(rep_df) + len(us_df) + len(xml_df)
        share = (total_pieces / global_total * 100) if global_total else 0
        avg_ticket = (total_money / total_pieces) if total_pieces else 0

        self.metric_labels["total"].configure(text=f"${total_money:,.2f}")
        self.metric_labels["pieces"].configure(text=str(total_pieces))

        self.metric_labels["share"].configure(text=f"{share:.1f}%")
        if share < 25:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["danger"])
        elif share < 60:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["warning"])
        else:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["emerald"])

        self.metric_labels["avg"].configure(text=f"${avg_ticket:,.2f}")
        self._update_period_comparison(inventory, filtro, total_money, total_pieces)

        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if not total_df.empty and "SUCURSAL" in total_df.columns:
            top = total_df.copy()
            top["TOTAL"] = pd.to_numeric(top.get("TOTAL", 0), errors="coerce").fillna(0)
            top = top.groupby("SUCURSAL", as_index=False).agg(
                CANTIDAD=("SUCURSAL", "size"),
                TOTAL=("TOTAL", "sum")
            ).sort_values("TOTAL", ascending=False)

            total_count = top["CANTIDAD"].sum() if not top.empty else 0
            for _, row in top.iterrows():
                pct = (row["CANTIDAD"] / total_count * 100) if total_count else 0
                self.summary_tree.insert("", "end", values=(row["SUCURSAL"], str(row["CANTIDAD"]), f"{pct:.1f}%", f"${row['TOTAL']:,.2f}"))

        self.draw_chart(total_df)

    def on_period_change(self, selected_period):
        now = pd.Timestamp.now().normalize()
        if selected_period == "Hoy":
            start = now
            end = now
            self.from_date_entry.delete(0, "end")
            self.from_date_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.to_date_entry.delete(0, "end")
            self.to_date_entry.insert(0, end.strftime("%Y-%m-%d"))
        elif selected_period in {"7d", "30d", "90d"}:
            days = int(selected_period.replace("d", ""))
            start = now - pd.Timedelta(days=days)
            end = now
            self.from_date_entry.delete(0, "end")
            self.from_date_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.to_date_entry.delete(0, "end")
            self.to_date_entry.insert(0, end.strftime("%Y-%m-%d"))
        elif selected_period == "Todo":
            self.custom_range = None
            self.from_date_entry.delete(0, "end")
            self.to_date_entry.delete(0, "end")
        self.refresh()

    def apply_custom_range(self):
        start_str = self.from_date_entry.get().strip()
        end_str = self.to_date_entry.get().strip()
        if not start_str or not end_str:
            messagebox.showwarning("Rango incompleto", "Ingresa fecha inicial y final en formato YYYY-MM-DD.")
            return
        try:
            start = pd.to_datetime(start_str, format="%Y-%m-%d")
            end = pd.to_datetime(end_str, format="%Y-%m-%d")
        except Exception:
            messagebox.showwarning("Formato inválido", "Usa formato YYYY-MM-DD. Ejemplo: 2026-03-24")
            return
        if end < start:
            messagebox.showwarning("Rango inválido", "La fecha final no puede ser menor que la inicial.")
            return
        self.custom_range = (start.normalize(), end.normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        self.period_var.set("Rango")
        self.refresh()

    def clear_custom_range(self):
        self.custom_range = None
        self.from_date_entry.delete(0, "end")
        self.to_date_entry.delete(0, "end")
        if self.period_var.get() == "Rango":
            self.period_var.set("Todo")
        self.refresh()

    def _filter_by_period(self, df):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df
        period = self.period_var.get()
        if period == "Todo":
            return df
        if "FECHA ACTUALIZACION" not in df.columns:
            return df
        now = pd.Timestamp.now()
        if period == "Hoy":
            start = now.normalize()
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
            return df[(fechas >= start) & (fechas <= end)]
        if period == "Rango":
            if not self.custom_range:
                return df
            start, end = self.custom_range
            fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
            return df[(fechas >= start) & (fechas <= end)]

        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period)
        if not days:
            return df
        tmp = df.copy()
        fechas = pd.to_datetime(tmp["FECHA ACTUALIZACION"], errors="coerce")
        cutoff = now - pd.Timedelta(days=days)
        return tmp[fechas >= cutoff]

    def _get_period_bounds(self):
        now = pd.Timestamp.now()
        period = self.period_var.get()
        if period == "Todo":
            return None
        if period == "Hoy":
            start = now.normalize()
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            return start, end
        if period in {"7d", "30d", "90d"}:
            days = int(period.replace("d", ""))
            end = now
            start = end - pd.Timedelta(days=days)
            return start, end
        if period == "Rango" and self.custom_range:
            return self.custom_range
        return None

    def _filter_by_bounds(self, df, bounds):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df
        if "FECHA ACTUALIZACION" not in df.columns:
            return df
        start, end = bounds
        fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
        return df[(fechas >= start) & (fechas <= end)]

    def _update_period_comparison(self, inventory, filtro, current_money, current_pieces):
        bounds = self._get_period_bounds()
        if not bounds:
            self.compare_label.configure(text="Comparativo: selecciona Hoy/7d/30d/90d/Rango.", text_color=CURRENT_THEME["muted"])
            return
        start, end = bounds
        duration = end - start
        prev_end = start - pd.Timedelta(seconds=1)
        prev_start = prev_end - duration
        prev_bounds = (prev_start, prev_end)

        rep_prev = self._filter_by_bounds(inventory.get("reporte"), prev_bounds)
        us_prev = self._filter_by_bounds(inventory.get("usados"), prev_bounds)
        xml_prev = self._filter_by_bounds(inventory.get("xml"), prev_bounds)
        dfs_prev = []
        if filtro in ["Todos", "Disponibles"]: dfs_prev.append(rep_prev)
        if filtro in ["Todos", "Usados"]: dfs_prev.append(us_prev)
        if filtro in ["Todos", "XML"]: dfs_prev.append(xml_prev)
        prev_df = pd.concat([df for df in dfs_prev if not df.empty], ignore_index=True) if any(not df.empty for df in dfs_prev) else pd.DataFrame()
        prev_money = pd.to_numeric(prev_df.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not prev_df.empty else 0
        prev_pieces = len(prev_df)

        def pct_delta(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return ((curr - prev) / prev) * 100

        delta_money = pct_delta(current_money, prev_money)
        delta_pieces = pct_delta(current_pieces, prev_pieces)

        def format_trend(delta):
            if delta > 0:
                return f"▲ +{delta:.1f}%"
            elif delta < 0:
                return f"▼ {delta:.1f}%"
            return f"► {delta:.1f}%"

        trend_pieces = format_trend(delta_pieces)
        trend_money = format_trend(delta_money)

        if delta_money >= 0 and delta_pieces >= 0:
            color = CURRENT_THEME["emerald"]
        elif delta_money < 0 and delta_pieces < 0:
            color = CURRENT_THEME["danger"]
        else:
            color = CURRENT_THEME["warning"]

        self.compare_label.configure(
            text=f"Vs periodo anterior → Piezas: {trend_pieces} · Total: {trend_money}",
            text_color=color,
        )

    def on_summary_double_click(self, event):
        selected = self.summary_tree.selection()
        if not selected:
            return
        item = self.summary_tree.item(selected[0])
        sucursal = item["values"][0]
        if sucursal:
            msg = f"¿Ir al inventario y ver piezas de la sucursal '{sucursal}'?"
            if messagebox.askyesno("Ver Inventario", msg):
                self.app.show_view("inventario")
                inv_view = self.app.views["inventario"]
                inv_view.clear_filters()

                state_map = {"Disponibles": "Disponibles", "Usados": "Usados", "XML": "XML", "Todos": "Disponibles"}
                current_state = self.filter_var.get()
                inv_view.tabview.set(state_map.get(current_state, "Disponibles"))

                # Deselect all except the clicked one
                for var in inv_view.sucursal_opt.variables.values():
                    var.set(0)
                if sucursal in inv_view.sucursal_opt.variables:
                    inv_view.sucursal_opt.variables[sucursal].set(1)
                inv_view.sucursal_opt.update_text()

                inv_view.refresh()

    def export_dashboard_snapshot(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("PDF", "*.pdf")],
            title="Exportar Dashboard (Excel/PDF)",
            initialfile="Dashboard_Resumen.xlsx",
        )
        if not out_path:
            return
        try:
            kpis = {
                "Rupias Totales": self.metric_labels["total"].cget("text"),
                "Reliquias Activas": self.metric_labels["pieces"].cget("text"),
                "Participación Rubro": self.metric_labels["share"].cget("text"),
                "Ticket Promedio": self.metric_labels["avg"].cget("text"),
                "Comparativo": self.compare_label.cget("text"),
            }
            filters = {
                "Filtro estado": self.filter_var.get(),
                "Periodo": self.period_var.get(),
                "Desde": self.from_date_entry.get() or "-",
                "Hasta": self.to_date_entry.get() or "-",
                "Exportado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            rows = []
            for item_id in self.summary_tree.get_children():
                values = self.summary_tree.item(item_id, "values")
                rows.append(values)
            summary_df = pd.DataFrame(rows, columns=["Sucursal", "Cantidad", "% del total", "Total"])
            kpi_df = pd.DataFrame([kpis])
            filters_df = pd.DataFrame([filters])

            if out_path.lower().endswith(".pdf"):
                self._export_dashboard_pdf(out_path, kpi_df, summary_df, filters_df)
            else:
                with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                    kpi_df.to_excel(writer, sheet_name="KPIs", index=False)
                    summary_df.to_excel(writer, sheet_name="Sucursales", index=False)
                    filters_df.to_excel(writer, sheet_name="Filtros", index=False)
            self.app.log(f"Dashboard exportado: {out_path}")
            messagebox.showinfo("Exportación completada", f"Dashboard exportado en:\n{out_path}")
        except Exception as exc:
            self.app.log(f"Error exportando dashboard: {exc}")
            import traceback
            self.app.log(traceback.format_exc())
            messagebox.showerror("Error exportando", f"No se pudo exportar dashboard.\n\n{exc}")

    def _export_dashboard_pdf(self, out_path, kpi_df, summary_df, filters_df):
        with PdfPages(out_path) as pdf:
            fig1 = Figure(figsize=(8.27, 11.69), dpi=120, facecolor="white")
            ax1 = fig1.add_subplot(111)
            ax1.axis("off")
            ax1.text(0.03, 0.97, "Dashboard - Resumen", fontsize=16, fontweight="bold", va="top")

            y = 0.90
            for col in filters_df.columns:
                val = str(filters_df.iloc[0][col])
                ax1.text(0.03, y, f"{col}: {val}", fontsize=10, va="top")
                y -= 0.04

            y -= 0.02
            ax1.text(0.03, y, "KPIs", fontsize=12, fontweight="bold", va="top")
            y -= 0.03
            for col in kpi_df.columns:
                val = str(kpi_df.iloc[0][col])
                ax1.text(0.03, y, f"{col}: {val}", fontsize=10, va="top")
                y -= 0.04
            pdf.savefig(fig1, bbox_inches="tight")

            fig2 = Figure(figsize=(11.69, 8.27), dpi=120, facecolor="white")
            ax2 = fig2.add_subplot(111)
            ax2.axis("off")
            ax2.text(0.01, 0.98, "Dashboard - Resumen por sucursal", fontsize=14, fontweight="bold", va="top")
            if summary_df.empty:
                ax2.text(0.01, 0.90, "No hay datos visibles para exportar con los filtros/rango actuales.", fontsize=10, va="top")
            else:
                table = ax2.table(
                    cellText=summary_df.values.tolist(),
                    colLabels=summary_df.columns.tolist(),
                    loc="upper left",
                    cellLoc="left",
                    colLoc="left",
                    bbox=[0.01, 0.05, 0.98, 0.88],
                )
                table.auto_set_font_size(False)
                table.set_fontsize(9)
            pdf.savefig(fig2, bbox_inches="tight")

    def draw_chart(self, total_df):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(5.4, 4.2), dpi=100, facecolor=CURRENT_THEME["panel"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(CURRENT_THEME["panel"])

        if not total_df.empty and "SUCURSAL" in total_df.columns:
            counts_all = total_df["SUCURSAL"].fillna("SIN SUCURSAL").value_counts()
            counts = counts_all.head(5)
            if len(counts_all) > 5:
                counts.loc["OTROS"] = counts_all.iloc[5:].sum()
            colors = [CURRENT_THEME["gold"], CURRENT_THEME["forest"], CURRENT_THEME["emerald"], CURRENT_THEME["sky"], CURRENT_THEME["warning"], CURRENT_THEME["danger"]]
            ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90, colors=colors[: len(counts)], textprops={"color": CURRENT_THEME["text"], "fontsize": 10})
            ax.set_title("Distribución por Sucursal (Top 5 + Otros)", color=CURRENT_THEME["gold"], fontsize=14)
        else:
            ax.text(0.5, 0.5, "No hay datos aún", color=CURRENT_THEME["text"], ha="center", va="center")
            ax.axis("off")

        fig.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

        if self.bar_chart_canvas:
            self.bar_chart_canvas.get_tk_widget().destroy()

        fig2 = Figure(figsize=(5.4, 4.2), dpi=100, facecolor=CURRENT_THEME["panel"])
        ax2 = fig2.add_subplot(111)
        ax2.set_facecolor(CURRENT_THEME["panel"])

        if not total_df.empty and "MODELO BASE" in total_df.columns:
            counts_mods = total_df["MODELO BASE"].fillna("SIN MODELO").value_counts()
            top_mods = counts_mods.head(10)

            x = range(len(top_mods))
            colors = [CURRENT_THEME["sky"], CURRENT_THEME["gold"], CURRENT_THEME["emerald"], CURRENT_THEME["warning"], CURRENT_THEME["danger"], CURRENT_THEME["forest"]]
            colors_cycle = [colors[i % len(colors)] for i in range(len(top_mods))]

            bars = ax2.bar(x, top_mods.values, color=colors_cycle)
            ax2.set_xticks(x)

            # Truncate long model names
            labels = [str(label)[:12] + '...' if len(str(label)) > 15 else str(label) for label in top_mods.index]
            ax2.set_xticklabels(labels, rotation=45, ha='right', color=CURRENT_THEME["text"], fontsize=8)
            ax2.tick_params(axis='y', colors=CURRENT_THEME["text"])

            # Spines
            for spine in ax2.spines.values():
                spine.set_color(CURRENT_THEME["gold"])
                spine.set_linewidth(0.5)

            # Labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax2.annotate(f'{height}',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 3),
                             textcoords="offset points",
                             ha='center', va='bottom', color=CURRENT_THEME["text"], fontsize=8)

            ax2.set_title("Top 10 Modelos por Cantidad", color=CURRENT_THEME["gold"], fontsize=12)
        else:
            ax2.text(0.5, 0.5, "No hay datos aún", color=CURRENT_THEME["text"], ha="center", va="center")
            ax2.axis("off")

        fig2.tight_layout()
        self.bar_chart_canvas = FigureCanvasTkAgg(fig2, master=self.bar_chart_container)
        self.bar_chart_canvas.draw()
        self.bar_chart_canvas.get_tk_widget().pack(fill="both", expand=True)
